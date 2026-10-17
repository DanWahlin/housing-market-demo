// Converts ../data/*.csv into small JSON files in public/data. Run with Node 24.
import { readFileSync, writeFileSync, mkdirSync, copyFileSync } from 'node:fs';
import { csvParse } from 'd3-dsv';
import { qKey, qLabel, yoy, change, monthlyToQuarterly, rank, type Series } from '../src/math.ts';

const root = new URL('../../data/', import.meta.url);
const out = new URL('../public/data/', import.meta.url);
mkdirSync(out, { recursive: true });

const read = (f: string) => csvParse(readFileSync(new URL(f, root), 'utf8'));
const write = (f: string, data: unknown) => writeFileSync(new URL(f, out), JSON.stringify(data));
const r3 = (v: number | null) => (v == null ? null : Math.round(v * 10000) / 10000);
const START = qKey(2000, 1);
const BASE_2019Q4 = qKey(2019, 4);

// States HPI
const states = read('states.csv');
const stateNsa = new Map<string, Series>();
const stateSa = new Map<string, Series>();
for (const r of read('hpi_state_quarterly.csv')) {
  const k = qKey(+r.year!, +r.quarter!);
  if (!stateNsa.has(r.state_code!)) { stateNsa.set(r.state_code!, new Map()); stateSa.set(r.state_code!, new Map()); }
  stateNsa.get(r.state_code!)!.set(k, +r.index_nsa!);
  stateSa.get(r.state_code!)!.set(k, +r.index_sa!);
}
const latest = Math.max(...[...stateNsa.values()].map((s) => Math.max(...s.keys())));
const quarters: number[] = [];
for (let k = START; k <= latest; k++) quarters.push(k);

write('states.json', {
  quarters: quarters.map(qLabel),
  states: states.map((s) => ({
    code: s.state_code,
    name: s.state_name,
    fips: s.fips,
    yoy: quarters.map((k) => r3(yoy(stateNsa.get(s.state_code!)!, k))),
    sa: quarters.map((k) => stateSa.get(s.state_code!)!.get(k) ?? null),
  })),
});

// U.S. national series (monthly -> quarterly mean of index_nsa)
const usMonthly = read('hpi_us_division_monthly.csv')
  .filter((r) => r.place_id === 'USA')
  .map((r) => ({ year: +r.year!, month: +r.month!, value: +r.index_nsa! }));
const us = monthlyToQuarterly(usMonthly);
const usLatest = Math.min(latest, Math.max(...us.keys()));

const stateYoy = states.map((s) => ({ code: s.state_code!, name: s.state_name! }));
const ranked = rank(stateYoy, (s) => yoy(stateNsa.get(s.code)!, latest));

// Metros: top 15 by latest YoY
const metroNsa = new Map<string, { name: string; s: Series }>();
for (const r of read('hpi_metro_quarterly.csv')) {
  if (!metroNsa.has(r.cbsa_code!)) metroNsa.set(r.cbsa_code!, { name: r.metro_name!, s: new Map() });
  metroNsa.get(r.cbsa_code!)!.s.set(qKey(+r.year!, +r.quarter!), +r.index_nsa!);
}
const metroLatest = Math.max(...[...metroNsa.values()].map((m) => Math.max(...m.s.keys())));
const topMetros = rank([...metroNsa.entries()].map(([code, m]) => ({ code, name: m.name, s: m.s })), (m) => yoy(m.s, metroLatest), 15)
  .map((m) => ({ code: m.code, name: m.name, yoy: r3(m.value) }));
write('metros.json', { period: qLabel(metroLatest), count: metroNsa.size, top: topMetros });

write('summary.json', {
  period: qLabel(latest),
  usPeriod: qLabel(usLatest),
  usYoy: r3(yoy(us, usLatest)),
  usSince2019Q4: r3(change(us, usLatest, BASE_2019Q4)),
  fastest: { ...ranked[0], value: r3(ranked[0].value) },
  slowest: { ...ranked.at(-1)!, value: r3(ranked.at(-1)!.value) },
});

// HMDA: { state: { years: [...], purposes: { purpose: loans[] } } }
const hmda: Record<string, Record<string, Record<string, { loans: number; volume: number }>>> = {};
const years = new Set<number>();
for (const r of read('hmda_state_originations.csv')) {
  years.add(+r.year!);
  ((hmda[r.state_code!] ??= {})[r.year!] ??= {})[r.loan_purpose!] = { loans: +r.loans!, volume: +r.dollar_volume! };
}
write('hmda.json', { years: [...years].sort(), byState: hmda });

copyFileSync(new URL('../node_modules/us-atlas/states-albers-10m.json', import.meta.url), new URL('us-states.json', out));
console.log(`Data built: latest state quarter ${qLabel(latest)}, U.S. ${qLabel(usLatest)}, metros ${qLabel(metroLatest)}`);
