// Reads ../data/*.csv (read only) and writes small JSON files to public/data/.
import { csvParse } from 'd3-dsv';
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  latestQuarter,
  placeMetrics,
  qKey,
  qLabel,
  rankByYoy,
  yoyChange,
  type QuarterPoint,
} from '../src/metrics.ts';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const dataDir = join(root, '..', 'data');
const outDir = join(root, 'public', 'data');
mkdirSync(outDir, { recursive: true });

const read = (f: string) => csvParse(readFileSync(join(dataDir, f), 'utf8'));
// Keep 4 decimals so that the page rounds only once (rounding twice can change the last digit).
const r1 = (n: number) => (Number.isFinite(n) ? Math.round(n * 10000) / 10000 : null);
const write = (f: string, d: unknown) => writeFileSync(join(outDir, f), JSON.stringify(d));

const START_YEAR = 2000;
const BASE = { year: 2019, quarter: 4 };

// States
const states = read('states.csv');
const stateRows = read('hpi_state_quarterly.csv');
const latest = latestQuarter(stateRows.map((r) => ({ year: +r.year!, quarter: +r.quarter! })));
const seriesBy = (rows: typeof stateRows, key: string, column: 'index_nsa' | 'index_sa' = 'index_nsa') => {
  const m = new Map<string, QuarterPoint[]>();
  for (const r of rows) {
    const id = r[key]!;
    if (!m.has(id)) m.set(id, []);
    m.get(id)!.push({ year: +r.year!, quarter: +r.quarter!, value: +r[column]! });
  }
  return m;
};
const stateSeries = seriesBy(stateRows, 'state_code');
const stateSeriesSa = seriesBy(stateRows, 'state_code', 'index_sa');

const quarters: { year: number; quarter: number }[] = [];
for (let k = qKey(START_YEAR, 1); k <= qKey(latest.year, latest.quarter); k++) {
  quarters.push({ year: Math.floor(k / 4), quarter: (k % 4) + 1 });
}

const stateOut = states.map((s) => {
  const series = stateSeries.get(s.state_code!) ?? [];
  return {
    code: s.state_code!,
    name: s.state_name!,
    fips: s.fips!,
    region: s.region!,
    division: s.division!,
    index: quarters.map((q) => r1(series.find((p) => p.year === q.year && p.quarter === q.quarter)?.value ?? NaN)),
    yoy: quarters.map((q) => r1(yoyChange(series, q.year, q.quarter))),
    since2019: r1(placeMetrics(series, stateSeriesSa.get(s.state_code!) ?? [], latest, BASE).since),
  };
});

// U.S.: FHFA's official quarterly U.S. index (see AGENTS.md)
const usRows = read('hpi_us_quarterly.csv');
const us = placeMetrics(seriesBy(usRows, 'place_id').get('USA')!, seriesBy(usRows, 'place_id', 'index_sa').get('USA')!, latest, BASE);
const usYoy = us.yoy;
const usSince = us.since;

const ranked = rankByYoy(
  stateOut.map((s) => ({ id: s.code, name: s.name, yoy: s.yoy[s.yoy.length - 1] ?? NaN })),
);
const fastest = ranked[0];
const slowest = ranked[ranked.length - 1];

// Metros
const metroRows = read('hpi_metro_quarterly.csv');
const metroSeries = seriesBy(metroRows, 'cbsa_code');
const metroNames = new Map(metroRows.map((r) => [r.cbsa_code!, r.metro_name!]));
const metroRanked = rankByYoy(
  [...metroSeries.entries()].map(([id, s]) => ({ id, name: metroNames.get(id)!, yoy: yoyChange(s, latest.year, latest.quarter) })),
);

// HMDA
const hmdaRows = read('hmda_state_originations.csv');
const purposes = ['Home purchase', 'Refinance', 'Cash-out refinance'];
const years = [...new Set(hmdaRows.map((r) => +r.year!))].sort((a, b) => a - b);
const hmda: Record<string, { year: number; loans: number[]; volume: number[] }[]> = {};
for (const r of hmdaRows) {
  const list = (hmda[r.state_code!] ??= years.map((year) => ({ year, loans: [0, 0, 0], volume: [0, 0, 0] })));
  const row = list.find((d) => d.year === +r.year!)!;
  const i = purposes.indexOf(r.loan_purpose!);
  row.loans[i] = +r.loans!;
  row.volume[i] = +r.dollar_volume!;
}

write('summary.json', {
  latest: { ...latest, label: qLabel(latest.year, latest.quarter) },
  us: { yoy: r1(usYoy), since2019: r1(usSince) },
  fastest: { code: fastest.id, name: fastest.name, yoy: r1(fastest.yoy) },
  slowest: { code: slowest.id, name: slowest.name, yoy: r1(slowest.yoy) },
  metroCount: metroRanked.length,
});
write('states.json', { quarters: quarters.map((q) => qLabel(q.year, q.quarter)), states: stateOut });
write('metros.json', metroRanked.slice(0, 15).map((m, i) => ({ rank: i + 1, cbsa: m.id, name: m.name, yoy: r1(m.yoy) })));
write('hmda.json', { years, purposes, states: hmda });
copyFileSync(join(root, 'node_modules', 'us-atlas', 'states-albers-10m.json'), join(outDir, 'us-states.json'));

console.log(
  `Data: latest ${qLabel(latest.year, latest.quarter)} | U.S. YoY ${usYoy.toFixed(2)}% | since 2019 Q4 ${usSince.toFixed(2)}% | ` +
    `fastest ${fastest.id} ${fastest.yoy.toFixed(2)}% | slowest ${slowest.id} ${slowest.yoy.toFixed(2)}%`,
);
