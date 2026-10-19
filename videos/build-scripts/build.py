"""Build the edited demo video, captions, and narration script from plan.json.

Usage: python build.py            # build everything
       python build.py --only d05 # rebuild one segment, then reassemble
Outputs (in out/):
  copilot-app-demo.mp4      1920x1080 30 fps H.264, soft SRT caption track, no audio
  copilot-app-demo.srt/.vtt captions timed to the edit
  narration-script.md       per-scene script with timecodes for ElevenLabs
  narration-elevenlabs.txt  one plain-text block per scene, ready to paste
  narration-timing.csv      scene start, duration, and word budget
"""
import json, math, re, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

V = Path(__file__).resolve().parent
P = json.loads((V / 'plan.json').read_text())
FPS, WPS = P['fps'], P['wps']
FADE = 0.4
SRC = {'demo': V / 'raw/demo-154738.mp4', 'excel': V / 'raw/excel-retake.mp4'}
STILLS, SEG, OUT = V / 'stills', V / 'segments', V / 'out'
SEG.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
ENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS)]
BOLD = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'FAILED: {" ".join(map(str, cmd))[:300]}\n{r.stderr[-1500:]}')


def words(t):
    return len(re.findall(r"[\w'’-]+", t))


def narr_len(s):
    return words(s['text']) / WPS + s.get('pad', 0.8)


def label_png(text, path):
    font = ImageFont.truetype(BOLD, 42)
    w = int(font.getlength(text)) + 64
    img = Image.new('RGBA', (w + 14, 86), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((6, 6, w + 6, 80), radius=16, fill=(13, 17, 23, 225))
    d.rounded_rectangle((6, 6, 18, 80), radius=4, fill=(46, 160, 67, 255))
    d.text((40, 20), text, font=font, fill=(255, 255, 255, 255))
    img.save(path)


def still(s, dur, path):
    # Static slide. A slow zoom (zoompan) moves in whole-pixel steps, which makes text shake.
    n = int(round(dur * FPS))
    run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-framerate', str(FPS), '-i', STILLS / s['src'],
         '-vf', 'scale=1920:1080:flags=lanczos,setsar=1', '-frames:v', str(n), *ENC, path])


def build(s, dur, path):
    imgs = s['srcs']
    first = dur * 0.22
    step = (dur - first) / (len(imgs) - 1)
    durs = [first] + [step] * (len(imgs) - 1)
    durs[-1] += 0.0
    inputs, chain, off = [], '', 0.0
    xf = 0.25
    for i, (img, d) in enumerate(zip(imgs, durs)):
        inputs += ['-loop', '1', '-t', f'{d + xf:.3f}', '-i', STILLS / img]
    prev = '[0:v]'
    for i in range(1, len(imgs)):
        off += durs[i - 1]
        chain += f'{prev}[{i}:v]xfade=transition=fade:duration={xf}:offset={off - xf:.3f}[x{i}];'
        prev = f'[x{i}]'
    chain += f'{prev}scale=1920:1080,format=yuv420p[v]'
    run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', chain, '-map', '[v]', '-t', f'{dur:.3f}', *ENC, path])


def scroll(s, dur, path):
    img = STILLS / s['src']
    h = Image.open(img).height
    travel = h - 1080
    hold = 1.2
    expr = f"if(lt(t,{hold}),0,if(gt(t,{dur - hold}),{travel},{travel}*(t-{hold})/{dur - 2 * hold}))"
    lab = SEG / f"{s['id']}-label.png"
    label_png(s['label'], lab)
    fc = (f"[0:v]crop=1920:1080:0:'{expr}',fps={FPS}[b];[1:v]format=rgba,fade=t=in:st=0.3:d=0.35:alpha=1,"
          f"fade=t=out:st={max(dur - 0.9, 1):.2f}:d=0.35:alpha=1[l];[b][l]overlay=x=56:y=H-h-56,format=yuv420p[v]")
    run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-framerate', str(FPS), '-t', f'{dur:.3f}', '-i', img,
         '-loop', '1', '-t', f'{dur:.3f}', '-i', lab, '-filter_complex', fc, '-map', '[v]', '-t', f'{dur:.3f}', *ENC, path])


