import * as d3 from 'd3';
import { pct } from './math.ts';

export const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const dur = (ms: number) => (reducedMotion() ? 0 : ms);

const css = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

/** Color-blind-safe diverging scale: orange (falling) to blue (rising). Colors come from the active theme. */
function makeScale() {
  const neg = d3.interpolateLab(css('--map-neg'), css('--map-mid'));
  const pos = d3.interpolateLab(css('--map-mid'), css('--map-pos'));
  return d3.scaleDivergingSqrt<string>((t) => (t < 0.5 ? neg(t * 2) : pos((t - 0.5) * 2))).domain([-0.1, 0, 0.1]).clamp(true);
}
const makePurposes = () => [
  { key: 'Home purchase', color: css('--c1') },
  { key: 'Refinance', color: css('--c2') },
  { key: 'Cash-out refinance', color: css('--c3') },
];
export let yoyColor = makeScale();
export let PURPOSES = makePurposes();
export const naColor = () => css('--map-na');

/** Rebuild theme-based colors after the theme changes. */
export function refreshPalette() {
  yoyColor = makeScale();
  PURPOSES = makePurposes();
}

function svgFor(el: HTMLElement, height: number, label: string) {
  const width = Math.max(280, el.clientWidth);
  d3.select(el).selectAll('*').remove();
  const svg = d3.select(el).append('svg').attr('viewBox', `0 0 ${width} ${height}`).attr('role', 'img').attr('aria-label', label);
  return { svg, width };
}

/** Line chart of the seasonally adjusted HPI. */
export function trendChart(el: HTMLElement, quarters: string[], values: (number | null)[], stateName: string) {
  const pts = quarters.map((q, i) => ({ x: +q.slice(0, 4) + (+q.slice(-1) - 1) / 4, y: values[i] })).filter((d): d is { x: number; y: number } => d.y != null);
  const last = pts.at(-1)!;
  const h = 260, m = { t: 12, r: 16, b: 44, l: 56 };
  const { svg, width } = svgFor(el, h, `${stateName} home price index from ${quarters[0]} to ${quarters.at(-1)}. Latest value ${last.y.toFixed(0)}.`);
  const x = d3.scaleLinear().domain(d3.extent(pts, (d) => d.x) as [number, number]).range([m.l, width - m.r]);
  const y = d3.scaleLinear().domain([0, d3.max(pts, (d) => d.y)! * 1.05]).nice().range([h - m.b, m.t]);
  svg.append('g').attr('class', 'grid').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickSize(-(width - m.l - m.r)).tickFormat(() => '')).call((g) => g.select('.domain').remove());
  svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${h - m.b})`).call(d3.axisBottom(x).ticks(width < 400 ? 4 : 7).tickFormat(d3.format('d')));
  svg.append('g').attr('class', 'axis').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5));
  svg.append('text').attr('class', 'axis-label').attr('x', (m.l + width - m.r) / 2).attr('y', h - 6).attr('text-anchor', 'middle').text('Year');
  svg.append('text').attr('class', 'axis-label').attr('transform', `translate(14,${(h - m.b + m.t) / 2}) rotate(-90)`).attr('text-anchor', 'middle').text('Index (1991 Q1 = 100)');
  const path = svg.append('path').datum(pts).attr('fill', 'none').style('stroke', 'var(--accent)').attr('stroke-width', 2.5)
    .attr('d', d3.line<{ x: number; y: number }>().x((d) => x(d.x)).y((d) => y(d.y)));
  const len = (path.node() as SVGPathElement).getTotalLength();
  path.attr('stroke-dasharray', `${len} ${len}`).attr('stroke-dashoffset', len).transition().duration(dur(900)).ease(d3.easeCubicOut).attr('stroke-dashoffset', 0);
  svg.append('circle').attr('cx', x(last.x)).attr('cy', y(last.y)).attr('r', 5).style('fill', 'var(--accent)');
}

type HmdaYear = Record<string, { loans: number; volume: number }>;

/** Grouped bars: loans originated per year by loan purpose. */
export function hmdaChart(el: HTMLElement, years: number[], byYear: Record<string, HmdaYear>, stateName: string) {
  const rows = years.flatMap((yr) => PURPOSES.map((p) => ({ yr, p: p.key, color: p.color, v: byYear?.[yr]?.[p.key]?.loans ?? 0 })));
  const h = 280, m = { t: 12, r: 12, b: 44, l: 64 };
  const desc = years.map((yr) => `${yr}: ${PURPOSES.map((p) => `${p.key} ${d3.format(',')(byYear?.[yr]?.[p.key]?.loans ?? 0)}`).join(', ')}`).join('. ');
  const { svg, width } = svgFor(el, h, `${stateName} mortgage originations by loan purpose. ${desc}.`);
  const x0 = d3.scaleBand<number>().domain(years).range([m.l, width - m.r]).paddingInner(0.2);
  const x1 = d3.scaleBand<string>().domain(PURPOSES.map((p) => p.key)).range([0, x0.bandwidth()]).padding(0.08);
  const y = d3.scaleLinear().domain([0, d3.max(rows, (d) => d.v) || 1]).nice().range([h - m.b, m.t]);
  svg.append('g').attr('class', 'grid').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickSize(-(width - m.l - m.r)).tickFormat(() => '')).call((g) => g.select('.domain').remove());
  svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${h - m.b})`).call(d3.axisBottom(x0).tickFormat((d) => (width < 420 ? `'${String(d).slice(2)}` : String(d))));
  svg.append('g').attr('class', 'axis').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5, '~s'));
  svg.append('text').attr('class', 'axis-label').attr('x', (m.l + width - m.r) / 2).attr('y', h - 6).attr('text-anchor', 'middle').text('Year');
  svg.append('text').attr('class', 'axis-label').attr('transform', `translate(14,${(h - m.b + m.t) / 2}) rotate(-90)`).attr('text-anchor', 'middle').text('Loans originated');
  svg.append('g').selectAll('rect').data(rows).join('rect')
    .attr('x', (d) => x0(d.yr)! + x1(d.p)!).attr('width', x1.bandwidth()).attr('fill', (d) => d.color).attr('rx', 2)
    .attr('y', y(0)).attr('height', 0)
    .call((r) => r.append('title').text((d) => `${d.yr} ${d.p}: ${d3.format(',')(d.v)} loans`))
    .transition().duration(dur(700)).delay((_, i) => dur(i * 12)).attr('y', (d) => y(d.v)).attr('height', (d) => y(0) - y(d.v));
}

