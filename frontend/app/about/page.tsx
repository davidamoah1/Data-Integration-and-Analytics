import type { Metadata } from 'next';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { Heart, Target, Users, Globe, Award, TrendingUp } from 'lucide-react';

export const metadata: Metadata = {
  title: 'About — DataFlow',
  description: 'We are building the analytics platform that makes data accessible to everyone.',
};

const values = [
  { icon: Heart, title: 'Accessibility First', description: 'Data tools should be usable by anyone, not just data scientists.' },
  { icon: Target, title: 'Workflow-Driven', description: 'Every feature exists to solve a real-world problem in a real workflow.' },
  { icon: Users, title: 'Built for Teams', description: 'From solo researchers to enterprise teams, we scale with you.' },
  { icon: Globe, title: 'Global Impact', description: 'Serving hospitals, universities, governments, and NGOs worldwide.' },
  { icon: Award, title: 'Excellence', description: 'We hold ourselves to the highest standards of quality and reliability.' },
  { icon: TrendingUp, title: 'Continuous Improvement', description: 'We constantly refine and improve based on user feedback.' },
];

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-background">
      <Navbar />

      <section className="mx-auto max-w-4xl px-6 py-20">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Making data accessible to everyone
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-600">
            DataFlow was built on a simple belief: powerful data analytics should not require
            a PhD in statistics or expensive enterprise software. We are building the platform
            that makes data work for everyone.
          </p>
        </div>

        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {values.map((value) => {
            const Icon = value.icon;
            return (
              <div key={value.title} className="rounded-xl border border-slate-200 bg-white p-6">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900">{value.title}</h3>
                <p className="mt-2 text-sm text-slate-600">{value.description}</p>
              </div>
            );
          })}
        </div>

        <div className="mt-20 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 p-12 text-center text-white">
          <h2 className="text-2xl font-bold">Our Mission</h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-blue-100">
            To empower organizations across healthcare, education, government, research, and business
            to transform raw data into meaningful decisions — without the complexity of traditional BI tools.
          </p>
        </div>

        <div className="mt-16 grid gap-8 sm:grid-cols-3">
          <div className="text-center">
            <p className="text-4xl font-bold text-blue-600">10+</p>
            <p className="mt-1 text-sm text-slate-600">Industries served</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-blue-600">5</p>
            <p className="mt-1 text-sm text-slate-600">Workflow templates</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-blue-600">100%</p>
            <p className="mt-1 text-sm text-slate-600">Browser-based, no install</p>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
