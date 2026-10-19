"""Cut the demo part of the edited video into one video per demo step.

Usage: python split.py
Reads plan.json, out/narration-timing.csv, out/copilot-app-demo.srt, and the rendered segments/.
Writes out/parts/<NN-name>/ with: <name>.mp4 (soft English captions, off by default),
<name>.srt, <name>.vtt, narration-script.md, narration-timing.csv
"""
import csv, json, re, subprocess, sys
from pathlib import Path

V = Path(__file__).resolve().parent
P = json.loads((V / 'plan.json').read_text())
FPS, FADE = P['fps'], 0.4
SEG, OUT = V / 'segments', V / 'out' / 'parts'
ENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS)]

PARTS = [
    ('01-get-the-data', 'Get the public data', ['d01', 'd02', 'd03']),
    ('02-start-agents-and-review-the-plan', 'Start agents and review the plan', ['d04', 'd05', 'd06']),
    ('03-website', 'Website: tested, deployed, and previewed', ['d07', 'd08', 'd09']),
    ('04-excel-workbook', 'Excel workbook', ['d10', 'd11']),
    ('05-workiq-brief', 'WorkIQ brief from Microsoft 365', ['d12', 'd13']),
    ('06-executive-briefing', 'Executive briefing', ['d14']),
    ('07-weekly-automation', 'Weekly automation', ['d15']),
]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'FAILED: {r.stderr[-1200:]}')


def dur(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                                capture_output=True, text=True).stdout)


def ts(x):
    h, m, r = x.split(':'); s, ms = r.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def fmt(t, sep=','):
    t = max(t, 0)
    h, r = divmod(t, 3600); m, r = divmod(r, 60)
    return f'{int(h):02d}:{int(m):02d}:{int(r):02d}{sep}{int(round((r % 1) * 1000)) % 1000:03d}'


timing = {r['scene']: r for r in csv.DictReader(open(V / 'out/narration-timing.csv'))}
scenes = {s['id']: s for s in P['scenes']}
cues = re.findall(r'(\d\d:\d\d:\d\d,\d{3}) --> (\d\d:\d\d:\d\d,\d{3})\n(.+?)(?:\n\n|\Z)',
                  (V / 'out/copilot-app-demo.srt').read_text(), re.S)

for slug, title, ids in PARTS:
    d = OUT / slug
    d.mkdir(parents=True, exist_ok=True)
    segs = [SEG / f'{i}.mp4' for i in ids]
    lens = [dur(s) for s in segs]
    total = sum(lens) - FADE * (len(segs) - 1)
    inputs, chain, prev, off = [], '', '[0:v]', 0.0
    for s in segs:
        inputs += ['-i', s]
    for k in range(1, len(segs)):
        off += lens[k - 1] - FADE
        chain += f'{prev}[{k}:v]xfade=transition=fade:duration={FADE}:offset={off:.3f}[a{k}];'
        prev = f'[a{k}]'
    chain += f'{prev}fade=t=in:st=0:d=0.5,fade=t=out:st={total - 0.8:.2f}:d=0.8,setsar=1,format=yuv420p[v]'
    silent = d / 'video-nocc.mp4'
    run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', chain, '-map', '[v]', *ENC, '-movflags', '+faststart', silent])

    # Captions: cues of these scenes, shifted to the part's timeline.
    t0 = float(timing[ids[0]]['start'])
    t1 = float(timing[ids[-1]]['end'])
    srt, vtt, n = [], ['WEBVTT', ''], 1
    for a, b, text in cues:
        a, b = ts(a), ts(b)
        if a >= t0 - 0.01 and a < t1:
            a, b = a - t0, min(b - t0, total - 0.05)
            srt += [str(n), f'{fmt(a)} --> {fmt(b)}', text.strip(), '']
            vtt += [f'{fmt(a, ".")} --> {fmt(b, ".")}', text.strip(), '']
            n += 1
    (d / f'{slug}.srt').write_text('\n'.join(srt))
    (d / f'{slug}.vtt').write_text('\n'.join(vtt))

    # Narration script and timing for this part.
    md = [f'# Narration: {title}', '',
          'Read each block during its time window. Name each audio file with its scene ID (for example, `d01.mp3`), '
          'then run `python add-narration.py <audio-folder> --video video-nocc.mp4 --timing narration-timing.csv` in this folder.', '']
    rows = ['scene,start,end,duration_s,words,max_words_at_150wpm']
    for i, (sid, ln) in enumerate(zip(ids, lens)):
        st = float(timing[sid]['start']) - t0
        win = ln if i == len(ids) - 1 else ln - FADE
        words = len(re.findall(r"[\w'’-]+", scenes[sid]['text']))
        md += [f"## {sid} · {fmt(st, '.')[3:-4]} to {fmt(st + win, '.')[3:-4]} · {win:.1f} s", '',
               f"*On screen: {scenes[sid].get('label', '')}*", '', scenes[sid]['text'], '']
        rows.append(f'{sid},{st:.2f},{st + win:.2f},{win:.2f},{words},{int(win * 2.5)}')
    (d / 'narration-script.md').write_text('\n'.join(md))
    (d / 'narration-timing.csv').write_text('\n'.join(rows) + '\n')

    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', silent, '-i', d / f'{slug}.srt', '-map', '0:v', '-map', '1:s',
         '-c:v', 'copy', '-c:s', 'mov_text', '-metadata:s:s:0', 'language=eng', '-metadata:s:s:0', 'title=English',
         '-disposition:s:0', '-default', '-metadata', f'title={title}', '-movflags', '+faststart', d / f'{slug}.mp4'])
    print(f'{slug:42} {total:6.1f}s  {n - 1:3d} cues')
