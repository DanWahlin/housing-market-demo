import * as d3 from 'd3';
import { feature } from 'topojson-client';
import type { Topology, GeometryCollection } from 'topojson-specification';
import { fmtPct, reducedMotion, YOY_LIMIT, yoyColor, type StateData, type StatesFile } from './shared';

interface MapOptions {
  data: StatesFile;
  topo: Topology;
  onSelect: (s: StateData, quarter: number) => void;
  onQuarter: (quarter: number) => void;
}

export function createMap({ data, topo, onSelect, onQuarter }: MapOptions) {
  const byFips = new Map(data.states.map((s) => [s.fips, s]));
  const svg = d3.select<SVGSVGElement, unknown>('#map').attr('viewBox', '0 0 975 610');
  const tooltip = d3.select<HTMLDivElement, unknown>('#tooltip');
  const wrap = document.querySelector<HTMLElement>('.map-wrap')!;
  const last = data.quarters.length - 1;
  let current = last;
  let selected: string | null = null;

  const geo = feature(topo, topo.objects.states as GeometryCollection);
  const path = d3.geoPath();
  const shapes = geo.features
    .map((f) => ({ f, s: byFips.get(String(f.id).padStart(2, '0')) }))
    .filter((d): d is { f: (typeof geo.features)[number]; s: StateData } => !!d.s)
    .sort((a, b) => a.s.name.localeCompare(b.s.name));

  const label = (s: StateData) =>
    `${s.name}: ${fmtPct(s.yoy[current])} year over year in ${data.quarters[current]}. Press Enter for details.`;

  const paths = svg
    .append('g')
    .selectAll<SVGPathElement, (typeof shapes)[number]>('path')
    .data(shapes)
    .join('path')
    .attr('class', 'state')
    .attr('d', (d) => path(d.f))
    .attr('tabindex', 0)
    .attr('role', 'button')
    .on('pointermove', (event: PointerEvent, d) => showTip(d.s, event.clientX, event.clientY))
    .on('pointerleave', hideTip)
    .on('focus', function (_e, d) {
      const r = (this as SVGPathElement).getBoundingClientRect();
      showTip(d.s, r.left + r.width / 2, r.top + r.height / 2);
    })
    .on('blur', hideTip)
    .on('click', (_e, d) => select(d.s))
    .on('keydown', (event: KeyboardEvent, d) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        select(d.s);
      }
    });

  svg
    .append('path')
    .datum(geo)
    .attr('class', 'state-borders')
    .attr('d', path(geo) ?? '');

  function select(s: StateData) {
    selected = s.code;
    paths.classed('selected', (d) => d.s.code === selected);
    onSelect(s, current);
  }

  function showTip(s: StateData, x: number, y: number) {
    const box = wrap.getBoundingClientRect();
    const idx = s.index[current];
    tooltip
      .attr('hidden', null)
      .html(
        `<strong>${s.name}</strong><span class="tip-period">${data.quarters[current]}</span>` +
          `<dl><dt>Year over year</dt><dd>${fmtPct(s.yoy[current])}</dd>` +
          `<dt>HPI</dt><dd>${idx == null ? 'n/a' : idx.toFixed(1)}</dd>` +
          `<dt>Since 2019 Q4</dt><dd>${fmtPct(s.since2019)}*</dd></dl>` +
          `<span class="tip-note">*Latest quarter</span>`,
      );
    const tip = tooltip.node()!;
    const left = Math.min(Math.max(x - box.left + 14, 4), box.width - tip.offsetWidth - 4);
    const top = y - box.top - tip.offsetHeight - 14;
    tooltip.style('left', `${left}px`).style('top', `${top < 4 ? y - box.top + 18 : top}px`);
  }

  function hideTip() {
    tooltip.attr('hidden', true);
  }

  function setQuarter(i: number, animate = false) {
    current = i;
    const t = paths.transition().duration(animate && !reducedMotion() ? 280 : 0).ease(d3.easeCubicOut);
    // States with no value get the .na class; its CSS fill follows the theme.
    paths.classed('na', (d) => d.s.yoy[i] == null);
    t.attr('fill', (d) => (d.s.yoy[i] == null ? null : yoyColor(d.s.yoy[i]!)));
    paths.attr('aria-label', (d) => label(d.s));
    d3.select('#map-period').text(data.quarters[i]);
    slider.value = String(i);
    slider.setAttribute('aria-valuetext', data.quarters[i]);
    d3.select('#quarter-label').text(data.quarters[i]);
    hideTip();
    onQuarter(i);
  }

  // Timeline controls
  const slider = document.querySelector<HTMLInputElement>('#quarter-slider')!;
  const play = document.querySelector<HTMLButtonElement>('#play')!;
  slider.max = String(last);
  slider.addEventListener('input', () => {
    stop();
    setQuarter(+slider.value, true);
  });
  let timer: number | undefined;
  function stop() {
    if (timer) window.clearInterval(timer);
    timer = undefined;
    play.classList.remove('playing');
    play.setAttribute('aria-label', 'Play timeline');
  }
  play.addEventListener('click', () => {
    if (timer) return stop();
    if (current >= last) setQuarter(0);
    play.classList.add('playing');
    play.setAttribute('aria-label', 'Pause timeline');
    timer = window.setInterval(() => {
      if (current >= last) return stop();
      setQuarter(current + 1, true);
    }, 320);
  });

  drawLegend();
  setQuarter(last);

  return {
    clearSelection() {
      selected = null;
      paths.classed('selected', false);
    },
    focusState(code: string) {
      paths.filter((d) => d.s.code === code).node()?.focus();
    },
  };
}

function drawLegend() {
  const w = 300;
  const h = 10;
  const svg = d3
    .select('#legend')
    .append('svg')
    .attr('viewBox', `0 0 ${w + 40} 52`)
    .attr('role', 'img')
    .attr('aria-label', `Color legend: purple is falling prices, orange is rising prices, from −${YOY_LIMIT}% to +${YOY_LIMIT}% or more.`);
  const grad = svg.append('defs').append('linearGradient').attr('id', 'legend-grad');
  d3.range(0, 1.01, 0.1).forEach((t) =>
    grad.append('stop').attr('offset', `${t * 100}%`).attr('stop-color', yoyColor(-YOY_LIMIT + t * 2 * YOY_LIMIT)),
  );
  const g = svg.append('g').attr('transform', 'translate(20,18)');
  g.append('rect').attr('width', w).attr('height', h).attr('rx', 3).attr('fill', 'url(#legend-grad)');
  const x = d3.scaleLinear().domain([-YOY_LIMIT, YOY_LIMIT]).range([0, w]);
  g.append('g')
    .attr('transform', `translate(0,${h})`)
    .call(d3.axisBottom(x).tickValues([-15, -10, -5, 0, 5, 10, 15]).tickFormat((d) => `${+d > 0 ? '+' : +d < 0 ? '−' : ''}${Math.abs(+d)}%`).tickSize(4))
    .call((a) => a.select('.domain').remove());
  svg.append('text').attr('x', 20).attr('y', 12).attr('class', 'legend-title').text('Year-over-year change in HPI (±15% or more)');
}
