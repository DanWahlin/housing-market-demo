"""Add per-scene narration files (s01.mp3, d05.wav, ...) to the edited video.

Usage: python add-narration.py <audio-folder> [--offset 0.35] [--video video-nocc.mp4] [--timing narration-timing.csv]
Defaults to the full video in out/. With --video and --timing, it works on one demo part.
Writes <video name without -nocc>-narrated.mp4 next to the video (video + AAC narration + soft English captions).
"""
import csv, subprocess, sys
from pathlib import Path

V = Path(__file__).resolve().parent
folder = Path(sys.argv[1])
lead = float(sys.argv[sys.argv.index('--offset') + 1]) if '--offset' in sys.argv else 0.35
arg = lambda k, d: Path(sys.argv[sys.argv.index(k) + 1]).resolve() if k in sys.argv else d
video = arg('--video', V / 'out/video-nocc.mp4')
timing = arg('--timing', V / 'out/narration-timing.csv')
srt = next(video.parent.glob('*.srt'))
rows = list(csv.DictReader(open(timing)))
inputs, parts, n = [], [], 0
for r in rows:
    f = next((p for p in folder.glob(f"{r['scene']}.*") if p.suffix.lower() in ('.mp3', '.wav', '.m4a')), None)
    if not f:
        print(f"missing audio for {r['scene']}"); continue
    d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f],
                             capture_output=True, text=True).stdout)
    if d + lead > float(r['duration_s']):
        print(f"WARNING {r['scene']}: audio {d:.1f}s is longer than its {float(r['duration_s']) - lead:.1f}s window")
    ms = int((float(r['start']) + lead) * 1000)
    inputs += ['-i', f]
    n += 1
    parts.append(f'[{n}:a]aresample=48000,adelay={ms}|{ms}[a{n}]')
fc = ';'.join(parts) + ';' + ''.join(f'[a{i}]' for i in range(1, n + 1)) + f'amix=inputs={n}:normalize=0,loudnorm=I=-16:TP=-1.5[aout]'
out = video.parent / f'{srt.stem}-narrated.mp4'
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', video, *inputs, '-i', srt,
                '-filter_complex', fc, '-map', '0:v', '-map', '[aout]', '-map', f'{n + 1}:s', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
                '-c:s', 'mov_text', '-metadata:s:s:0', 'language=eng', '-disposition:s:0', '-default', '-shortest', '-movflags', '+faststart', out],
               check=True)
print('wrote', out)
