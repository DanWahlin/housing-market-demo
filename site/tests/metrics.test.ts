import { describe, expect, it } from 'vitest';
import {
  changeBetween,
  latestQuarter,
  monthlyToQuarterly,
  pctChange,
  rankByYoy,
  topN,
  yoyChange,
  type QuarterPoint,
} from '../src/metrics';

const series: QuarterPoint[] = [
  { year: 2019, quarter: 4, value: 200 },
  { year: 2025, quarter: 1, value: 290 },
  { year: 2025, quarter: 2, value: 300 },
  { year: 2026, quarter: 1, value: 300 },
  { year: 2026, quarter: 2, value: 315 },
];

describe('pctChange', () => {
  it('computes percent change', () => {
    expect(pctChange(110, 100)).toBeCloseTo(10);
    expect(pctChange(90, 100)).toBeCloseTo(-10);
  });
  it('returns NaN for missing or zero base', () => {
    expect(pctChange(100, 0)).toBeNaN();
    expect(pctChange(NaN, 100)).toBeNaN();
  });
});

describe('yoyChange', () => {
  it('compares with the same quarter one year earlier', () => {
    expect(yoyChange(series, 2026, 2)).toBeCloseTo(5);
    expect(yoyChange(series, 2026, 1)).toBeCloseTo((300 / 290 - 1) * 100);
  });
  it('returns NaN when the prior year is missing', () => {
    expect(yoyChange(series, 2025, 2)).toBeNaN();
  });
});

describe('changeBetween', () => {
  it('computes change since 2019 Q4', () => {
    expect(changeBetween(series, { year: 2019, quarter: 4 }, { year: 2026, quarter: 2 })).toBeCloseTo(57.5);
  });
});

describe('latestQuarter', () => {
  it('finds the latest quarter', () => {
    expect(latestQuarter([...series].reverse())).toEqual({ year: 2026, quarter: 2 });
  });
});

describe('monthlyToQuarterly', () => {
  it('averages three months and drops incomplete quarters', () => {
    const q = monthlyToQuarterly([
      { year: 2026, month: 4, value: 100 },
      { year: 2026, month: 5, value: 110 },
      { year: 2026, month: 6, value: 120 },
      { year: 2026, month: 7, value: 130 },
    ]);
    expect(q).toEqual([{ year: 2026, quarter: 2, value: 110 }]);
  });
  it('gives U.S. YoY from monthly averages', () => {
    const months = [
      ...[1, 2, 3].map((m) => ({ year: 2025, month: m, value: 100 })),
      ...[1, 2, 3].map((m, i) => ({ year: 2026, month: m, value: 102 + i * 2 })),
    ];
    expect(yoyChange(monthlyToQuarterly(months), 2026, 1)).toBeCloseTo(4);
  });
});

describe('rankByYoy', () => {
  const items = [
    { id: 'a', name: 'Alpha', yoy: 1 },
    { id: 'b', name: 'Bravo', yoy: 5 },
    { id: 'c', name: 'Charlie', yoy: NaN },
    { id: 'd', name: 'Delta', yoy: -3 },
    { id: 'e', name: 'Echo', yoy: 5 },
  ];
  it('sorts largest first, breaks ties by name, drops NaN', () => {
    expect(rankByYoy(items).map((d) => d.id)).toEqual(['b', 'e', 'a', 'd']);
  });
  it('takes the top N', () => {
    expect(topN(items, 2).map((d) => d.id)).toEqual(['b', 'e']);
  });
  it('does not change the input array', () => {
    rankByYoy(items);
    expect(items[0].id).toBe('a');
  });
});
