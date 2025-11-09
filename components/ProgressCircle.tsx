
import React from 'react';

interface ProgressCircleProps {
  progress: number;
}

export const ProgressCircle: React.FC<ProgressCircleProps> = ({ progress }) => {
  const radius = 15.9155;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div className="relative w-32 h-32">
      <svg viewBox="0 0 36 36" className="w-full h-full">
        <path
          className="stroke-slate-200"
          strokeWidth="3.8"
          fill="none"
          d={`M18 2.0845 a ${radius} ${radius} 0 0 1 0 ${2 * radius} a ${radius} ${radius} 0 0 1 0 -${2 * radius}`}
        />
        <path
          className="stroke-blue-500 transition-all duration-700 ease-out"
          strokeWidth="3.8"
          strokeDasharray={`${circumference} ${circumference}`}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="none"
          d={`M18 2.0845 a ${radius} ${radius} 0 0 1 0 ${2 * radius} a ${radius} ${radius} 0 0 1 0 -${2 * radius}`}
        />
      </svg>
      <div className="absolute top-0 left-0 w-full h-full flex items-center justify-center">
        <span className="text-2xl font-bold text-blue-600">{Math.round(progress)}%</span>
      </div>
    </div>
  );
};
