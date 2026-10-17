export interface QuarterPoint {
  year: number;
  quarter: number;
  value: number;
}

export interface MonthPoint {
  year: number;
  month: number;
  value: number;
}

export interface Ranked {
  id: string;
  name: string;
  yoy: number;
}

export const qKey = (year: number, quarter: number) => year * 4 + (quarter - 1);
export const qLabel = (year: number, quarter: number) => `${year} Q${quarter}`;

/** Percent change from `before` to `after`. */
export function pctChange(after: number, before: number): number {
  if (!Number.isFinite(after) || !Number.isFinite(before) || before === 0) return NaN;
  return ((after - before) / before) * 100;
}

/** Latest quarter present in a quarterly series (all rows count as complete quarters). */
export function latestQuarter(points: { year: number; quarter: number }[]): { year: number; quarter: number } {
  if (points.length === 0) throw new Error('No data');
  let best = points[0];
  for (const p of points) if (qKey(p.year, p.quarter) > qKey(best.year, best.quarter)) best = p;
  return { year: best.year, quarter: best.quarter };
}

export function valueAt(series: QuarterPoint[], year: number, quarter: number): number {
  const p = series.find((s) => s.year === year && s.quarter === quarter);
  return p ? p.value : NaN;
}

/** Year-over-year percent change for a quarterly series at the given quarter. */
export function yoyChange(series: QuarterPoint[], year: number, quarter: number): number {
  return pctChange(valueAt(series, year, quarter), valueAt(series, year - 1, quarter));
}

/** Percent change between two quarters of a quarterly series. */
export function changeBetween(
  series: QuarterPoint[],
  from: { year: number; quarter: number },
  to: { year: number; quarter: number },
): number {
  return pctChange(valueAt(series, to.year, to.quarter), valueAt(series, from.year, from.quarter));
}

/** Average monthly values into quarters. Only quarters with all three months are kept. */
export function monthlyToQuarterly(points: MonthPoint[]): QuarterPoint[] {
  const groups = new Map<number, { year: number; quarter: number; values: number[] }>();
  for (const p of points) {
    const quarter = Math.ceil(p.month / 3);
    const k = qKey(p.year, quarter);
    const g = groups.get(k) ?? { year: p.year, quarter, values: [] };
    g.values.push(p.value);
    groups.set(k, g);
  }
  return [...groups.entries()]
    .sort((a, b) => a[0] - b[0])
    .filter(([, g]) => g.values.length === 3)
    .map(([, g]) => ({ year: g.year, quarter: g.quarter, value: g.values.reduce((s, v) => s + v, 0) / 3 }));
}

/** Sort by year-over-year change, largest first. Ties sort by name. NaN values are dropped. */
export function rankByYoy<T extends Ranked>(items: T[]): T[] {
  return items
    .filter((d) => Number.isFinite(d.yoy))
    .sort((a, b) => b.yoy - a.yoy || a.name.localeCompare(b.name));
}

export function topN<T extends Ranked>(items: T[], n: number): T[] {
  return rankByYoy(items).slice(0, n);
}
