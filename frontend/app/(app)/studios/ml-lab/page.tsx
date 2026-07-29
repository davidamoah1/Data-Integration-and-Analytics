'use client';

import { useEffect, useState } from 'react';
import { Brain, Plus, Trophy, Lightbulb, TrendingUp } from 'lucide-react';
import { mlLabService, type MLExperiment } from '@/services/studios/studiosService';

const taskTypes = [
  { id: 'classification', name: 'Classification', desc: 'Predict categories' },
  { id: 'regression', name: 'Regression', desc: 'Predict numbers' },
  { id: 'clustering', name: 'Clustering', desc: 'Group similar items' },
  { id: 'forecasting', name: 'Forecasting', desc: 'Predict future values' },
  { id: 'anomaly_detection', name: 'Anomaly Detection', desc: 'Find unusual patterns' },
];

export default function MLLabPage() {
  const [experiments, setExperiments] = useState<MLExperiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<MLExperiment | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newExp, setNewExp] = useState({ name: '', task_type: 'classification' });

  useEffect(() => {
    loadExperiments();
  }, []);

  async function loadExperiments() {
    try {
      const res = await mlLabService.list();
      setExperiments(res.experiments || []);
    } catch {
      // Empty state
    } finally {
      setLoading(false);
    }
  }

  async function createExperiment() {
    if (!newExp.name.trim()) return;
    try {
      await mlLabService.create({
        dataset_id: 1,
        name: newExp.name,
        task_type: newExp.task_type,
      });
      setNewExp({ name: '', task_type: 'classification' });
      setShowCreate(false);
      loadExperiments();
    } catch {
      // Error handled
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">ML Lab</h1>
          <p className="text-gray-600 mt-1">No-code machine learning with model comparison and clear explanations</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
        >
          <Plus size={18} /> New Experiment
        </button>
      </div>

      {showCreate && (
        <div className="mb-6 p-4 bg-orange-50 rounded-xl border border-orange-200">
          <div className="flex flex-col gap-3">
            <input
              type="text"
              value={newExp.name}
              onChange={(e) => setNewExp({ ...newExp, name: e.target.value })}
              placeholder="Experiment name..."
              className="px-4 py-2 border border-orange-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
            />
            <select
              value={newExp.task_type}
              onChange={(e) => setNewExp({ ...newExp, task_type: e.target.value })}
              className="px-4 py-2 border border-orange-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
            >
              {taskTypes.map((t) => (
                <option key={t.id} value={t.id}>{t.name} — {t.desc}</option>
              ))}
            </select>
            <button
              onClick={createExperiment}
              className="px-6 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
            >
              Create Experiment
            </button>
          </div>
        </div>
      )}

      {/* Task Types */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        {taskTypes.map((t) => (
          <div key={t.id} className="p-4 bg-white rounded-xl border border-gray-200 text-center hover:border-orange-300 transition-colors cursor-pointer">
            <Brain size={24} className="mx-auto text-orange-600 mb-2" />
            <h3 className="font-semibold text-sm text-gray-900">{t.name}</h3>
            <p className="text-xs text-gray-500 mt-1">{t.desc}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Experiments List */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Experiments</h2>
          {loading ? (
            <p className="text-gray-500">Loading...</p>
          ) : experiments.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-2xl">
              <Brain size={40} className="mx-auto text-gray-400 mb-3" />
              <p className="text-gray-500">No experiments yet. Create your first ML experiment.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {experiments.map((exp) => (
                <button
                  key={exp.id}
                  onClick={async () => {
                    try {
                      const full = await mlLabService.get(exp.id);
                      setSelected(full);
                    } catch { /* handled */ }
                  }}
                  className={`w-full text-left p-4 rounded-xl border transition-colors ${
                    selected?.id === exp.id
                      ? 'border-orange-300 bg-orange-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">{exp.name}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      exp.status === 'completed' ? 'bg-green-100 text-green-700' :
                      exp.status === 'training' ? 'bg-blue-100 text-blue-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {exp.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{exp.task_type} · {exp.algorithm || 'auto'}</p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Experiment Details */}
        <div>
          {selected ? (
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">{selected.name}</h2>

              {selected.model_summary && (
                <div className="mb-6 p-4 bg-orange-50 rounded-xl border border-orange-200">
                  <h3 className="font-medium text-orange-900 mb-2 flex items-center gap-2">
                    <Lightbulb size={18} /> Summary
                  </h3>
                  <p className="text-sm text-orange-800 leading-relaxed">{selected.model_summary}</p>
                </div>
              )}

              {selected.metrics && (
                <div className="mb-6">
                  <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                    <Trophy size={18} className="text-yellow-500" /> Metrics
                  </h3>
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(selected.metrics).map(([key, value]) => (
                      <div key={key} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                        <p className="text-xs text-gray-500 uppercase">{key.replace(/_/g, ' ')}</p>
                        <p className="text-lg font-semibold text-gray-900">
                          {typeof value === 'number' ? (value * 100).toFixed(1) + '%' : String(value)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selected.feature_importance && Object.keys(selected.feature_importance).length > 0 && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                    <TrendingUp size={18} className="text-blue-500" /> Feature Importance
                  </h3>
                  <div className="space-y-2">
                    {Object.entries(selected.feature_importance)
                      .sort(([, a], [, b]) => (b as number) - (a as number))
                      .slice(0, 5)
                      .map(([feature, importance]) => (
                        <div key={feature} className="flex items-center gap-3">
                          <span className="text-sm text-gray-700 w-32 truncate">{feature}</span>
                          <div className="flex-1 h-4 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-500 rounded-full"
                              style={{ width: `${(importance as number) * 100}%` }}
                            />
                          </div>
                          <span className="text-sm text-gray-600 w-12 text-right">
                            {((importance as number) * 100).toFixed(0)}%
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 bg-gray-50 rounded-2xl">
              <Brain size={40} className="text-gray-400 mb-3" />
              <p className="text-gray-500">Select an experiment to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
