import * as d3 from 'd3';
import type { Topology } from 'topojson-specification';
import './style.css';
import { createMap } from './map';
import { createMetroChart } from './metroChart';
import { createStatePanel } from './statePanel';
import { fmtPct, loadJson, reducedMotion, type HmdaFile, type Metro, type StatesFile, type Summary } from './shared';

async function main() {
  const [summary, states, metros, hmda, topo] = await Promise.all([
    loadJson<Summary>('summary.json'),
    loadJson<StatesFile>('states.json'),
    loadJson<Metro[]>('metros.json'),
    loadJson<HmdaFile>('hmda.json'),
    loadJson<Topology>('us-states.json'),
  ]);
  const latest = summary.latest.label;
  const prior = `${summary.latest.year - 1} Q${summary.latest.quarter}`;
  d3.selectAll('[data-latest]').text(latest);
  d3.select('#metro-count').text(summary.metroCount);

  renderHero(summary, prior);

  const panel = createStatePanel(states, hmda, (code) => {
    map.clearSelection();
    map.focusState(code);
  });
  const map = createMap({
    data: states,
    topo,
    onSelect: (s, q) => panel.open(s, q),
    onQuarter: (q) => panel.setQuarter(q),
  });
  createMetroChart(metros, latest);
}

function renderHero(s: Summary, prior: string) {
  const cards = [
    { label: 'U.S. home prices, year over year', value: s.us.yoy, note: `${s.latest.label} vs ${prior}` },
    { label: 'U.S. home prices since 2019 Q4', value: s.us.since2019, note: `2019 Q4 to ${s.latest.label}` },
    { label: 'Fastest state, year over year', value: s.fastest.yoy, note: s.fastest.name },
    { label: 'Slowest state, year over year', value: s.slowest.yoy, note: s.slowest.name },
  ];
  const card = d3
    .select('#hero-cards')
    .selectAll('article')
    .data(cards)
    .join('article')
    .attr('class', (d) => `card ${d.value >= 0 ? 'up' : 'down'}`)
    .style('--i', (_d, i) => i);
  card.append('h3').attr('class', 'card-label').text((d) => d.label);
  const value = card
    .append('p')
    .attr('class', 'card-value')
    .text((d) => fmtPct(d.value));
  card
    .append('p')
    .attr('class', 'card-note')
    .text((d) => d.note);

  if (reducedMotion()) return;
  value
    .attr('aria-hidden', 'true')
    .transition()
    .duration(1400)
    .delay((_d, i) => 200 + i * 120)
    .ease(d3.easeCubicOut)
    .tween('text', function (d) {
      const interp = d3.interpolateNumber(0, d.value);
      return (t) => {
        this.textContent = fmtPct(interp(t));
      };
    })
    .on('end', function (d) {
      this.textContent = fmtPct(d.value);
      this.removeAttribute('aria-hidden');
    });
}

main().catch((err) => {
  console.error(err);
  d3.select('#main').insert('p', ':first-child').attr('class', 'error').attr('role', 'alert').text('The data could not load. Please reload the page.');
});
