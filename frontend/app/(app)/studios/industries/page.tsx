'use client';

import { useEffect, useState } from 'react';
import { Building2, TrendingUp, FileText, Lightbulb } from 'lucide-react';
import { industryService, type IndustryOverview } from '@/services/studios/studiosService';

const industryIcons: Record<string, string> = {
  healthcare: '🏥',
  education: '🎓',
  banking: '🏦',
  retail: '🛒',
  agriculture: '🌾',
  manufacturing: '🏭',
  government: '🏛️',
  telecom: '📡',
  logistics: '🚚',
};

export default function IndustriesPage() {
  const [industries, setIndustries] = useState<string[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState<string | null>(null);
  const [overview, setOverview] = useState<IndustryOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadIndustries();
  }, []);

  async function loadIndustries() {
    try {
      const res = await industryService.list();
      setIndustries(res.industries || []);
    } catch {
      // Empty state
    } finally {
      setLoading(false);
    }
  }

  async function selectIndustry(industry: string) {
    setSelectedIndustry(industry);
    try {
      const data = await industryService.overview(industry);
      setOverview(data);
    } catch {
      setOverview(null);
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Industry Intelligence</h1>
        <p className="text-gray-600 mt-1">Industry-specific KPIs, templates, and decision recommendations</p>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading industries...</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Industries List */}
          <div className="lg:col-span-1">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Industries</h2>
            <div className="space-y-2">
              {industries.map((ind) => (
                <button
                  key={ind}
                  onClick={() => selectIndustry(ind)}
                  className={`w-full text-left p-4 rounded-xl border transition-colors capitalize ${
                    selectedIndustry === ind
                      ? 'border-teal-300 bg-teal-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{industryIcons[ind] || '📊'}</span>
                  <span className="font-medium text-gray-900">{ind}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Industry Overview */}
          <div className="lg:col-span-2">
            {overview ? (
              <div className="space-y-6">
                {/* KPIs */}
                <div className="bg-white rounded-2xl border border-gray-200 p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <TrendingUp size={20} className="text-teal-600" />
                    Key Performance Indicators ({overview.kpi_count})
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {overview.kpis.map((kpi: any) => (
                      <div key={kpi.kpi_code} className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                        <h4 className="font-semibold text-gray-900">{kpi.kpi_name}</h4>
                        <p className="text-sm text-gray-600 mt-1">{kpi.description}</p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                          <span>Target: {kpi.target}</span>
                          <span className="px-2 py-0.5 bg-teal-100 text-teal-700 rounded">{kpi.category}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Templates */}
                <div className="bg-white rounded-2xl border border-gray-200 p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <FileText size={20} className="text-teal-600" />
                    Templates ({overview.template_count})
                  </h2>
                  <div className="space-y-3">
                    {overview.templates.map((t: any, i: number) => (
                      <div key={i} className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                        <h4 className="font-semibold text-gray-900">{t.template_name}</h4>
                        <span className="text-xs px-2 py-1 bg-teal-100 text-teal-700 rounded mt-1 inline-block">
                          {t.template_type}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : selectedIndustry ? (
              <div className="flex flex-col items-center justify-center py-16 bg-gray-50 rounded-2xl">
                <Building2 size={40} className="text-gray-400 mb-3" />
                <p className="text-gray-500">Loading {selectedIndustry} intelligence...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 bg-gray-50 rounded-2xl">
                <Building2 size={40} className="text-gray-400 mb-3" />
                <p className="text-gray-500">Select an industry to view KPIs and templates</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
