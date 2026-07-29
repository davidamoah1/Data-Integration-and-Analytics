'use client';

import { useEffect, useState } from 'react';
import { FlaskConical, Plus, FileText, Lightbulb } from 'lucide-react';
import { researchService, type ResearchProject } from '@/services/studios/studiosService';

const statusColors: Record<string, string> = {
  design: 'bg-blue-100 text-blue-700',
  data_collection: 'bg-yellow-100 text-yellow-700',
  analysis: 'bg-purple-100 text-purple-700',
  interpretation: 'bg-orange-100 text-orange-700',
  complete: 'bg-green-100 text-green-700',
};

export default function ResearchPage() {
  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newProject, setNewProject] = useState({ title: '', research_question: '', industry: '' });
  const [designSuggestion, setDesignSuggestion] = useState<any>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    try {
      const res = await researchService.list();
      setProjects(res.projects || []);
    } catch {
      // Empty state
    } finally {
      setLoading(false);
    }
  }

  async function createProject() {
    if (!newProject.title.trim()) return;
    try {
      await researchService.create(newProject);
      setNewProject({ title: '', research_question: '', industry: '' });
      setShowCreate(false);
      loadProjects();
    } catch {
      // Error handled
    }
  }

  async function getDesignSuggestion() {
    if (!newProject.research_question.trim()) return;
    try {
      const suggestion = await researchService.suggestDesign(newProject.research_question, newProject.industry || undefined);
      setDesignSuggestion(suggestion);
    } catch {
      setDesignSuggestion(null);
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Research Studio</h1>
          <p className="text-gray-600 mt-1">Complete research environment with hypothesis testing and publication-ready output</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-pink-600 text-white rounded-lg hover:bg-pink-700 transition-colors"
        >
          <Plus size={18} /> New Project
        </button>
      </div>

      {showCreate && (
        <div className="mb-6 p-6 bg-pink-50 rounded-2xl border border-pink-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Create Research Project</h2>
          <div className="space-y-4">
            <input
              type="text"
              value={newProject.title}
              onChange={(e) => setNewProject({ ...newProject, title: e.target.value })}
              placeholder="Project title..."
              className="w-full px-4 py-2 border border-pink-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
            />
            <textarea
              value={newProject.research_question}
              onChange={(e) => setNewProject({ ...newProject, research_question: e.target.value })}
              placeholder="Research question (e.g., 'Does digital learning improve student outcomes?')"
              rows={3}
              className="w-full px-4 py-2 border border-pink-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
            />
            <input
              type="text"
              value={newProject.industry}
              onChange={(e) => setNewProject({ ...newProject, industry: e.target.value })}
              placeholder="Industry (optional)..."
              className="w-full px-4 py-2 border border-pink-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
            />
            <div className="flex gap-3">
              <button
                onClick={getDesignSuggestion}
                className="px-4 py-2 bg-pink-100 text-pink-700 rounded-lg hover:bg-pink-200 transition-colors flex items-center gap-2"
              >
                <Lightbulb size={18} /> Suggest Design
              </button>
              <button
                onClick={createProject}
                className="px-6 py-2 bg-pink-600 text-white rounded-lg hover:bg-pink-700 transition-colors"
              >
                Create Project
              </button>
            </div>
          </div>

          {designSuggestion && (
            <div className="mt-4 p-4 bg-white rounded-xl border border-pink-200">
              <h3 className="font-semibold text-gray-900 mb-2">Research Design Suggestion</h3>
              <div className="space-y-2 text-sm text-gray-700">
                <p><strong>Design:</strong> {designSuggestion.suggested_design}</p>
                <p><strong>Methodology:</strong> {designSuggestion.suggested_methodology}</p>
                <p><strong>Tests:</strong> {designSuggestion.suggested_tests?.join(', ')}</p>
                <p><strong>Sample size:</strong> {designSuggestion.sample_size_consideration}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Research Workflow */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        {['design', 'data_collection', 'analysis', 'interpretation', 'complete'].map((step) => (
          <div key={step} className="p-4 bg-white rounded-xl border border-gray-200 text-center">
            <FlaskConical size={20} className="mx-auto text-pink-600 mb-2" />
            <p className="text-sm font-medium text-gray-900 capitalize">{step.replace(/_/g, ' ')}</p>
          </div>
        ))}
      </div>

      {/* Projects */}
      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : projects.length === 0 ? (
        <div className="text-center py-16 bg-gray-50 rounded-2xl">
          <FlaskConical size={48} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">No research projects yet</h3>
          <p className="text-gray-500 mb-6">Start a research project to design studies, test hypotheses, and generate reports.</p>
          <button
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-2 px-6 py-3 bg-pink-600 text-white rounded-xl hover:bg-pink-700"
          >
            <Plus size={18} /> Start Research
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {projects.map((p) => (
            <div key={p.id} className="p-6 bg-white rounded-2xl border border-gray-200">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{p.title}</h3>
                  {p.research_question && (
                    <p className="text-gray-600 mt-1">{p.research_question}</p>
                  )}
                </div>
                <span className={`text-xs px-3 py-1 rounded-full ${statusColors[p.status] || 'bg-gray-100 text-gray-600'}`}>
                  {p.status.replace(/_/g, ' ')}
                </span>
              </div>
              {p.industry && (
                <span className="inline-block text-xs px-2 py-1 bg-pink-100 text-pink-700 rounded-full">
                  {p.industry}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
