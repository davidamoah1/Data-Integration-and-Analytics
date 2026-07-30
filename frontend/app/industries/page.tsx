import type { Metadata } from 'next';
import Link from 'next/link';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { Button } from '@/components/ui/Button';
import {
  Heart, GraduationCap, Landmark, Wheat, ShoppingCart, Globe2, HeartHandshake,
  ArrowRight,
} from 'lucide-react';

export const metadata: Metadata = {
  title: 'Industries — DataFlow',
  description: 'DataFlow serves healthcare, education, banking, agriculture, retail, government, and NGOs with specialized analytics and KPIs tailored to each sector.',
};

const industries = [
  {
    icon: Heart,
    title: 'Healthcare',
    description: 'Patient outcomes, resource utilization, and operational analytics for hospitals and clinics.',
  },
  {
    icon: GraduationCap,
    title: 'Education',
    description: 'Student performance, enrollment trends, and research data analysis for universities and schools.',
  },
  {
    icon: Landmark,
    title: 'Banking',
    description: 'Risk assessment, transaction analysis, and regulatory reporting for financial institutions.',
  },
  {
    icon: Wheat,
    title: 'Agriculture',
    description: 'Yield tracking, weather pattern analysis, and supply chain optimization for farms and cooperatives.',
  },
  {
    icon: ShoppingCart,
    title: 'Retail',
    description: 'Sales forecasting, inventory management, and customer behavior analytics for retail businesses.',
  },
  {
    icon: Globe2,
    title: 'Government',
    description: 'Public service metrics, census data analysis, and policy impact assessment for government agencies.',
  },
  {
    icon: HeartHandshake,
    title: 'NGOs',
    description: 'Impact measurement, donor analytics, and program effectiveness tracking for non-profit organizations.',
  },
];

export default function IndustriesPage() {
  return (
    <main className="min-h-screen bg-background">
      <Navbar />

      <section className="mx-auto max-w-4xl px-4 pt-32 pb-12 text-center md:px-6">
        <span className="text-sm font-semibold uppercase tracking-wider text-blue-600">Industries</span>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Built for your sector
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
          Specialized analytics and KPIs tailored to different sectors, ready to use out of the box.
        </p>
        <div className="mt-8">
          <Link href="/signup">
            <Button size="lg" className="gap-2">
              Get Started Free <ArrowRight size={18} />
            </Button>
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-16 md:px-6">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {industries.map((industry) => {
            const Icon = industry.icon;
            return (
              <div
                key={industry.title}
                className="group flex h-full flex-col rounded-2xl border border-slate-200 p-6 transition-all duration-300 hover:-translate-y-1 hover:border-blue-200 hover:shadow-xl hover:shadow-blue-100/50"
              >
                <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-blue-600 transition-colors duration-300 group-hover:bg-blue-600 group-hover:text-white">
                  <Icon size={22} />
                </div>
                <h3 className="text-base font-semibold text-slate-900">{industry.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{industry.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      <Footer />
    </main>
  );
}
