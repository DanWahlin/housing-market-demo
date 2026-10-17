// Download public U.S. housing data into data/.
//
// Sources (public U.S. government data, no API key):
// - FHFA House Price Index: https://www.fhfa.gov/data/hpi/datasets
// - CFPB HMDA Data Browser API: https://ffiec.cfpb.gov/documentation/api/data-browser/
//
// Run: node scripts/fetch-data.mjs   (Node.js 18 or later)

import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const DATA = join(dirname(fileURLToPath(import.meta.url)), '..', 'data');
const HPI_URL = 'https://www.fhfa.gov/hpi/download/monthly/hpi_master.csv';
const hmdaUrl = (year, state) =>
  `https://ffiec.cfpb.gov/v2/data-browser-api/view/aggregations?years=${year}&states=${state}&actions_taken=1&loan_purposes=1,31,32`;
const HMDA_YEARS = Array.from({ length: 8 }, (_, i) => 2018 + i);
const PURPOSES = { 1: 'Home purchase', 31: 'Refinance', 32: 'Cash-out refinance' };

// code, name, FIPS, census region, census division
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

// The HMDA API rejects some user agents, so identify as curl.
async function get(url, tries = 4) {
  for (let i = 1; ; i++) {
    try {
      const res = await fetch(url, { headers: { 'User-Agent': 'curl/8.7.1' } });
      if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
      return await res.text();
    } catch (err) {
      if (i === tries) throw err;
      await new Promise((r) => setTimeout(r, 2000 * i));
    }
  }
}

// Minimal CSV parser that handles quoted fields with commas.
function parseCsv(text) {
  const rows = [];
  let row = [], field = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n') { row.push(field.replace(/\r$/, '')); rows.push(row); row = []; field = ''; }
    else field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  const [header, ...body] = rows;
  return body.filter((r) => r.length === header.length).map((r) => Object.fromEntries(header.map((h, i) => [h, r[i]])));
}

const cell = (v) => (/[",\r\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));

async function write(name, header, rows) {
  const lines = [header, ...rows].map((r) => r.map(cell).join(','));
  await writeFile(join(DATA, name), lines.join('\r\n') + '\r\n');
  console.log(`data/${name}: ${rows.length.toLocaleString('en-US')} rows`);
}

// Index values have two decimals. Whole numbers keep one decimal (100.0).
function num(v) {
  if (v === '' || v == null) return '';
  const n = Math.round(parseFloat(v) * 100) / 100;
  return Number.isInteger(n) ? n.toFixed(1) : String(n);
}

async function fetchHpi() {
  const names = Object.fromEntries(STATES.map((s) => [s[0], s[1]]));
  const state = [], metro = [], us = [];
  for (const r of parseCsv(await get(HPI_URL))) {
    const key = [r.hpi_type, r.hpi_flavor, r.frequency, r.level].join('|');
    const values = [r.yr, r.period, num(r.index_nsa), num(r.index_sa)];
    if (key === 'traditional|purchase-only|quarterly|State' && names[r.place_id]) state.push([r.place_id, names[r.place_id], ...values]);
    else if (key === 'traditional|purchase-only|quarterly|MSA') metro.push([r.place_id, r.place_name, ...values]);
    else if (key === 'traditional|purchase-only|monthly|USA or Census Division') us.push([r.place_id, r.place_name, ...values]);
  }
  await write('hpi_state_quarterly.csv', ['state_code', 'state_name', 'year', 'quarter', 'index_nsa', 'index_sa'], state);
  await write('hpi_metro_quarterly.csv', ['cbsa_code', 'metro_name', 'year', 'quarter', 'index_nsa', 'index_sa'], metro);
  await write('hpi_us_division_monthly.csv', ['place_id', 'place_name', 'year', 'month', 'index_nsa', 'index_sa'], us);
}

async function fetchHmda() {
  const jobs = STATES.flatMap(([code]) => HMDA_YEARS.map((year) => [code, year]));
  const rows = [];
  // Four requests at a time keeps the API from rate limiting us.
  for (let i = 0; i < jobs.length; i += 4) {
    const results = await Promise.all(jobs.slice(i, i + 4).map(async ([code, year]) => {
      const data = JSON.parse(await get(hmdaUrl(year, code)));
      return data.aggregations.map((a) => [code, year, PURPOSES[a.loan_purposes], a.count, Math.trunc(a.sum)]);
    }));
    rows.push(...results.flat());
  }
  const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
  rows.sort((a, b) => cmp(a[0], b[0]) || a[1] - b[1] || cmp(a[2], b[2]));
  await write('hmda_state_originations.csv', ['state_code', 'year', 'loan_purpose', 'loans', 'dollar_volume'], rows);
}

await mkdir(DATA, { recursive: true });
await write('states.csv', ['state_code', 'state_name', 'fips', 'region', 'division'], STATES);
await fetchHpi();
await fetchHmda();
