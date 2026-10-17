import * as d3 from 'd3';
import { fmtPct, onResize, reducedMotion, yoyColor, type Metro } from './shared';

export function createMetroChart(metros: Metro[], latestLabel: string) {
  const el = document.querySelector<HTMLElement>('#metro-chart')!;
  let shown = false;

  function draw(animate: boolean) {
    const w = el.clientWidth || 360;
    const row = 46;
    const m = { t: 8, r: 64, b: 48, l: 12 };
    const h = m.t + metros.length * row + m.b;
    const x = d3
      .scaleLinear()
      .domain([Math.min(0, d3.min(metros, (d) => d.yoy)!), d3.max(metros, (d) => d.yoy)!])
      .nice()
      .range([m.l, w - m.r]);
    const svg = d3
      .select(el)
      .html('')
      .append('svg')
      .attr('viewBox', `0 0 ${w} ${h}`)
      .attr('role', 'img')
      .attr(
        'aria-label',
        `Bar chart of the 15 metros with the largest year-over-year home price change in ${latestLabel}. ` +
          metros.map((d) => `${d.rank}. ${d.name}: ${fmtPct(d.yoy)}`).join('; '),
      );
    svg
      .append('g')
      .attr('class', 'axis grid')
      .attr('transform', `translate(0,${h - m.b})`)
      .call(d3.axisBottom(x).ticks(w < 500 ? 4 : 8).tickFormat((d) => `${d}%`).tickSize(-(h - m.t - m.b)))
      .call((g) => g.select('.domain').remove());
    svg
      .append('text')
      .attr('class', 'axis-label')
      .attr('x', (w - m.r + m.l) / 2)
      .attr('y', h - 8)
      .attr('text-anchor', 'middle')
      .text('Year-over-year change in HPI (%)');

    const g = svg
      .append('g')
      .selectAll('g')
      .data(metros)
      .join('g')
      .attr('transform', (_d, i) => `translate(0,${m.t + i * row})`);
    g.append('text')
      .attr('class', 'bar-name')
      .attr('x', m.l)
      .attr('y', 14)
      .text((d) => `${d.rank}. ${d.name}`);
    const bar = g
      .append('rect')
      .attr('class', 'bar')
      .attr('x', x(0))
      .attr('y', 20)
      .attr('height', 16)
      .attr('rx', 3)
      .attr('fill', (d) => yoyColor(d.yoy))
      .attr('width', 0);
    const val = g
      .append('text')
      .attr('class', 'bar-value')
      .attr('x', x(0) + 6)
      .attr('y', 33)
      .text((d) => fmtPct(d.yoy))
      .attr('opacity', 0);
    const t = animate && !reducedMotion();
    bar
      .transition()
      .duration(t ? 800 : 0)
      .delay((_d, i) => (t ? i * 45 : 0))
      .ease(d3.easeCubicOut)
      .attr('width', (d) => Math.max(0, x(d.yoy) - x(0)));
    val
      .transition()
      .duration(t ? 800 : 0)
      .delay((_d, i) => (t ? i * 45 : 0))
      .ease(d3.easeCubicOut)
      .attr('x', (d) => x(Math.max(0, d.yoy)) + 6)
      .attr('opacity', 1);
  }

  draw(false);
  d3.select(el).select('svg').selectAll('.bar').interrupt().attr('width', 0);
  d3.select(el).select('svg').selectAll('.bar-value').interrupt().attr('opacity', 0);
  new IntersectionObserver(
    (entries, obs) => {
      if (entries.some((e) => e.isIntersecting)) {
        shown = true;
        draw(true);
        obs.disconnect();
      }
    },
    { threshold: 0.2 },
  ).observe(el);
  onResize(el, () => shown && draw(false));
}
