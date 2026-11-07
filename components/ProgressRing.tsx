import React from 'react';
import { motion } from 'motion/react';

export const ProgressRing: React.FC<{ value: number; size?: number; label?: string }> = ({ value, size = 76, label = 'complete' }) => {
  const r = (size - 10) / 2;
  const c = 2 * Math.PI * r;
  const v = Math.max(0, Math.min(100, value));
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }} role="img" aria-label={`${v}% ${label}`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="currentColor" strokeWidth="7" fill="none" className="text-white/15" />
        <motion.circle
          cx={size / 2} cy={size / 2} r={r} strokeWidth="7" fill="none" strokeLinecap="round"
          stroke="#f59e0b" strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c - (v / 100) * c }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center leading-tight">
        <div>
          <div className="text-lg font-bold text-white">{v}%</div>
          <div className="text-[10px] uppercase tracking-wide text-slate-300">{label}</div>
        </div>
      </div>
    </div>
  );
};
