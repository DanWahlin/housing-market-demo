"""Render talk-deck slides (and progressive build variants) to 1920x1080 PNGs.

Usage: python slides.py <deck.pptx> <out-dir>
"""
import copy, subprocess, sys, tempfile
from pathlib import Path
from pptx import Presentation
from pptx.util import Pt

deck, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)


def render(pptx_path, prefix):
    with tempfile.TemporaryDirectory() as t:
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', t, str(pptx_path)],
                       check=True, capture_output=True)
        pdf = next(Path(t).glob('*.pdf'))
        subprocess.run(['pdftoppm', '-png', '-scale-to-x', '1920', '-scale-to-y', '1080', str(pdf), str(out / prefix)], check=True)


# 1. Every slide, final state.
# render(deck, "slide")


def text_of(sh):
    return sh.text_frame.text.strip() if sh.has_text_frame else ''


def rect(s):
    return (s.left, s.top, s.left + s.width, s.top + s.height)


def inside(a, b, tol=Pt(2)):
    return a[0] >= b[0] - tol and a[1] >= b[1] - tol and a[2] <= b[2] + tol and a[3] <= b[3] + tol


def group(slide, label, maxw=Pt(220)):
    t = next(sh for sh in slide.shapes if text_of(sh) == label)
    boxes = [sh for sh in slide.shapes if sh is not t and sh.width < maxw and not text_of(sh) and inside(rect(t), rect(sh))]
    box = min(boxes, key=lambda s: s.width * s.height)
    return [sh for sh in slide.shapes if inside(rect(sh), rect(box))]


def variants(title, steps, prefix):
    """steps: list of lists of shape-getters; variant k shows steps[:k]."""
    for k in range(len(steps) + 1):
        prs = Presentation(deck)
        idx = next(i for i, s in enumerate(prs.slides) if any(text_of(sh) == title for sh in s.shapes))
        s = prs.slides[idx]
        hide = [sh for step in steps[k:] for sh in step(s)]
        for sh in hide:
            sh._element.getparent().remove(sh._element)
        # keep only this slide
        ids = prs.slides._sldIdLst
        for i, sid in reversed(list(enumerate(list(ids)))):
            if i != idx:
                prs.part.drop_rel(sid.rId)
                ids.remove(sid)
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / f'{prefix}-{k}.pptx'
            prs.save(p)
            render(p, f'{prefix}-{k}')


orch = ['You', 'Housing website', 'Excel workbook', 'PowerPoint briefing', 'WorkIQ session brief', 'Weekly automation']
# variants('Each session plays its own part', [(lambda s, n=n: group(s, n)) for n in orch], 'orch')

eq_steps = [
    lambda s: group(s, 'Your ideas'),
    lambda s: [sh for sh in s.shapes if text_of(sh) == '×'] + group(s, 'Agents that do \x0bthe work'),
    lambda s: [sh for sh in s.shapes if text_of(sh) == '=' or text_of(sh).startswith('You bring')] + group(s, 'Impact'),
]
variants('Ideas need execution', eq_steps, 'eq')
print('done')
