// Downloads FHFA HPI and CFPB HMDA data and writes five CSV files to data/.
// Usage: node scripts/fetch-data.mjs   (Node 18+, no npm packages)
import { mkdir, writeFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const DATA = join(dirname(fileURLToPath(import.meta.url)), '..', 'data');
const HPI_URL = 'https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv';
const HMDA_URL = 'https://ffiec.cfpb.gov/v2/data-browser-api/view/aggregations';
const HMDA_YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
const LOAN_PURPOSES = { 1: 'Home purchase', 31: 'Refinance', 32: 'Cash-out refinance' };

// 50 states + DC: [code, name, fips, region, division]
const STATES = [
  ['AL', 'Alabama', '01', 'South', 'East South Central'],
  ['AK', 'Alaska', '02', 'West', 'Pacific'],
  ['AZ', 'Arizona', '04', 'West', 'Mountain'],
  ['AR', 'Arkansas', '05', 'South', 'West South Central'],
  ['CA', 'California', '06', 'West', 'Pacific'],
  ['CO', 'Colorado', '08', 'West', 'Mountain'],
  ['CT', 'Connecticut', '09', 'Northeast', 'New England'],
  ['DE', 'Delaware', '10', 'South', 'South Atlantic'],
  ['DC', 'District of Columbia', '11', 'South', 'South Atlantic'],
  ['FL', 'Florida', '12', 'South', 'South Atlantic'],
  ['GA', 'Georgia', '13', 'South', 'South Atlantic'],
  ['HI', 'Hawaii', '15', 'West', 'Pacific'],
  ['ID', 'Idaho', '16', 'West', 'Mountain'],
  ['IL', 'Illinois', '17', 'Midwest', 'East North Central'],
  ['IN', 'Indiana', '18', 'Midwest', 'East North Central'],
  ['IA', 'Iowa', '19', 'Midwest', 'West North Central'],
  ['KS', 'Kansas', '20', 'Midwest', 'West North Central'],
  ['KY', 'Kentucky', '21', 'South', 'East South Central'],
  ['LA', 'Louisiana', '22', 'South', 'West South Central'],
  ['ME', 'Maine', '23', 'Northeast', 'New England'],
  ['MD', 'Maryland', '24', 'South', 'South Atlantic'],
  ['MA', 'Massachusetts', '25', 'Northeast', 'New England'],
  ['MI', 'Michigan', '26', 'Midwest', 'East North Central'],
  ['MN', 'Minnesota', '27', 'Midwest', 'West North Central'],
  ['MS', 'Mississippi', '28', 'South', 'East South Central'],
  ['MO', 'Missouri', '29', 'Midwest', 'West North Central'],
  ['MT', 'Montana', '30', 'West', 'Mountain'],
  ['NE', 'Nebraska', '31', 'Midwest', 'West North Central'],
  ['NV', 'Nevada', '32', 'West', 'Mountain'],
  ['NH', 'New Hampshire', '33', 'Northeast', 'New England'],
  ['NJ', 'New Jersey', '34', 'Northeast', 'Middle Atlantic'],
  ['NM', 'New Mexico', '35', 'West', 'Mountain'],
  ['NY', 'New York', '36', 'Northeast', 'Middle Atlantic'],
  ['NC', 'North Carolina', '37', 'South', 'South Atlantic'],
  ['ND', 'North Dakota', '38', 'Midwest', 'West North Central'],
  ['OH', 'Ohio', '39', 'Midwest', 'East North Central'],
  ['OK', 'Oklahoma', '40', 'South', 'West South Central'],
  ['OR', 'Oregon', '41', 'West', 'Pacific'],
  ['PA', 'Pennsylvania', '42', 'Northeast', 'Middle Atlantic'],
  ['RI', 'Rhode Island', '44', 'Northeast', 'New England'],
  ['SC', 'South Carolina', '45', 'South', 'South Atlantic'],
  ['SD', 'South Dakota', '46', 'Midwest', 'West North Central'],
  ['TN', 'Tennessee', '47', 'South', 'East South Central'],
  ['TX', 'Texas', '48', 'South', 'West South Central'],
  ['UT', 'Utah', '49', 'West', 'Mountain'],
  ['VT', 'Vermont', '50', 'Northeast', 'New England'],
  ['VA', 'Virginia', '51', 'South', 'South Atlantic'],
  ['WA', 'Washington', '53', 'West', 'Pacific'],
  ['WV', 'West Virginia', '54', 'South', 'South Atlantic'],
  ['WI', 'Wisconsin', '55', 'Midwest', 'East North Central'],
  ['WY', 'Wyoming', '56', 'West', 'Mountain'],
];
const STATE_NAME = Object.fromEntries(STATES.map(s => [s[0], s[1]]));

// Minimal RFC 4180 CSV parser (handles quoted fields with commas and "" escapes).
function parseCsv(text) {
  const rows = [];
  let row = [], field = '', inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; } else inQuotes = false;
      } else field += c;
    } else if (c === '"') inQuotes = true;
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(field); rows.push(row); row = []; field = '';
    } else field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows.filter(r => r.length > 1 || r[0] !== '');
}

