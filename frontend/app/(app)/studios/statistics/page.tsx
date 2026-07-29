'use client';

import { useEffect, useState } from 'react';
import { BarChart3, FlaskConical, TrendingUp, PieChart, Activity } from 'lucide-react';
import { statisticsService, type StatisticalAnalysis } from '@/services/studios/studiosService';

const analysisTypes = [
  { id: 'descriptive', name: 'Descriptive', desc: 'Mean, median, mode, std dev', icon: BarChart3 },
  { id: 'ttest', name: 'T-Test', desc: 'Compare group means', icon: TrendingUp },
  { id: 'anova', name: 'ANOVA', desc: 'Compare 3+ groups', icon: Activity },
  { id: 'chi_square', name: 'Chi-Square', desc: 'Test independence', icon: PieChart },
  { id: 'correlation', name: 'Correlation', desc: 'Measure relationships', icon: TrendingUp },
  { id: 'regression', name: 'Regression', desc: 'Predict outcomes', icon: FlaskConical },
];

export default function StatisticsPage() {
  const [analyses, setAnalyses] = useState<StatisticalAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<StatisticalAnalysis | null>(null);

  useEffect(() => {
    loadAnalyses();
  }, []);

  async function loadAnalyses() {
    try {
      const res = await statisticsService.list();
      setAnalyses(res.analyses || []);
    } catch {
      // Empty state
    } finally {
      setLoading(false);
    }
  }

  async function selectAnalysis(id: number) {
    try {
      const analysis = await statisticsService.get(id);
      setSelected(analysis);
    } catch {
      // Error handled
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Statistics Engine</h1>
        <p className="text-gray-600 mt-1">
          Professional statistical analysis with full interpretation and assumption checking
        </p>
      </div>

      {/* Analysis Types */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {analysisTypes.map((t) => {
          const Icon = t.icon;
          return (
            <div key={t.id} className="p-4 bg-white rounded-xl border border-gray-200 text-center hover:border-purple-300 transition-colors cursor-pointer">
              <Icon size={24} className="mx-auto text-purple-600 mb-2" />
              <h3 className="font-semibold text-sm text-gray-900">{t.name}</h3>
              <p className="text-xs text-gray-500 mt-1">{t.desc}</p>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Analyses List */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Analyses</h2>
          {loading ? (
            <p className="text-gray-500">Loading...</p>
          ) : analyses.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-2xl">
              <BarChart3 size={40} className="mx-auto text-gray-400 mb-3" />
              <p className="text-gray-500">No analyses yet. Upload data and run a statistical test.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {analyses.map((a) => (
                <button
                  key={a.id}
                  onClick={() => selectAnalysis(a.id)}
                  className={`w-full text-left p-4 rounded-xl border transition-colors ${
                    selected?.id === a.id
                      ? 'border-purple-300 bg-purple-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">{a.test_name || a.analysis_type}</span>
                    <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
                      {a.analysis_type}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Analysis Details */}
        <div>
          {selected ? (
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">{selected.test_name}</h2>

              {selected.interpretation && (
                <div className="mb-6 p-4 bg-purple-50 rounded-xl border border-purple-200">
                  <h3 className="font-medium text-purple-900 mb-2">Interpretation</h3>
                  <p className="text-sm text-purple-800 leading-relaxed">{selected.interpretation}</p>
                </div>
              )}

              {selected.results && (
                <div className="mb-6">
                  <h3 className="font-medium text-gray-900 mb-3">Results</h3>
                  <div className="bg-gray-50 rounded-xl p-4 overflow-auto">
                    <pre className="text-sm text-gray-800">{JSON.stringify(selected.results, null, 2)}</pre>
                  </div>
                </div>
              )}

              {selected.assumptions && selected.assumptions.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-medium text-gray-900 mb-3">Assumptions</h3>
                  <ul className="space-y-2">
                    {selected.assumptions.map((a, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                        <span className="text-purple-500 mt-0.5">•</span>
                        {a}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {selected.limitations && (
                <div className="p-4 bg-yellow-50 rounded-xl border border-yellow-200">
                  <h3 className="font-medium text-yellow-900 mb-2">Limitations</h3>
                  <p className="text-sm text-yellow-800">{selected.limitations}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 bg-gray-50 rounded-2xl">
              <BarChart3 size={40} className="text-gray-400 mb-3" />
              <p className="text-gray-500">Select an analysis to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
