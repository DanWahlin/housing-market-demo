/** Quarter key: a single integer so that "one year earlier" is key - 4. */
export const qKey = (year: number, quarter: number): number => year * 4 + (quarter - 1);
export const qLabel = (key: number): string => `${Math.floor(key / 4)} Q${(key % 4) + 1}`;

export type Series = Map<number, number>;

/** Change between two keys of a series as a fraction (0.05 = +5%). Null when data is missing. */
export function change(series: Series, key: number, baseKey: number): number | null {
  const now = series.get(key);
  const base = series.get(baseKey);
  if (now == null || base == null || base === 0) return null;
  return now / base - 1;
}

/** Year-over-year change: index ÷ same quarter one year earlier − 1. */
export const yoy = (series: Series, key: number): number | null => change(series, key, key - 4);

/** Quarterly series from monthly rows: mean of the 3 months. Only complete quarters are kept. */
export function monthlyToQuarterly(rows: { year: number; month: number; value: number }[]): Series {
  const groups = new Map<number, number[]>();
  for (const r of rows) {
    const key = qKey(r.year, Math.ceil(r.month / 3));
    const list = groups.get(key) ?? [];
    list.push(r.value);
    groups.set(key, list);
  }
  const out: Series = new Map();
  for (const [key, values] of groups) {
    if (values.length === 3) out.set(key, values.reduce((a, b) => a + b, 0) / 3);
  }
  return out;
}

/** Items sorted by value (highest first by default), nulls removed, limited to n. */
export function rank<T>(
  items: T[],
  value: (item: T) => number | null,
  n = Infinity,
  order: 'desc' | 'asc' = 'desc',
): (T & { value: number })[] {
  const sign = order === 'desc' ? -1 : 1;
  return items
    .map((item) => ({ ...item, value: value(item) }))
    .filter((d): d is T & { value: number } => d.value != null && Number.isFinite(d.value))
    .sort((a, b) => sign * (a.value - b.value))
    .slice(0, n);
}

/** Fraction to signed percent text, for example 0.0523 -> "+5.2%". */
export function pct(v: number | null, digits = 1): string {
  if (v == null) return 'n/a';
  const s = (v * 100).toFixed(digits);
  return v > 0 ? `+${s}%` : `${s}%`;
}