def clip(s, dur, path):
    span = s['out'] - s['in']
    speed = span / dur
    hold = 0.0
    if speed < 1.0:
        speed, hold = 1.0, dur - span
    f = []
    if s.get('brighten'):
        k = s['brighten']
        f.append(f"lutrgb=r='clip(val*{k},0,255)':g='clip(val*{k},0,255)':b='clip(val*{k},0,255)'")
    if s.get('zoom'):
        x, y, w = s['zoom']
        cw, ch = int(1920 * w), int(1080 * w)
        f.append(f'crop={cw}:{ch}:{int(1920 * x)}:{int(1080 * y)},scale=1920:1080:flags=lanczos')
    f.append(f'setpts=(PTS-STARTPTS)/{speed:.4f},fps={FPS}')
    patch = None
    if s.get('patch'):
        pt = s['patch']
        patch = SEG / f"{s['id']}-patch.png"
        img = Image.new('RGB', (pt['w'], pt['h']), tuple(pt['bg']))
        ImageDraw.Draw(img).text((pt['tx'], pt['ty']), pt['text'], font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', pt['size']), fill=tuple(pt['fg']))
        img.save(patch)
    if hold > 0:
        f.append(f'tpad=stop_mode=clone:stop_duration={hold:.3f}')
    vf = ','.join(f)
    lab = SEG / f"{s['id']}-label.png"
    label_png(s['label'], lab)
    pre = f"[0:v][2:v]overlay=x={s['patch']['x']}:y={s['patch']['y']}[p];[p]" if patch else "[0:v]"
    fc = (f"{pre}{vf}[b];[1:v]format=rgba,fade=t=in:st=0.3:d=0.35:alpha=1,fade=t=out:st={max(dur - 0.9, 1):.2f}:d=0.35:alpha=1[l];"
          f"[b][l]overlay=x=56:y=H-h-56:shortest=0,format=yuv420p[v]")
    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(s['in']), '-t', f'{span + 0.5:.3f}', '-i', SRC[s['src']],
         '-loop', '1', '-t', f'{dur:.3f}', '-i', lab, *(['-loop', '1', '-i', patch] if patch else []),
         '-filter_complex', fc, '-map', '[v]', '-t', f'{dur:.3f}', *ENC, path])
    return speed, hold


def fmt(t, sep=','):
    h, r = divmod(t, 3600); m, r = divmod(r, 60)
    return f'{int(h):02d}:{int(m):02d}:{int(r):02d}{sep}{int(round((r % 1) * 1000)) % 1000:03d}'


def chunks(text, limit=72):
    out = []
    for sent in re.split(r'(?<=[.!?:])\s+', text.strip()):
        cur = ''
        for w in sent.split():
            if len(cur) + len(w) + 1 > limit and cur:
                out.append(cur); cur = w
            else:
                cur = f'{cur} {w}'.strip()
        if cur:
            out.append(cur)
    return out


def wrap2(c, width=44):
    if len(c) <= width:
        return c
    mid = len(c) // 2
    cut = min((i for i, ch in enumerate(c) if ch == ' '), key=lambda i: abs(i - mid))
    return c[:cut] + '\n' + c[cut + 1:]


only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
rows, t = [], 0.0
for i, s in enumerate(P['scenes']):
    n = narr_len(s)
    if s['kind'] == 'clip':
        native = (s['out'] - s['in']) / s.get('speed', 1)
        dur = max(n, min(native, n + 3.0))
    else:
        dur = max(n, s.get('min', 3.0))
    dur = round(dur + (FADE if i < len(P['scenes']) - 1 else 0), 2)
    path = SEG / f"{s['id']}.mp4"
    info = ''
    if only in (None, s['id']) or not path.exists():
        if s['kind'] == 'still':
            still(s, dur, path)
        elif s['kind'] == 'build':
            build(s, dur, path)
        elif s['kind'] == 'scroll':
            scroll(s, dur, path)
        else:
            sp, hold = clip(s, dur, path)
            info = f'speed {sp:.1f}x' + (f', hold {hold:.1f}s' if hold else '')
        print(f"{s['id']:4} {dur:6.2f}s {info}")
    rows.append((s, t, dur))
    t += dur - FADE

