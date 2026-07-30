'use client';

import Link from 'next/link';
import {
  Table2, Brush, BarChart3, Brain, FlaskConical, Presentation,
  Building2, Eye, BotMessageSquare, Users,
} from 'lucide-react';

const studios = [
  {
    href: '/studios/workspace',
    icon: Table2,
    title: 'Data Workspace',
    description: 'Excel-like spreadsheet with smart formulas and editing',
    color: 'bg-emerald-500',
  },
  {
    href: '/studios/cleaning',
    icon: Brush,
    title: 'Smart Data Preparation',
    description: 'Automated detection and transformation of data issues',
    color: 'bg-blue-500',
  },
  {
    href: '/studios/statistics',
    icon: BarChart3,
    title: 'Statistics Engine',
    description: 'Professional statistical tests with full interpretation',
    color: 'bg-purple-500',
  },
  {
    href: '/studios/ml-lab',
    icon: Brain,
    title: 'ML Lab',
    description: 'No-code machine learning with model comparison',
    color: 'bg-orange-500',
  },
  {
    href: '/studios/research',
    icon: FlaskConical,
    title: 'Research Studio',
    description: 'Complete research environment with hypothesis testing',
    color: 'bg-pink-500',
  },
  {
    href: '/studios/presentations',
    icon: Presentation,
    title: 'Presentations',
    description: 'Automatically generated professional presentations from your analysis',
    color: 'bg-indigo-500',
  },
  {
    href: '/studios/industries',
    icon: Building2,
    title: 'Industry Intelligence',
    description: 'Industry-specific KPIs, templates, and recommendations',
    color: 'bg-teal-500',
  },
  {
    href: '/studios/visualizations',
    icon: Eye,
    title: 'Visualization Engine',
    description: 'Intelligent chart selection and recommendations',
    color: 'bg-cyan-500',
  },
  {
    href: '/studios/mentors',
    icon: BotMessageSquare,
    title: 'Data Assistants',
    description: 'Role-based guidance for data, research, and business decisions',
    color: 'bg-amber-500',
  },
  {
    href: '/studios/collaboration',
    icon: Users,
    title: 'Collaboration',
    description: 'Share, comment, and collaborate on analyses',
    color: 'bg-rose-500',
  },
];

export default function StudiosPage() {
  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-foreground">Data Intelligence Studios</h1>
        <p className="mt-2 text-lg text-muted-foreground">
          One intelligent platform where data enters and decisions come out.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {studios.map((studio) => {
          const Icon = studio.icon;
          return (
            <Link
              key={studio.href}
              href={studio.href}
              className="group relative overflow-hidden rounded-2xl border border-border bg-card p-6 shadow-sm transition-all hover:shadow-lg hover:border-primary/50"
            >
              <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl ${studio.color} text-white mb-4`}>
                <Icon size={24} />
              </div>
              <h3 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
                {studio.title}
              </h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                {studio.description}
              </p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
