'use client';

import { useEffect, useState } from 'react';
import { Table2, Plus, Sparkles, Filter, ArrowUpDown, Grid3X3 } from 'lucide-react';
import { workspaceService, type DataWorkspace } from '@/services/studios/studiosService';

export default function DataWorkspacePage() {
  const [workspaces, setWorkspaces] = useState<DataWorkspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [aiFormula, setAiFormula] = useState('');
  const [aiSuggestion, setAiSuggestion] = useState<string | null>(null);

  useEffect(() => {
    loadWorkspaces();
  }, []);

  async function loadWorkspaces() {
    try {
      const res = await workspaceService.list();
      setWorkspaces(res.workspaces || []);
    } catch {
      // Empty state
    } finally {
      setLoading(false);
    }
  }

  async function createWorkspace() {
    if (!newName.trim()) return;
    try {
      await workspaceService.create({ name: newName });
      setNewName('');
      setShowCreate(false);
      loadWorkspaces();
    } catch {
      // Error handled silently
    }
  }

  async function getAISuggestion() {
    if (!aiFormula.trim()) return;
    try {
      const res = await workspaceService.aiSuggestFormula(aiFormula, []);
      const first = res.suggestions?.[0];
      if (first) {
        setAiSuggestion(`Formula: ${first.formula}\n\n${first.explanation}`);
      }
    } catch {
      setAiSuggestion('Unable to generate suggestion. Please try a different description.');
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Data Workspace</h1>
          <p className="text-gray-600 mt-1">Excel-like spreadsheet with smart formulas and editing</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={18} /> New Workspace
        </button>
      </div>

      {showCreate && (
        <div className="mb-6 p-4 bg-blue-50 rounded-xl border border-blue-200">
          <div className="flex gap-3">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Workspace name..."
              className="flex-1 px-4 py-2 border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={createWorkspace}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Create
            </button>
          </div>
        </div>
      )}

      {/* Smart Formula Assistant */}
      <div className="mb-8 p-6 bg-gradient-to-r from-purple-50 to-blue-50 rounded-2xl border border-purple-200">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles size={20} className="text-purple-600" />
          <h2 className="text-lg font-semibold text-gray-900">Smart Formula Assistant</h2>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Describe what you want to calculate and the assistant will suggest the formula.
        </p>
        <div className="flex gap-3">
          <input
            type="text"
            value={aiFormula}
            onChange={(e) => setAiFormula(e.target.value)}
            placeholder="e.g., 'Create a profit margin column' or 'Calculate growth rate'"
            className="flex-1 px-4 py-3 border border-purple-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 bg-white"
          />
          <button
            onClick={getAISuggestion}
            className="px-6 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors"
          >
            Suggest
          </button>
        </div>
        {aiSuggestion && (
          <div className="mt-4 p-4 bg-white rounded-xl border border-purple-200">
            <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono">{aiSuggestion}</pre>
          </div>
        )}
      </div>

      {/* Feature Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {[
          { icon: Filter, title: 'Filter & Sort', desc: 'Advanced filtering and multi-column sorting' },
          { icon: ArrowUpDown, title: 'Pivot Analysis', desc: 'Dynamic pivot tables and cross-tabulation' },
          { icon: Grid3X3, title: 'Version History', desc: 'Track all changes with full history' },
        ].map((f) => {
          const Icon = f.icon;
          return (
            <div key={f.title} className="p-4 bg-white rounded-xl border border-gray-200">
              <Icon size={24} className="text-blue-600 mb-2" />
              <h3 className="font-semibold text-gray-900">{f.title}</h3>
              <p className="text-sm text-gray-600 mt-1">{f.desc}</p>
            </div>
          );
        })}
      </div>

      {/* Workspaces List */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading workspaces...</div>
      ) : workspaces.length === 0 ? (
        <div className="text-center py-16 bg-gray-50 rounded-2xl">
          <Table2 size={48} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">No workspaces yet</h3>
          <p className="text-gray-500 mb-6">Create your first workspace to start working with data.</p>
          <button
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700"
          >
            <Plus size={18} /> Create Workspace
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {workspaces.map((ws) => (
            <div key={ws.id} className="flex items-center justify-between p-4 bg-white rounded-xl border border-gray-200 hover:border-gray-300 transition-colors">
              <div>
                <h3 className="font-semibold text-gray-900">{ws.name}</h3>
                {ws.description && <p className="text-sm text-gray-500 mt-1">{ws.description}</p>}
              </div>
              <div className="text-sm text-gray-400">
                {ws.created_at && new Date(ws.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