const esc = v => {
  const s = v == null ? '' : String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};
async function writeCsv(name, header, rows) {
  const body = [header, ...rows].map(r => r.map(esc).join(',')).join('\n') + '\n';
  await writeFile(join(DATA, name), body);
  console.log(`wrote data/${name} (${rows.length} rows)`);
}

const byKeys = (...keys) => (a, b) => {
  for (const k of keys) { if (a[k] < b[k]) return -1; if (a[k] > b[k]) return 1; }
  return 0;
};

async function fetchHpi() {
  console.log(`downloading ${HPI_URL} ...`);
  const res = await fetch(HPI_URL);
  if (!res.ok) throw new Error(`FHFA HTTP ${res.status}`);
  const [header, ...rows] = parseCsv(await res.text());
  const col = Object.fromEntries(header.map((h, i) => [h.trim(), i]));
  const recs = rows
    .map(r => Object.fromEntries(Object.entries(col).map(([k, i]) => [k, (r[i] ?? '').trim()])))
    .filter(r => r.hpi_type === 'traditional' && r.hpi_flavor === 'purchase-only')
    .map(r => ({ ...r, yr: +r.yr, period: +r.period }));
  const pick = (freq, level) => recs.filter(r => r.frequency === freq && r.level === level)
    .sort(byKeys('place_id', 'yr', 'period'));

  const state = pick('quarterly', 'State').filter(r => STATE_NAME[r.place_id])
    .map(r => [r.place_id, STATE_NAME[r.place_id], r.yr, r.period, r.index_nsa, r.index_sa]);
  await writeCsv('hpi_state_quarterly.csv', ['state_code', 'state_name', 'year', 'quarter', 'index_nsa', 'index_sa'], state);

  const metro = pick('quarterly', 'MSA')
    .map(r => [r.place_id, r.place_name, r.yr, r.period, r.index_nsa, r.index_sa]);
  await writeCsv('hpi_metro_quarterly.csv', ['cbsa_code', 'metro_name', 'year', 'quarter', 'index_nsa', 'index_sa'], metro);

  const div = pick('monthly', 'USA or Census Division')
    .map(r => [r.place_id, r.place_name, r.yr, r.period, r.index_nsa, r.index_sa]);
  await writeCsv('hpi_us_division_monthly.csv', ['place_id', 'place_name', 'year', 'month', 'index_nsa', 'index_sa'], div);
}

async function fetchHmdaOne(state, year) {
  const url = `${HMDA_URL}?years=${year}&states=${state}&actions_taken=1&loan_purposes=1,31,32`;
  for (let attempt = 1; attempt <= 4; attempt++) {
    try {
      const res = await fetch(url, { headers: { 'User-Agent': 'curl/8.7.1', Accept: 'application/json' } });
      if (res.status === 400 || res.status === 404) return []; // year not published
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      return (json.aggregations ?? []).filter(a => a.count > 0).map(a =>
        [state, year, LOAN_PURPOSES[a.loan_purposes] ?? a.loan_purposes, a.count, Math.round(a.sum)]);
    } catch (err) {
      if (attempt === 4) throw new Error(`HMDA ${state} ${year}: ${err.message}`);
      await new Promise(r => setTimeout(r, 1000 * attempt));
    }
  }
}

async function fetchHmda() {
  const jobs = STATES.flatMap(([code]) => HMDA_YEARS.map(y => [code, y]));
  const results = [];
  let next = 0;
  console.log(`fetching ${jobs.length} HMDA aggregations (4 at a time) ...`);
  const worker = async () => {
    while (next < jobs.length) {
      const [s, y] = jobs[next++];
      results.push(...await fetchHmdaOne(s, y));
    }
  };
  await Promise.all(Array.from({ length: 4 }, worker));
  const order = Object.values(LOAN_PURPOSES);
  results.sort((a, b) => a[0].localeCompare(b[0]) || a[1] - b[1] || order.indexOf(a[2]) - order.indexOf(b[2]));
  const years = [...new Set(results.map(r => r[1]))];
  const missing = HMDA_YEARS.filter(y => !years.includes(y));
  if (missing.length) console.warn(`HMDA: no data returned for ${missing.join(', ')}`);
  await writeCsv('hmda_state_originations.csv', ['state_code', 'year', 'loan_purpose', 'loans', 'dollar_volume'], results);
}

await mkdir(DATA, { recursive: true });
await writeCsv('states.csv', ['state_code', 'state_name', 'fips', 'region', 'division'], STATES);
await Promise.all([fetchHpi(), fetchHmda()]);
console.log('done');
