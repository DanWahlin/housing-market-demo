import * as d3 from 'd3';
import { feature } from 'topojson-client';
import type { Topology, GeometryCollection } from 'topojson-specification';
import { pct } from './math.ts';
import { yoyColor, trendChart, hmdaChart, metroChart, legend, PURPOSES, reducedMotion } from './charts.ts';

type State = { code: string; name: string; fips: string; yoy: (number | null)[]; sa: (number | null)[] };
type Summary = { period: string; usPeriod: string; usYoy: number; usSince2019Q4: number; fastest: { name: string; value: number }; slowest: { name: string; value: number } };
type Metros = { period: string; count: number; top: { name: string; yoy: number }[] };
type Hmda = { years: number[]; byState: Record<string, Record<string, Record<string, { loans: number; volume: number }>>> };

const $ = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;
const get = <T>(f: string): Promise<T> => fetch(`data/${f}`).then((r) => r.json());

const [summary, { quarters, states }, metros, hmda, topo] = await Promise.all([
  get<Summary>('summary.json'), get<{ quarters: string[]; states: State[] }>('states.json'),
  get<Metros>('metros.json'), get<Hmda>('hmda.json'), get<Topology>('us-states.json'),
]);
const SRC_HPI = `Source: FHFA House Price Index, purchase-only. Latest period: ${summary.period}.`;

// ---------- Hero ----------
$('hero-period').textContent = `Latest quarter: ${summary.period}`;
$('hero-source').textContent = `${SRC_HPI} U.S. quarter = average of monthly national index values. Year-over-year uses the not seasonally adjusted index.`;
const cards = [
  { label: 'U.S. home prices, year over year', v: summary.usYoy, sub: `${summary.usPeriod} vs. one year earlier` },
  { label: 'U.S. home prices since 2019 Q4', v: summary.usSince2019Q4, sub: `${summary.usPeriod} vs. 2019 Q4` },
  { label: 'Fastest state, year over year', v: summary.fastest.value, sub: summary.fastest.name },
  { label: 'Slowest state, year over year', v: summary.slowest.value, sub: summary.slowest.name },
];
d3.select('#stats').selectAll('li').data(cards).join('li').attr('class', 'stat').style('animation-delay', (_, i) => `${i * 120}ms`)
  .html((d) => `<span class="label">${d.label}</span><span class="value ${d.v >= 0 ? 'up' : 'down'}">${pct(d.v)}</span><span class="sub">${d.sub}</span>`)
  .select<HTMLElement>('.value').transition().duration(reducedMotion() ? 0 : 1400).ease(d3.easeCubicOut)
  .tween('text', function (d) { const i = d3.interpolateNumber(0, d.v); return (t) => { this.textContent = pct(i(t)); }; });

// ---------- Map ----------
const byFips = new Map(states.map((s) => [s.fips, s]));
const geo = feature(topo, topo.objects.states as GeometryCollection);
const path = d3.geoPath();
let qi = quarters.length - 1;
let selected: State | null = null;
let lastFocus: SVGPathElement | null = null;
const tip = $('tooltip');
const mapWrap = document.querySelector('.map-wrap') as HTMLElement;

legend($('legend'));
$('map-source').textContent = `${SRC_HPI} Year-over-year change = index ÷ same quarter one year earlier − 1 (not seasonally adjusted).`;

const statePaths = d3.select('#map').append('g').selectAll<SVGPathElement, (typeof geo.features)[number]>('path')
  .data(geo.features.filter((f) => byFips.has(String(f.id)))).join('path')
  .attr('class', 'state').attr('d', path).attr('tabindex', 0).attr('role', 'button')
  .on('pointermove', (e: PointerEvent, f) => showTip(byFips.get(String(f.id))!, d3.pointer(e, mapWrap)))
  .on('pointerleave blur', hideTip)
  .on('focus', function (_, f) {
    const b = this.getBoundingClientRect(), w = mapWrap.getBoundingClientRect();
    showTip(byFips.get(String(f.id))!, [b.x + b.width / 2 - w.x, b.y + b.height / 3 - w.y]);
  })
  .on('click', function (_, f) { openPanel(byFips.get(String(f.id))!, this); })
  .on('keydown', function (e: KeyboardEvent, f) {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openPanel(byFips.get(String(f.id))!, this); }
  });

function showTip(s: State, [x, y]: [number, number]) {
  const v = s.yoy[qi];
  tip.innerHTML = `<strong>${s.name}</strong><span class="big ${v != null && v < 0 ? 'down' : 'up'}">${pct(v)}</span> year over year, ${quarters[qi]}<br/>Price index (SA): ${s.sa[qi]?.toFixed(1) ?? 'n/a'}`;
  tip.hidden = false;
  const w = mapWrap.clientWidth;
  tip.style.left = `${Math.min(Math.max(x, 100), w - 100)}px`;
  tip.style.top = `${Math.max(y, 90)}px`;
}
function hideTip() { tip.hidden = true; }

