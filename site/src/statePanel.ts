import * as d3 from 'd3';
import {
  fmtCompact,
  fmtDollars,
  fmtInt,
  fmtPct,
  onResize,
  purposeColors,
  reducedMotion,
  type HmdaFile,
  type StateData,
  type StatesFile,
} from './shared';

export function createStatePanel(data: StatesFile, hmda: HmdaFile, onClose: (code: string) => void) {
  const panel = document.querySelector<HTMLElement>('#state-panel')!;
  const closeBtn = document.querySelector<HTMLButtonElement>('#close-panel')!;
  const lineEl = document.querySelector<HTMLElement>('#state-line')!;
  const hmdaEl = document.querySelector<HTMLElement>('#state-hmda')!;
  const dates = data.quarters.map((q) => new Date(+q.slice(0, 4), (+q.slice(-1) - 1) * 3, 1));
  let state: StateData | null = null;
  let quarter = data.quarters.length - 1;

  function close() {
    if (!state) return;
    const code = state.code;
    panel.hidden = true;
    state = null;
    onClose(code);
  }
  closeBtn.addEventListener('click', close);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close();
  });
  onResize(panel, () => state && render(false));

  function render(animate: boolean, quarterOnly = false) {
    if (!state) return;
    const s = state;
    const latest = data.quarters.length - 1;
    d3.select('#state-title').text(s.name);
    d3.select('#state-region').text(`${s.division} · ${s.region}`);
    const rows = hmda.states[s.code] ?? [];
    const lastYear = rows[rows.length - 1];
    d3.select('#state-stats').html(
      stat(`YoY, ${data.quarters[quarter]}`, fmtPct(s.yoy[quarter])) +
        stat(`Since 2019 Q4`, fmtPct(s.since2019)) +
        stat(`Loans, ${lastYear?.year ?? ''}`, lastYear ? fmtCompact(d3.sum(lastYear.loans)) : 'n/a'),
    );
    drawLine(s, quarter, latest, animate);
    if (!quarterOnly) drawHmda(s, rows, animate);
  }

  function stat(label: string, value: string) {
    return `<div class="stat"><span class="stat-label">${label}</span><span class="stat-value">${value}</span></div>`;
  }

  function drawLine(s: StateData, q: number, latest: number, animate: boolean) {
    const w = lineEl.clientWidth || 320;
    const h = 200;
    const m = { t: 12, r: 14, b: 38, l: 48 };
    const pts = s.index.map((v, i) => ({ d: dates[i], v })).filter((p): p is { d: Date; v: number } => p.v != null);
    const x = d3.scaleTime().domain(d3.extent(dates) as [Date, Date]).range([m.l, w - m.r]);
    const y = d3.scaleLinear().domain([0, d3.max(pts, (p) => p.v)! * 1.05]).nice().range([h - m.b, m.t]);
    const svg = d3
      .select(lineEl)
      .html('')
      .append('svg')
      .attr('viewBox', `0 0 ${w} ${h}`)
      .attr('role', 'img')
      .attr(
        'aria-label',
        `${s.name} house price index from ${data.quarters[0]} to ${data.quarters[latest]}: ${pts[0]?.v.toFixed(0)} to ${pts[pts.length - 1]?.v.toFixed(0)}.`,
      );
    svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${h - m.b})`).call(d3.axisBottom(x).ticks(w < 400 ? 4 : 6));
    svg
      .append('g')
      .attr('class', 'axis grid')
      .attr('transform', `translate(${m.l},0)`)
      .call(d3.axisLeft(y).ticks(5).tickSize(-(w - m.l - m.r)))
      .call((g) => g.select('.domain').remove());
    svg.append('text').attr('class', 'axis-label').attr('x', (w + m.l) / 2).attr('y', h - 4).attr('text-anchor', 'middle').text('Quarter');
    svg
      .append('text')
      .attr('class', 'axis-label')
      .attr('transform', `translate(12,${(h - m.b + m.t) / 2}) rotate(-90)`)
      .attr('text-anchor', 'middle')
      .text('HPI (1991 Q1 = 100)');
    const area = d3.area<{ d: Date; v: number }>().x((p) => x(p.d)).y0(y(0)).y1((p) => y(p.v)).curve(d3.curveMonotoneX);
    const line = d3.line<{ d: Date; v: number }>().x((p) => x(p.d)).y((p) => y(p.v)).curve(d3.curveMonotoneX);
    svg.append('path').datum(pts).attr('class', 'line-area').attr('d', area);
    const lp = svg.append('path').datum(pts).attr('class', 'line').attr('d', line);
    if (animate && !reducedMotion()) {
      const len = (lp.node() as SVGPathElement).getTotalLength();
      lp.attr('stroke-dasharray', `${len} ${len}`)
        .attr('stroke-dashoffset', len)
        .transition()
        .duration(900)
        .ease(d3.easeCubicOut)
        .attr('stroke-dashoffset', 0);
    }
    const cur = s.index[q];
    if (cur != null) {
      const g = svg.append('g').attr('class', 'marker').attr('transform', `translate(${x(dates[q])},0)`);
      g.append('line').attr('y1', m.t).attr('y2', h - m.b);
      g.append('circle').attr('cy', y(cur)).attr('r', 4.5);
    }
  }

  function drawHmda(s: StateData, rows: HmdaFile['states'][string], animate: boolean) {
    const w = hmdaEl.clientWidth || 320;
    const h = 220;
    const m = { t: 12, r: 10, b: 38, l: 52 };
    const keys = hmda.purposes;
    const stacked = d3.stack<(typeof rows)[number], number>().keys(keys.map((_, i) => i)).value((d, k) => d.loans[k])(rows);
    const x = d3.scaleBand<number>().domain(hmda.years).range([m.l, w - m.r]).padding(0.22);
    const y = d3.scaleLinear().domain([0, d3.max(rows, (r) => d3.sum(r.loans)) ?? 1]).nice().range([h - m.b, m.t]);
    const root = d3.select(hmdaEl).html('');
    root
      .append('ul')
      .attr('class', 'chart-legend')
      .attr('aria-hidden', 'true')
      .selectAll('li')
      .data(keys)
      .join('li')
      .html((k, i) => `<span class="swatch" style="background:${purposeColors[i]}"></span>${k}`);
    const svg = root
      .append('svg')
      .attr('viewBox', `0 0 ${w} ${h}`)
      .attr('role', 'img')
      .attr(
        'aria-label',
        `${s.name} originated mortgage loans by purpose, ${hmda.years[0]} to ${hmda.years[hmda.years.length - 1]}. ` +
          rows.map((r) => `${r.year}: ${fmtInt(d3.sum(r.loans))} loans`).join('; '),
      );
    svg
      .append('g')
      .attr('class', 'axis')
      .attr('transform', `translate(0,${h - m.b})`)
      .call(d3.axisBottom(x).tickFormat((d) => (w < 360 ? `’${String(d).slice(2)}` : String(d))));
    svg
      .append('g')
      .attr('class', 'axis grid')
      .attr('transform', `translate(${m.l},0)`)
      .call(d3.axisLeft(y).ticks(5).tickFormat((d) => fmtCompact(+d)).tickSize(-(w - m.l - m.r)))
      .call((g) => g.select('.domain').remove());
    svg.append('text').attr('class', 'axis-label').attr('x', (w + m.l) / 2).attr('y', h - 4).attr('text-anchor', 'middle').text('Year');
    svg
      .append('text')
      .attr('class', 'axis-label')
      .attr('transform', `translate(12,${(h - m.b + m.t) / 2}) rotate(-90)`)
      .attr('text-anchor', 'middle')
      .text('Originated loans');
    const bars = svg
      .append('g')
      .selectAll('g')
      .data(stacked)
      .join('g')
      .attr('fill', (_d, i) => purposeColors[i])
      .selectAll('rect')
      .data((series) => series.map((p) => ({ p, k: series.key })))
      .join('rect')
      .attr('x', (d) => x(d.p.data.year)!)
      .attr('width', x.bandwidth())
      .attr('y', y(0))
      .attr('height', 0);
    bars
      .append('title')
      .text(({ p, k }) => `${p.data.year} ${keys[k]}: ${fmtInt(p.data.loans[k])} loans, ${fmtDollars(p.data.volume[k])}`);
    const motion = animate && !reducedMotion();
    bars
      .transition()
      .duration(motion ? 700 : 0)
      .delay((_d, i) => (motion ? i * 40 : 0))
      .attr('y', (d) => y(d.p[1]))
      .attr('height', (d) => y(d.p[0]) - y(d.p[1]));

    const table = `<table><caption class="sr-only">${s.name} originated loans by purpose</caption><thead><tr><th scope="col">Year</th>${keys
      .map((k) => `<th scope="col">${k}</th>`)
      .join('')}<th scope="col">Total volume</th></tr></thead><tbody>${rows
      .map(
        (r) =>
          `<tr><th scope="row">${r.year}</th>${r.loans.map((l) => `<td>${fmtInt(l)}</td>`).join('')}<td>${fmtDollars(d3.sum(r.volume))}</td></tr>`,
      )
      .join('')}</tbody></table>`;
    d3.select('#state-hmda-table').html(table);
  }

  return {
    open(s: StateData, q: number) {
      const isNew = state?.code !== s.code;
      state = s;
      quarter = q;
      panel.hidden = false;
      render(isNew);
      if (isNew) {
        panel.scrollTop = 0;
        if (window.matchMedia('(max-width: 900px)').matches) panel.scrollIntoView({ behavior: reducedMotion() ? 'auto' : 'smooth', block: 'start' });
      }
      closeBtn.focus({ preventScroll: true });
    },
    setQuarter(q: number) {
      quarter = q;
      if (state) render(false, true);
    },
  };
}
