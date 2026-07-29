import {
  Brush, LayoutDashboard, Building2, Sigma, TrendingUp, FileBarChart,
  Heart, GraduationCap, Landmark, Wheat, ShoppingCart, Globe2, HeartHandshake,
} from 'lucide-react';
import { Reveal } from './Reveal';

const industries = [
  { label: 'Healthcare', icon: Heart },
  { label: 'Education', icon: GraduationCap },
  { label: 'Banking', icon: Landmark },
  { label: 'Agriculture', icon: Wheat },
  { label: 'Retail', icon: ShoppingCart },
  { label: 'Government', icon: Globe2 },
  { label: 'NGOs', icon: HeartHandshake },
];

const features = [
  {
    icon: Brush,
    title: 'Smart Data Preparation',
    description: 'Automatically identify and improve data quality — missing values, duplicates, and inconsistent formats handled for you.',
  },
  {
    icon: LayoutDashboard,
    title: 'Analytics Workspace',
    description: 'Explore datasets in a familiar spreadsheet-style workspace and discover insights as you work.',
  },
  {
    icon: Building2,
    title: 'Industry Dashboards',
    description: 'Specialized analytics and KPIs tailored to different sectors, ready to use out of the box.',
    footer: true,
  },
  {
    icon: Sigma,
    title: 'Statistical Analysis',
    description: 'Professional-grade tools built for researchers, analysts, and students alike.',
  },
  {
    icon: TrendingUp,
    title: 'Predictive Analysis',
    description: 'Discover possible future trends in your data to plan ahead with confidence.',
  },
  {
    icon: FileBarChart,
    title: 'Professional Reports',
    description: 'Generate PDF reports, presentation slides, and executive summaries in a few clicks.',
  },
];

export function Features() {
  return (
    <section id="features" className="bg-white py-24">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-blue-600">Capabilities</span>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Everything you need, built in
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Powerful capabilities that work together, so your team spends less time
            wrangling data and more time making decisions.
          </p>
        </Reveal>

        <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, i) => (
            <Reveal key={feature.title} delay={(i % 3) * 100}>
              <div className="group flex h-full flex-col rounded-2xl border border-slate-200 p-6 transition-all duration-300 hover:-translate-y-1 hover:border-blue-200 hover:shadow-xl hover:shadow-blue-100/50">
                <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-blue-600 transition-colors duration-300 group-hover:bg-blue-600 group-hover:text-white">
                  <feature.icon size={22} />
                </div>
                <h3 className="text-base font-semibold text-slate-900">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{feature.description}</p>

                {feature.footer && (
                  <div id="industries" className="mt-4 flex flex-wrap gap-2">
                    {industries.map((ind) => (
                      <span
                        key={ind.label}
                        className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 transition-colors hover:bg-blue-100 hover:text-blue-700"
                      >
                        <ind.icon size={12} />
                        {ind.label}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
