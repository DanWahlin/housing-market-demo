import * as d3 from 'd3';

export interface StateData {
  code: string;
  name: string;
  fips: string;
  region: string;
  division: string;
  index: (number | null)[];
  yoy: (number | null)[];
  since2019: number | null;
}
export interface StatesFile {
  quarters: string[];
  states: StateData[];
}
export interface Summary {
  latest: { year: number; quarter: number; label: string };
  us: { yoy: number; since2019: number };
  fastest: { code: string; name: string; yoy: number };
  slowest: { code: string; name: string; yoy: number };
  metroCount: number;
}
export interface Metro {
  rank: number;
  cbsa: string;
  name: string;
  yoy: number;
}
export interface HmdaFile {
  years: number[];
  purposes: string[];
  states: Record<string, { year: number; loans: number[]; volume: number[] }[]>;
}

export const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export const fmtPct = (v: number | null | undefined, digits = 1) =>
  v == null || !Number.isFinite(v) ? 'n/a' : `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(digits)}%`;

export const fmtInt = d3.format(',');
export const fmtCompact = (v: number) => d3.format('.3~s')(v).replace('G', 'B');
export const fmtDollars = (v: number) => `$${fmtCompact(v)}`;

/** Diverging, color-blind-safe scale (purple = falling, orange = rising). */
export const YOY_LIMIT = 15;
export const yoyColor = d3
  .scaleDiverging<string>((t) => d3.interpolatePuOr(0.08 + t * 0.84))
  .domain([-YOY_LIMIT, 0, YOY_LIMIT])
  .clamp(true);

/** Okabe-Ito colors for loan purposes. */
export const purposeColors = ['#E69F00', '#56B4E9', '#009E73'];

export async function loadJson<T>(name: string): Promise<T> {
  const res = await fetch(`${import.meta.env.BASE_URL}data/${name}`);
  if (!res.ok) throw new Error(`Could not load ${name}`);
  return res.json() as Promise<T>;
}

export function onResize(el: Element, cb: () => void) {
  let last = 0;
  new ResizeObserver(() => {
    const w = Math.round(el.clientWidth);
    if (w !== last) {
      last = w;
      cb();
    }
  }).observe(el);
}
