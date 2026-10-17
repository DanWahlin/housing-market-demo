import { describe, it, expect } from 'vitest';
import { qKey, qLabel, yoy, change, monthlyToQuarterly, rank, pct } from './math.ts';

describe('quarter keys', () => {
  it('puts the same quarter one year earlier 4 keys back', () => {
    expect(qKey(2026, 2) - qKey(2025, 2)).toBe(4);
    expect(qLabel(qKey(2019, 4))).toBe('2019 Q4');
  });
});

describe('yoy', () => {
  const s = new Map([[qKey(2025, 2), 200], [qKey(2026, 1), 205], [qKey(2026, 2), 210]]);
  it('divides by the same quarter one year earlier', () => {
    expect(yoy(s, qKey(2026, 2))).toBeCloseTo(0.05);
  });
  it('returns null when the earlier quarter is missing', () => {
    expect(yoy(s, qKey(2026, 1))).toBeNull();
  });
  it('computes change since a base quarter', () => {
    const t = new Map([[qKey(2019, 4), 100], [qKey(2026, 2), 150]]);
    expect(change(t, qKey(2026, 2), qKey(2019, 4))).toBeCloseTo(0.5);
  });
});

describe('monthlyToQuarterly', () => {
  it('averages 3 months and drops incomplete quarters', () => {
    const q = monthlyToQuarterly([
      { year: 2026, month: 4, value: 100 },
      { year: 2026, month: 5, value: 110 },
      { year: 2026, month: 6, value: 120 },
      { year: 2026, month: 7, value: 130 },
    ]);
    expect(q.get(qKey(2026, 2))).toBeCloseTo(110);
    expect(q.has(qKey(2026, 3))).toBe(false);
  });
});

describe('rank', () => {
  const items = [{ id: 'a', v: 0.02 }, { id: 'b', v: -0.01 }, { id: 'c', v: 0.07 }, { id: 'd', v: null }];
  it('sorts highest first, removes nulls, and limits to n', () => {
    expect(rank(items, (d) => d.v, 2).map((d) => d.id)).toEqual(['c', 'a']);
  });
  it('sorts lowest first when asked', () => {
    expect(rank(items, (d) => d.v, Infinity, 'asc').map((d) => d.id)).toEqual(['b', 'a', 'c']);
  });
});

describe('pct', () => {
  it('formats signed percents', () => {
    expect(pct(0.0523)).toBe('+5.2%');
    expect(pct(-0.012)).toBe('-1.2%');
    expect(pct(null)).toBe('n/a');
  });
});
