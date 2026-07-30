import type { Metadata } from 'next';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { CheckCircle2, AlertTriangle, Clock, Server } from 'lucide-react';

export const metadata: Metadata = {
  title: 'System Status — DataFlow',
  description: 'Real-time status of DataFlow services and infrastructure.',
};

const services = [
  { name: 'Web Application', status: 'operational', description: 'Dashboard, analytics, and reporting' },
  { name: 'API Services', status: 'operational', description: 'Authentication, data processing, and integrations' },
  { name: 'Data Import', status: 'operational', description: 'File uploads and database connectors' },
  { name: 'Report Generation', status: 'operational', description: 'PDF, PowerPoint, and Word exports' },
  { name: 'Smart Capture (OCR)', status: 'operational', description: 'Document scanning and text extraction' },
  { name: 'Scheduled Reports', status: 'operational', description: 'Automated recurring report delivery' },
];

const incidents = [
  {
    date: 'Jul 28, 2025',
    title: 'Scheduled maintenance completed',
    status: 'resolved',
    description: 'Database optimization completed. All services restored.',
  },
  {
    date: 'Jul 15, 2025',
    title: 'Brief API latency',
    status: 'resolved',
    description: 'Increased response times for analytics API. Root cause identified and fixed.',
  },
];

const statusConfig = {
  operational: { icon: CheckCircle2, color: 'text-green-500', bg: 'bg-green-50', border: 'border-green-200', label: 'Operational' },
  degraded: { icon: AlertTriangle, color: 'text-yellow-500', bg: 'bg-yellow-50', border: 'border-yellow-200', label: 'Degraded Performance' },
  down: { icon: AlertTriangle, color: 'text-red-500', bg: 'bg-red-50', border: 'border-red-200', label: 'Service Disruption' },
};

export default function SystemStatusPage() {
  const allOperational = services.every((s) => s.status === 'operational');

  return (
    <main className="min-h-screen bg-background">
      <Navbar />

      <section className="mx-auto max-w-3xl px-6 py-20">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">System Status</h1>
          <p className="mt-4 text-lg text-slate-600">Real-time status of all DataFlow services.</p>
        </div>

        {/* Overall Status */}
        <div className={`mt-12 rounded-2xl border-2 p-8 text-center ${
          allOperational ? 'border-green-200 bg-green-50' : 'border-yellow-200 bg-yellow-50'
        }`}>
          <div className={`mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full ${
            allOperational ? 'bg-green-100' : 'bg-yellow-100'
          }`}>
            <CheckCircle2 className={`h-8 w-8 ${allOperational ? 'text-green-600' : 'text-yellow-600'}`} />
          </div>
          <h2 className="text-2xl font-bold text-slate-900">
            {allOperational ? 'All Systems Operational' : 'Some Services Degraded'}
          </h2>
          <p className="mt-2 text-sm text-slate-600">Last updated: {new Date().toLocaleString()}</p>
        </div>

        {/* Services */}
        <div className="mt-12 space-y-3">
          <h2 className="text-lg font-semibold text-slate-900">Services</h2>
          {services.map((service) => {
            const config = statusConfig[service.status as keyof typeof statusConfig];
            const Icon = config.icon;
            return (
              <div key={service.name} className={`flex items-center justify-between rounded-lg border p-4 ${config.border} ${config.bg}`}>
                <div className="flex items-center gap-3">
                  <Server className="h-5 w-5 text-slate-400" />
                  <div>
                    <p className="font-medium text-slate-900">{service.name}</p>
                    <p className="text-xs text-slate-500">{service.description}</p>
                  </div>
                </div>
                <div className={`flex items-center gap-2 ${config.color}`}>
                  <Icon className="h-5 w-5" />
                  <span className="text-sm font-medium">{config.label}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Incident History */}
        <div className="mt-12 space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">Recent Incidents</h2>
          {incidents.map((incident, idx) => (
            <div key={idx} className="rounded-lg border border-slate-200 bg-white p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-slate-400" />
                  <span className="text-sm text-slate-500">{incident.date}</span>
                </div>
                <span className="rounded-full bg-green-100 px-3 py-0.5 text-xs font-medium text-green-700">
                  Resolved
                </span>
              </div>
              <h3 className="mt-2 font-medium text-slate-900">{incident.title}</h3>
              <p className="mt-1 text-sm text-slate-600">{incident.description}</p>
            </div>
          ))}
        </div>
      </section>

      <Footer />
    </main>
  );
}