/** Ranked horizontal bars for metros. */
export function metroChart(el: HTMLElement, data: { name: string; yoy: number }[], period: string) {
  const width0 = Math.max(280, el.clientWidth);
  const narrow = width0 < 640;
  const row = narrow ? 52 : 36;
  const m = { t: 8, r: 64, b: 48, l: narrow ? 8 : Math.min(380, width0 * 0.36) };
  const h = m.t + m.b + row * data.length;
  const { svg, width } = svgFor(el, h, `Bar chart: 15 metros with the largest year-over-year home price change in ${period}. ` +
    data.map((d, i) => `${i + 1}. ${d.name} ${pct(d.yoy)}`).join('; '));
  const x = d3.scaleLinear().domain([0, d3.max(data, (d) => d.yoy)!]).nice().range([m.l, width - m.r]);
  const y = (i: number) => m.t + i * row;
  const barH = narrow ? 18 : 22;
  const barY = (i: number) => y(i) + (narrow ? 24 : (row - barH) / 2);
  svg.append('g').attr('class', 'grid').attr('transform', `translate(0,${h - m.b})`).call(d3.axisBottom(x).ticks(5).tickSize(-(h - m.b - m.t)).tickFormat(() => '')).call((g) => g.select('.domain').remove());
  svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${h - m.b})`).call(d3.axisBottom(x).ticks(narrow ? 4 : 6, '.0%'));
  svg.append('text').attr('class', 'axis-label').attr('x', (m.l + width - m.r) / 2).attr('y', h - 8).attr('text-anchor', 'middle').text(`Year-over-year home price change, ${period}`);
  const g = svg.append('g').selectAll('g').data(data).join('g');
  g.append('text').attr('class', 'bar-label')
    .attr('x', narrow ? m.l : m.l - 10).attr('y', (_, i) => (narrow ? y(i) + 16 : barY(i) + barH / 2)).attr('dy', narrow ? 0 : '.35em').attr('text-anchor', narrow ? 'start' : 'end')
    .text((d, i) => `${i + 1}. ${d.name}`);
  g.append('rect').attr('x', m.l).attr('y', (_, i) => barY(i)).attr('height', barH).attr('rx', 4).attr('width', 0)
    .attr('fill', (d) => yoyColor(Math.max(d.yoy, 0.06)))
    .transition().duration(dur(900)).delay((_, i) => dur(i * 50)).ease(d3.easeCubicOut).attr('width', (d) => x(d.yoy) - m.l);
  g.append('text').attr('class', 'bar-value').attr('y', (_, i) => barY(i) + barH / 2).attr('dy', '.35em').attr('x', m.l + 6).text((d) => pct(d.yoy))
    .attr('opacity', 0).transition().duration(dur(900)).delay((_, i) => dur(i * 50)).ease(d3.easeCubicOut).attr('x', (d) => x(d.yoy) + 6).attr('opacity', 1);
}

/** Horizontal gradient legend for the map scale. */
export function legend(el: HTMLElement) {
  const w = 280, h = 58;
  d3.select(el).selectAll('*').remove();
  const svg = d3.select(el).append('svg').attr('width', w).attr('height', h);
  const grad = svg.append('defs').append('linearGradient').attr('id', 'lg');
  d3.range(0, 1.001, 0.1).forEach((t) => grad.append('stop').attr('offset', `${t * 100}%`).attr('stop-color', yoyColor(-0.1 + t * 0.2)));
  svg.append('rect').attr('x', 24).attr('y', 4).attr('width', w - 48).attr('height', 12).attr('rx', 6).attr('fill', 'url(#lg)');
  const x = d3.scaleLinear().domain([-0.1, 0.1]).range([24, w - 24]);
  svg.append('g').attr('transform', 'translate(0,18)').call(d3.axisBottom(x).ticks(5, '+.0%').tickSize(4)).call((g) => g.select('.domain').remove()).selectAll('line').style('stroke', 'var(--muted)');
  svg.append('text').attr('x', w / 2).attr('y', h - 1).attr('text-anchor', 'middle').text('Year-over-year change (±10% or more)');
}
