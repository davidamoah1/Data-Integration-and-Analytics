'use client';

import Link from 'next/link';
import { ArrowRight, Sparkles, X } from 'lucide-react';
import { RECOMMENDATIONS, type SmartRecommendation } from '@/lib/workflows';
import { useState } from 'react';

interface SmartRecommendationsProps {
  trigger: string;
  onDismiss?: () => void;
}

export function SmartRecommendations({ trigger, onDismiss }: SmartRecommendationsProps) {
  const [dismissed, setDismissed] = useState(false);
  const recommendations = RECOMMENDATIONS[trigger] || [];

  if (dismissed || recommendations.length === 0) return null;

  const handleDismiss = () => {
    setDismissed(true);
    onDismiss?.();
  };

  return (
    <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-blue-600" />
          <h3 className="text-sm font-semibold text-blue-900">Recommended next steps</h3>
        </div>
        <button onClick={handleDismiss} className="text-blue-400 hover:text-blue-600">
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="mt-3 space-y-2">
        {recommendations.map((rec: SmartRecommendation, idx: number) => {
          const Icon = rec.icon;
          return (
            <Link
              key={idx}
              href={rec.href}
              className="group flex items-center gap-3 rounded-lg border border-blue-100 bg-white p-3 transition-all hover:border-blue-300 hover:shadow-sm"
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
                <Icon className="h-4 w-4" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-900 group-hover:text-blue-600">{rec.title}</p>
                <p className="text-xs text-slate-500">{rec.description}</p>
              </div>
              <span className="text-xs font-medium text-blue-600 group-hover:underline">
                {rec.actionLabel}
              </span>
              <ArrowRight className="h-4 w-4 text-blue-400 transition-transform group-hover:translate-x-1" />
            </Link>
          );
        })}
      </div>
    </div>
  );
}
