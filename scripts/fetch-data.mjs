// Downloads public housing data (FHFA HPI and CFPB HMDA) and writes CSV files to data/.
// Usage: node scripts/fetch-data.mjs   (Node.js 18+, no npm packages)
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const DATA_DIR = join(dirname(fileURLToPath(import.meta.url)), '..', 'data');
const HPI_URL = 'https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv';
const HMDA_URL = 'https://ffiec.cfpb.gov/v2/data-browser-api/view/aggregations';
const HMDA_YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
const LOAN_PURPOSES = { 1: 'Home purchase', 31: 'Refinance', 32: 'Cash-out refinance' };

// [code, name, fips, region, division]
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
const STATE_NAMES = new Map(STATES.map(([code, name]) => [code, name]));

// Minimal RFC 4180 parser: handles quoted fields with commas, quotes, and newlines.
function parseCsv(text) {
  const rows = [];
  let row = [], field = '', inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') inQuotes = false;
      else field += c;
    } else if (c === '"') inQuotes = true;
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(field); rows.push(row); row = []; field = '';
    } else field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  const [header, ...body] = rows.filter((r) => r.length > 1 || r[0] !== '');
  return body.map((r) => Object.fromEntries(header.map((h, i) => [h, r[i] ?? ''])));
}

const csvCell = (v) => (/[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));

async function writeCsv(name, columns, rows) {
  const lines = [columns.join(','), ...rows.map((r) => columns.map((c) => csvCell(r[c] ?? '')).join(','))];
  await writeFile(join(DATA_DIR, name), lines.join('\n') + '\n');
  console.log(`wrote data/${name} (${rows.length} rows)`);
}

const byKeys = (...keys) => (a, b) => {
  for (const k of keys) {
    const x = a[k], y = b[k];
    if (x !== y) return typeof x === 'number' ? x - y : String(x).localeCompare(String(y));
  }
  return 0;
};

async function fetchHpi() {
  console.log(`downloading ${HPI_URL}`);
  const res = await fetch(HPI_URL);
  if (!res.ok) throw new Error(`HPI download failed: HTTP ${res.status}`);
  const rows = parseCsv(await res.text()).filter(
    (r) => r.hpi_type === 'traditional' && r.hpi_flavor === 'purchase-only',
  );
  const pick = (frequency, level) => rows.filter((r) => r.frequency === frequency && r.level === level);
  const num = (v) => (v === '' ? '' : Number(v));

  const state = pick('quarterly', 'State')
    .filter((r) => STATE_NAMES.has(r.place_id))
    .map((r) => ({
      state_code: r.place_id, state_name: STATE_NAMES.get(r.place_id),
      year: +r.yr, quarter: +r.period, index_nsa: num(r.index_nsa), index_sa: num(r.index_sa),
    }))
    .sort(byKeys('state_code', 'year', 'quarter'));

  const metro = pick('quarterly', 'MSA')
    .map((r) => ({
      cbsa_code: r.place_id, metro_name: r.place_name,
      year: +r.yr, quarter: +r.period, index_nsa: num(r.index_nsa), index_sa: num(r.index_sa),
    }))
    .sort(byKeys('cbsa_code', 'year', 'quarter'));

  const division = pick('monthly', 'USA or Census Division')
    .map((r) => ({
      place_id: r.place_id, place_name: r.place_name,
      year: +r.yr, month: +r.period, index_nsa: num(r.index_nsa), index_sa: num(r.index_sa),
    }))
    .sort(byKeys('place_id', 'year', 'month'));

  await writeCsv('hpi_state_quarterly.csv', ['state_code', 'state_name', 'year', 'quarter', 'index_nsa', 'index_sa'], state);
  await writeCsv('hpi_metro_quarterly.csv', ['cbsa_code', 'metro_name', 'year', 'quarter', 'index_nsa', 'index_sa'], metro);
  await writeCsv('hpi_us_division_monthly.csv', ['place_id', 'place_name', 'year', 'month', 'index_nsa', 'index_sa'], division);
}

async function fetchHmdaOne(state, year, attempt = 1) {
  const url = `${HMDA_URL}?years=${year}&states=${state}&actions_taken=1&loan_purposes=${Object.keys(LOAN_PURPOSES).join(',')}`;
  try {
    // The API returns HTTP 403 for some User-Agent values.
    const res = await fetch(url, { headers: { 'User-Agent': 'curl/8.7.1', Accept: 'application/json' } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const { aggregations } = await res.json();
    return aggregations.map((a) => ({
      state_code: state, year, loan_purpose: LOAN_PURPOSES[a.loan_purposes],
      loans: a.count, dollar_volume: Math.round(a.sum),
    }));
  } catch (err) {
    if (attempt >= 4) throw new Error(`HMDA ${state} ${year} failed: ${err.message}`);
    await new Promise((r) => setTimeout(r, 1000 * attempt));
    return fetchHmdaOne(state, year, attempt + 1);
  }
}

async function fetchHmda() {
  const jobs = STATES.flatMap(([code]) => HMDA_YEARS.map((year) => [code, year]));
  console.log(`downloading HMDA aggregations (${jobs.length} requests, 4 at a time)`);
  const results = [];
  let next = 0;
  const worker = async () => {
    while (next < jobs.length) {
      const [state, year] = jobs[next++];
      results.push(...(await fetchHmdaOne(state, year)));
    }
  };
  await Promise.all(Array.from({ length: 4 }, worker));
  const purposeOrder = Object.values(LOAN_PURPOSES);
  results.sort((a, b) => byKeys('state_code', 'year')(a, b) || purposeOrder.indexOf(a.loan_purpose) - purposeOrder.indexOf(b.loan_purpose));
  await writeCsv('hmda_state_originations.csv', ['state_code', 'year', 'loan_purpose', 'loans', 'dollar_volume'], results);
}

await mkdir(DATA_DIR, { recursive: true });
await writeCsv('states.csv', ['state_code', 'state_name', 'fips', 'region', 'division'],
  STATES.map(([state_code, state_name, fips, region, division]) => ({ state_code, state_name, fips, region, division })));
await fetchHpi();
await fetchHmda();
console.log('done');
