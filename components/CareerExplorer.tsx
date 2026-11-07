import React, { useMemo, useState } from 'react';
import { motion } from 'motion/react';
import type { CareerCard, Profile } from '../types';
import { Icon } from './Icons';

interface Props {
  careers: CareerCard[];
  selectedId: string | null;
  profile: Profile;
  onProfile: (p: Profile) => void;
  onSelect: (careerId: string) => void;
  onCustom: (query: string) => void;
  busy: boolean;
}

const money = (n: number | null) => (n ? `$${Math.round(n / 1000)}k` : '');

export const CareerExplorer: React.FC<Props> = ({ careers, selectedId, profile, onProfile, onSelect, onCustom, busy }) => {
  const [q, setQ] = useState('');
  const [cluster, setCluster] = useState<string>('All');
  const clusters = useMemo(() => ['All', ...Array.from(new Set(careers.map(c => c.cluster)))], [careers]);

  const shown = careers.filter(c =>
    (cluster === 'All' || c.cluster === cluster) &&
    (!q || (c.title + ' ' + c.tagline).toLowerCase().includes(q.toLowerCase())));

  return (
    <section aria-label="Career explorer" className="flex h-full flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Where do you want to end up?</h2>
        <p className="text-sm text-slate-600">Pick a career, or type any job. We'll map every step from Miami Dade College.</p>
      </div>

      <form
        className="flex gap-2"
        onSubmit={e => { e.preventDefault(); if (q.trim()) onCustom(q.trim()); }}
      >
        <label className="relative flex-1">
          <span className="sr-only">Search or type a career</span>
          <Icon name="search" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="e.g. architect, chef, game designer"
            className="w-full rounded-xl border border-slate-300 bg-white py-2.5 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-amber-500 focus:outline-none"
          />
        </label>
        <button
          type="submit"
          disabled={!q.trim() || busy}
          className="rounded-xl bg-navy-900 px-4 text-sm font-medium text-white transition-colors hover:bg-navy-800 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Map it
        </button>
      </form>

      <div className="flex flex-wrap gap-1.5" role="tablist" aria-label="Filter by field">
        {clusters.map(c => (
          <button
            key={c}
            role="tab"
            aria-selected={cluster === c}
            onClick={() => setCluster(c)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              cluster === c ? 'bg-amber-500 text-navy-950' : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-100'}`}
          >
            {c}
          </button>
        ))}
      </div>

      <div className="scroll-thin -mr-2 grid flex-1 auto-rows-min grid-cols-1 gap-2.5 overflow-y-auto pr-2 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
        {shown.map((c, i) => {
          const active = c.id === selectedId;
          return (
            <motion.button
              key={c.id}
              layout
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(i * 0.03, 0.3) }}
              onClick={() => onSelect(c.id)}
              aria-pressed={active}
              className={`group flex items-start gap-3 rounded-2xl border p-3 text-left transition-colors ${
                active ? 'border-amber-500 bg-amber-50' : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'}`}
            >
              <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${active ? 'bg-amber-500 text-navy-950' : 'bg-navy-900 text-amber-400'}`}>
                <Icon name={c.icon} />
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex items-baseline justify-between gap-2">
                  <span className="truncate font-medium text-slate-900">{c.title}</span>
                  <span className="shrink-0 text-xs font-semibold text-emerald-700">{money(c.salary.median)}</span>
                </span>
                <span className="mt-0.5 line-clamp-2 block text-xs text-slate-600">{c.tagline}</span>
              </span>
            </motion.button>
          );
        })}
        {shown.length === 0 && (
          <p className="col-span-full rounded-xl bg-white p-4 text-sm text-slate-600 ring-1 ring-slate-200">
            No card for "{q}". Press <strong>Map it</strong> and the AI will build a custom roadmap.
          </p>
        )}
      </div>

      <details className="rounded-2xl bg-white p-3 ring-1 ring-slate-200">
        <summary className="cursor-pointer text-sm font-medium text-slate-800">Personalize my roadmap</summary>
        <div className="mt-3 grid grid-cols-3 gap-2">
          <label className="text-xs text-slate-600">
            Grade
            <select
              value={profile.grade}
              onChange={e => onProfile({ ...profile, grade: e.target.value })}
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900"
            >
              <option value="">-</option>
              {['9', '10', '11', '12', 'Graduate', 'Adult learner'].map(g => <option key={g}>{g}</option>)}
            </select>
          </label>
          <label className="col-span-2 text-xs text-slate-600">
            Interests (comma separated)
            <input
              value={profile.interests}
              onChange={e => onProfile({ ...profile, interests: e.target.value })}
              placeholder="robotics, drawing, soccer"
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 placeholder:text-slate-400"
            />
          </label>
        </div>
        <p className="mt-2 text-[11px] text-slate-500">Stays in your browser. Don't add names, phone numbers or IDs.</p>
      </details>
    </section>
  );
};