total = t + FADE
# Assemble with crossfades.
inputs, chain, prev, off = [], '', '[0:v]', 0.0
for i, (s, start, dur) in enumerate(rows):
    inputs += ['-i', SEG / f"{s['id']}.mp4"]
for i in range(1, len(rows)):
    off += rows[i - 1][2] - FADE
    chain += f'{prev}[{i}:v]xfade=transition=fade:duration={FADE}:offset={off:.3f}[a{i}];'
    prev = f'[a{i}]'
chain += f'{prev}fade=t=in:st=0:d=0.6,fade=t=out:st={total - 1.0:.2f}:d=1.0,setsar=1,format=yuv420p[v]'
silent = OUT / 'video-nocc.mp4'
run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', chain, '-map', '[v]', *ENC, '-movflags', '+faststart', silent])

# Captions and narration script.
srt, vtt, md, plain, csv = [], ['WEBVTT', ''], [], [], ['scene,start,end,duration_s,words,max_words_at_150wpm']
md += ['# Narration script: GitHub Copilot app demo', '',
       'Read each block during its time window. The windows match the video exactly. The timing assumes about 150 words a minute.',
       'Generate one audio file per scene and name it with the scene ID (for example, `s01.mp3`). '
       'Then run `python add-narration.py <folder>`. It places each file at the start of its scene. '
       'If a file is longer than its window, the script reports it, so you can shorten that text or slow the clip.', '']
k = 1
for s, start, dur in rows:
    seg_len = dur - FADE if s is not rows[-1][0] else dur
    lead = 0.35
    speak = words(s['text']) / WPS
    parts = chunks(s['text'])
    wc = [words(p) for p in parts]
    tt = start + lead
    for p, w in zip(parts, wc):
        d = speak * w / max(sum(wc), 1)
        a, b = tt, min(tt + d, start + seg_len - 0.05)
        srt += [str(k), f'{fmt(a)} --> {fmt(b)}', wrap2(p), '']
        vtt += [f'{fmt(a, ".")} --> {fmt(b, ".")}', wrap2(p), '']
        k += 1; tt += d
    vis = s.get('label') or {'still': 'Slide ' + s.get('src', '').replace('slide-', '').replace('.png', ''), 'build': 'Slide build', 'scroll': ''}[s['kind']]
    md += [f"## {s['id']} · {fmt(start, '.')[3:-4]} to {fmt(start + seg_len, '.')[3:-4]} · {seg_len:.1f} s", '',
           f'*On screen: {vis}*', '', s['text'], '']
    plain += [s['text'], '<break time="1.0s" />']
    csv.append(f"{s['id']},{start:.2f},{start + seg_len:.2f},{seg_len:.2f},{words(s['text'])},{int(seg_len * 2.5)}")

(OUT / 'copilot-app-demo.srt').write_text('\n'.join(srt))
(OUT / 'copilot-app-demo.vtt').write_text('\n'.join(vtt))
(OUT / 'narration-script.md').write_text('\n'.join(md))
(OUT / 'narration-elevenlabs.txt').write_text('\n'.join(plain[:-1]) + '\n')
(OUT / 'narration-timing.csv').write_text('\n'.join(csv) + '\n')

final = OUT / 'copilot-app-demo.mp4'
run(['ffmpeg', '-y', '-loglevel', 'error', '-i', silent, '-i', OUT / 'copilot-app-demo.srt', '-map', '0:v', '-map', '1:s',
     '-c:v', 'copy', '-c:s', 'mov_text', '-metadata:s:s:0', 'language=eng', '-metadata:s:s:0', 'title=English',
     '-disposition:s:0', '-default', '-movflags', '+faststart', final])
print(f'total {total:.1f}s ({total / 60:.1f} min) -> {final}')
