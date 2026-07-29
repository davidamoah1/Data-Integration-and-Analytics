import type { Metadata } from 'next';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { HelpCircle, Database, BarChart3, FileText, Settings, Users, Zap } from 'lucide-react';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Help Center — DataFlow',
  description: 'Find answers, guides, and resources to get the most out of DataFlow.',
};

const categories = [
  {
    icon: Database,
    title: 'Getting Started',
    description: 'Upload your first dataset, navigate the dashboard, and run your first analysis.',
    articles: ['How to upload a dataset', 'Understanding the dashboard', 'Creating your first chart', 'Importing from external databases'],
  },
  {
    icon: BarChart3,
    title: 'Analytics & Dashboards',
    description: 'Build dashboards, create KPIs, and visualize your data effectively.',
    articles: ['Creating a dashboard', 'Adding widgets and charts', 'Using KPIs', 'Sharing dashboards with your team'],
  },
  {
    icon: FileText,
    title: 'Reports & Export',
    description: 'Generate professional reports and export to PDF, PowerPoint, and Word.',
    articles: ['Creating a report', 'Exporting to PDF', 'Exporting to PowerPoint', 'Scheduling recurring reports'],
  },
  {
    icon: Zap,
    title: 'Smart Capture',
    description: 'Scan paper records and extract data using OCR technology.',
    articles: ['Uploading paper documents', 'Reviewing extracted data', 'Correcting OCR errors', 'Batch processing'],
  },
  {
    icon: Users,
    title: 'Team & Collaboration',
    description: 'Invite team members, manage roles, and collaborate on projects.',
    articles: ['Inviting team members', 'Managing roles and permissions', 'Sharing projects', 'Activity logs'],
  },
  {
    icon: Settings,
    title: 'Account & Settings',
    description: 'Manage your account, security, and platform preferences.',
    articles: ['Changing your password', 'Enabling two-factor authentication', 'Managing API keys', 'Organization settings'],
  },
];

export default function HelpCenterPage() {
  return (
    <main className="min-h-screen bg-white">
      <Navbar />

      <section className="mx-auto max-w-5xl px-6 py-20">
        <div className="text-center">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100 text-blue-600">
            <HelpCircle className="h-8 w-8" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">Help Center</h1>
          <p className="mx-auto mt-4 max-w-xl text-lg text-slate-600">
            Browse our guides and articles to get the most out of DataFlow.
          </p>
        </div>

        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {categories.map((cat) => {
            const Icon = cat.icon;
            return (
              <div key={cat.title} className="rounded-xl border border-slate-200 bg-white p-6 transition-all hover:shadow-md">
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="font-semibold text-slate-900">{cat.title}</h3>
                <p className="mt-1 text-sm text-slate-600">{cat.description}</p>
                <ul className="mt-4 space-y-2">
                  {cat.articles.map((article) => (
                    <li key={article}>
                      <Link href="/contact" className="text-sm text-blue-600 hover:underline">
                        {article}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>

        <div className="mt-16 rounded-2xl bg-slate-50 p-8 text-center">
          <h2 className="text-xl font-bold text-slate-900">Still need help?</h2>
          <p className="mt-2 text-slate-600">Our support team is here to assist you.</p>
          <Link href="/contact" className="mt-4 inline-block rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700">
            Contact Support
          </Link>
        </div>
      </section>

      <Footer />
    </main>
  );
}
