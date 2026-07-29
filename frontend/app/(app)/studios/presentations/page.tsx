'use client';

import { useEffect, useState } from 'react';
import { Presentation, Plus, FileText, LayoutTemplate } from 'lucide-react';
import { presentationService, type Presentation as PresentationType } from '@/services/studios/studiosService';

const templates = [
  { id: 'executive', name: 'Executive', desc: 'High-level summary for C-suite' },
  { id: 'analytical', name: 'Analytical', desc: 'Detailed findings for analysts' },
  { id: 'research', name: 'Research', desc: 'Academic with methodology' },
  { id: 'pitch', name: 'Pitch', desc: 'Persuasive for stakeholders' },
];

export default function PresentationsPage() {
  const [presentations, setPresentations] = useState<PresentationType[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<PresentationType | null>(null);

  useEffect(() => {
    loadPresentations();
  }, []);

  async function loadPresentations() {
    try {
      const res = await presentationService.list();
      setPresentations(res.presentations || []);
    } catch {
      // Empty state
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Presentation Studio</h1>
          <p className="text-gray-600 mt-1">Turn your analysis into professional presentations automatically</p>
        </div>
      </div>

      {/* Templates */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {templates.map((t) => (
          <div key={t.id} className="p-4 bg-white rounded-xl border border-gray-200 text-center hover:border-indigo-300 transition-colors cursor-pointer">
            <LayoutTemplate size={24} className="mx-auto text-indigo-600 mb-2" />
            <h3 className="font-semibold text-sm text-gray-900">{t.name}</h3>
            <p className="text-xs text-gray-500 mt-1">{t.desc}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Presentations List */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Presentations</h2>
          {loading ? (
            <p className="text-gray-500">Loading...</p>
          ) : presentations.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-2xl">
              <Presentation size={40} className="mx-auto text-gray-400 mb-3" />
              <p className="text-gray-500">No presentations yet. Run an analysis to generate one.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {presentations.map((p) => (
                <button
                  key={p.id}
                  onClick={async () => {
                    try {
                      const full = await presentationService.get(p.id);
                      setSelected(full);
                    } catch { /* handled */ }
                  }}
                  className={`w-full text-left p-4 rounded-xl border transition-colors ${
                    selected?.id === p.id
                      ? 'border-indigo-300 bg-indigo-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">{p.title}</span>
                    <span className="text-xs px-2 py-1 bg-indigo-100 text-indigo-700 rounded-full">
                      {p.template}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Presentation Details */}
        <div>
          {selected ? (
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">{selected.title}</h2>
              {selected.slides && selected.slides.length > 0 ? (
                <div className="space-y-4">
                  {selected.slides.map((slide: any) => (
                    <div key={slide.slide_number} className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-bold text-indigo-600">#{slide.slide_number}</span>
                        <span className="text-xs px-2 py-0.5 bg-gray-200 text-gray-600 rounded">{slide.layout}</span>
                      </div>
                      <h4 className="font-semibold text-gray-900">{slide.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{slide.content}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No slides generated yet.</p>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 bg-gray-50 rounded-2xl">
              <FileText size={40} className="text-gray-400 mb-3" />
              <p className="text-gray-500">Select a presentation to view slides</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