function paint(animate: boolean) {
  statePaths.each(function (f) {
    const s = byFips.get(String(f.id))!;
    const v = s.yoy[qi];
    this.setAttribute('aria-label', `${s.name}: ${pct(v)} year over year, ${quarters[qi]}`);
  });
  (animate && !reducedMotion() ? statePaths.transition().duration(220) : statePaths)
    .attr('fill', (f) => { const v = byFips.get(String(f.id))!.yoy[qi]; return v == null ? '#444c56' : yoyColor(v); });
  $('map-quarter').textContent = quarters[qi];
  slider.value = String(qi);
  slider.setAttribute('aria-valuetext', quarters[qi]);
  if (selected) $('panel-stats').innerHTML = statsLine(selected);
}

// ---------- Player ----------
const slider = $<HTMLInputElement>('slider');
const play = $<HTMLButtonElement>('play');
slider.max = String(quarters.length - 1);
let timer: number | undefined;
const setPlaying = (on: boolean) => {
  play.setAttribute('aria-label', on ? 'Pause animation' : 'Play animation through every quarter');
  play.setAttribute('aria-pressed', String(on));
  $('play-icon').setAttribute('d', on ? 'M6 5h4v14H6zm8 0h4v14h-4z' : 'M8 5v14l11-7z');
  $('map-quarter').setAttribute('aria-live', on ? 'off' : 'polite');
};
function stop() { clearInterval(timer); timer = undefined; setPlaying(false); }
play.addEventListener('click', () => {
  if (timer) return stop();
  if (qi >= quarters.length - 1) qi = 0;
  setPlaying(true);
  paint(true);
  timer = window.setInterval(() => {
    qi += 1;
    paint(true);
    if (qi >= quarters.length - 1) stop();
  }, 260);
});
slider.addEventListener('input', () => { stop(); qi = +slider.value; paint(true); });
paint(false);

// ---------- State panel ----------
const panel = $('panel');
function statsLine(s: State) {
  return `<b>${pct(s.yoy[qi])}</b> year over year in ${quarters[qi]} · latest (${summary.period}): <b>${pct(s.yoy.at(-1)!)}</b>`;
}
function openPanel(s: State, el: SVGPathElement) {
  selected = s;
  lastFocus = el;
  statePaths.classed('selected', (f) => String(f.id) === s.fips);
  $('panel-title').textContent = s.name;
  $('panel-stats').innerHTML = statsLine(s);
  $('trend-source').textContent = `Source: FHFA House Price Index, purchase-only, seasonally adjusted, ${quarters[0]} to ${summary.period}.`;
  $('hmda-legend').innerHTML = PURPOSES.map((p) => `<span style="--c:${p.color}">${p.key}</span>`).join('');
  panel.hidden = false;
  requestAnimationFrame(() => {
    panel.classList.add('open');
    trendChart($('trend'), quarters, s.sa, s.name);
    hmdaChart($('hmda'), hmda.years, hmda.byState[s.code], s.name);
    $('panel-close').focus();
  });
}
function closePanel() {
  if (panel.hidden) return;
  panel.classList.remove('open');
  selected = null;
  statePaths.classed('selected', false);
  setTimeout(() => { panel.hidden = true; }, reducedMotion() ? 0 : 350);
  lastFocus?.focus();
}
$('panel-close').addEventListener('click', closePanel);
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { closePanel(); hideTip(); } });

// ---------- Metros ----------
$('metros-hint').textContent = `Ranked by year-over-year change in ${metros.period}, among the ${metros.count} largest metros in the FHFA data.`;
$('metros-source').textContent = `Source: FHFA House Price Index, purchase-only, not seasonally adjusted. Latest period: ${metros.period}.`;
let metrosDrawn = false;
const drawMetros = () => { metroChart($('metros'), metros.top, metros.period); metrosDrawn = true; };

// ---------- Reveal on scroll, resize ----------
const io = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    e.target.classList.add('in');
    if (e.target.id === 'metros-section' && !metrosDrawn) drawMetros();
    io.unobserve(e.target);
  }
}, { threshold: 0.15 });
document.querySelectorAll('.reveal').forEach((el) => io.observe(el));

let lastW = window.innerWidth;
window.addEventListener('resize', () => {
  if (window.innerWidth === lastW) return;
  lastW = window.innerWidth;
  if (metrosDrawn) drawMetros();
  if (selected) { trendChart($('trend'), quarters, selected.sa, selected.name); hmdaChart($('hmda'), hmda.years, hmda.byState[selected.code], selected.name); }
});
