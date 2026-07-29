'use client';

import { useEffect, useState } from 'react';
import { Brush, AlertTriangle, CheckCircle, XCircle, Play } from 'lucide-react';
import { cleaningService, type CleaningJob } from '@/services/studios/studiosService';

const severityColors: Record<string, string> = {
  high: 'bg-red-100 text-red-700 border-red-200',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  low: 'bg-green-100 text-green-700 border-green-200',
};

export default function DataCleaningPage() {
  const [jobs, setJobs] = useState<CleaningJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState<CleaningJob | null>(null);

  useEffect(() => {
    loadJobs();
  }, []);

  async function loadJobs() {
    try {
      const res = await cleaningService.list();
      setJobs(res.jobs || []);
    } catch {
      // Empty state
    } finally {
      setLoading(false);
    }
  }

  async function selectJob(id: number) {
    try {
      const job = await cleaningService.get(id);
      setSelectedJob(job);
    } catch {
      // Error handled
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Smart Data Preparation</h1>
        <p className="text-gray-600 mt-1">
          Automatically detect and fix data quality issues
        </p>
      </div>

      {/* Capabilities */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Missing Values', desc: 'Auto-detect and fill gaps' },
          { label: 'Duplicates', desc: 'Find and remove duplicates' },
          { label: 'Invalid Dates', desc: 'Fix date format issues' },
          { label: 'Outliers', desc: 'Flag extreme values' },
        ].map((c) => (
          <div key={c.label} className="p-4 bg-white rounded-xl border border-gray-200 text-center">
            <Brush size={24} className="mx-auto text-blue-600 mb-2" />
            <h3 className="font-semibold text-sm text-gray-900">{c.label}</h3>
            <p className="text-xs text-gray-500 mt-1">{c.desc}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Jobs List */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Cleaning Jobs</h2>
          {loading ? (
            <p className="text-gray-500">Loading...</p>
          ) : jobs.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-2xl">
              <Brush size={40} className="mx-auto text-gray-400 mb-3" />
              <p className="text-gray-500">No cleaning jobs yet. Upload a dataset to get started.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => (
                <button
                  key={job.id}
                  onClick={() => selectJob(job.id)}
                  className={`w-full text-left p-4 rounded-xl border transition-colors ${
                    selectedJob?.id === job.id
                      ? 'border-blue-300 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">Job #{job.id}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      job.status === 'applied' ? 'bg-green-100 text-green-700' :
                      job.status === 'awaiting_approval' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {job.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">Dataset #{job.dataset_id}</p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Job Details */}
        <div>
          {selectedJob ? (
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Job Details</h2>

              {selectedJob.issues_found && selectedJob.issues_found.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                    <AlertTriangle size={18} className="text-yellow-500" />
                    Issues Found ({selectedJob.issues_found.length})
                  </h3>
                  <div className="space-y-2">
                    {selectedJob.issues_found.map((issue: any, i: number) => (
                      <div
                        key={i}
                        className={`p-3 rounded-lg border text-sm ${severityColors[issue.severity] || severityColors.medium}`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{issue.issue_type.replace(/_/g, ' ')}</span>
                          <span className="text-xs">{issue.count} affected</span>
                        </div>
                        <p className="mt-1 text-xs opacity-80">{issue.suggestion}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedJob.transformations && selectedJob.transformations.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                    <CheckCircle size={18} className="text-green-500" />
                    Proposed Transformations
                  </h3>
                  <div className="space-y-2">
                    {selectedJob.transformations.map((t: any, i: number) => (
                      <div key={i} className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-sm">
                        <p className="font-medium text-gray-900">{t.action.replace(/_/g, ' ')}</p>
                        <p className="text-gray-600 mt-1">{t.reason}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedJob.summary && (
                <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
                  <h3 className="font-medium text-blue-900 mb-2">Summary</h3>
                  <p className="text-sm text-blue-700">
                    {selectedJob.summary.total_changes} changes applied.{' '}
                    {selectedJob.summary.original_shape?.[0]} rows processed.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 bg-gray-50 rounded-2xl">
              <Brush size={40} className="text-gray-400 mb-3" />
              <p className="text-gray-500">Select a job to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
