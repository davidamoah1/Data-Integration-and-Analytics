'use client';

import { useEffect, useState } from 'react';
import { Eye, BarChart3, LineChart, PieChart, ScatterChart, Map } from 'lucide-react';
import { visualizationService } from '@/services/studios/studiosService';

const chartIcons: Record<string, any> = {
  bar: BarChart3,
  horizontal_bar: BarChart3,
  line: LineChart,
  pie: PieChart,
  scatter: ScatterChart,
  choropleth: Map,
  histogram: BarChart3,
  box: BarChart3,
  treemap: BarChart3,
};

export default function VisualizationsPage() {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [intent, setIntent] = useState('');
  const [loading, setLoading] = useState(false);

  async function getRecommendation() {
    setLoading(true);
    try {
      // Sample data for demonstration
      const sampleData = [
        { month: 'Jan', sales: 100, region: 'North' },
        { month: 'Feb', sales: 150, region: 'South' },
        { month: 'Mar', sales: 200, region: 'East' },
        { month: 'Apr', sales: 180, region: 'West' },
      ];
      const res = await visualizationService.recommend(sampleData, undefined, intent || undefined);
      setRecommendations([res]);
    } catch {
      // Error handled
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Visualization Engine</h1>
        <p className="text-gray-600 mt-1">
          Intelligent chart selection — the system decides which chart explains your data best
        </p>
      </div>

      {/* Intent Input */}
      <div className="mb-8 p-6 bg-gradient-to-r from-cyan-50 to-blue-50 rounded-2xl border border-cyan-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">What do you want to see?</h2>
        <div className="flex flex-wrap gap-2 mb-4">
          {['trend', 'comparison', 'distribution', 'relationship', 'composition'].map((i) => (
            <button
              key={i}
              onClick={() => setIntent(i)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                intent === i
                  ? 'bg-cyan-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:border-cyan-300'
              }`}
            >
              {i}
            </button>
          ))}
        </div>
        <button
          onClick={getRecommendation}
          disabled={loading}
          className="px-6 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Analyzing...' : 'Get Recommendation'}
        </button>
      </div>

      {/* Chart Types */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
        {[
          { type: 'bar', label: 'Bar Chart' },
          { type: 'line', label: 'Line Chart' },
          { type: 'pie', label: 'Pie Chart' },
          { type: 'scatter', label: 'Scatter Plot' },
          { type: 'histogram', label: 'Histogram' },
          { type: 'choropleth', label: 'Geographic' },
        ].map((c) => {
          const Icon = chartIcons[c.type] || BarChart3;
          return (
            <div key={c.type} className="p-4 bg-white rounded-xl border border-gray-200 text-center">
              <Icon size={24} className="mx-auto text-cyan-600 mb-2" />
              <p className="text-sm font-medium text-gray-900">{c.label}</p>
            </div>
          );
        })}
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Recommendations</h2>
          {recommendations.map((rec: any, i: number) => (
            <div key={i} className="p-6 bg-white rounded-2xl border border-gray-200">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{rec.title}</h3>
                  <span className="text-xs px-2 py-1 bg-cyan-100 text-cyan-700 rounded-full">
                    {rec.chart_type}
                  </span>
                </div>
              </div>
              <p className="text-gray-700 mb-4">{rec.reasoning}</p>
              {rec.data_summary && (
                <div className="p-4 bg-gray-50 rounded-xl">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Data Summary</h4>
                  <pre className="text-sm text-gray-600">{JSON.stringify(rec.data_summary, null, 2)}</pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
