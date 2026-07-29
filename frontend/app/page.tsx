import type { Metadata } from 'next';
import { Navbar } from '@/components/landing/Navbar';
import { Hero } from '@/components/landing/Hero';
import { Problem } from '@/components/landing/Problem';
import { Solution } from '@/components/landing/Solution';
import { Features } from '@/components/landing/Features';
import { Audience } from '@/components/landing/Audience';
import { Comparison } from '@/components/landing/Comparison';
import { Workflow } from '@/components/landing/Workflow';
import { Trust } from '@/components/landing/Trust';
import { Screenshots } from '@/components/landing/Screenshots';
import { Testimonials } from '@/components/landing/Testimonials';
import { PricingTeaser } from '@/components/landing/PricingTeaser';
import { CTA } from '@/components/landing/CTA';
import { Stats } from '@/components/landing/Stats';
import { Footer } from '@/components/landing/Footer';

export const metadata: Metadata = {
  title: 'DataFlow — Transform Your Data Into Meaningful Decisions',
  description:
    'A complete analytics platform that helps businesses, researchers, and organizations clean, analyze, visualize, and understand their data.',
};

export default function HomePage() {
  return (
    <main className="min-h-screen bg-white">
      <Navbar />
      <Hero />
      <Stats />
      <Problem />
      <Solution />
      <Features />
      <Audience />
      <Comparison />
      <Workflow />
      <Screenshots />
      <Trust />
      <Testimonials />
      <Stats />
      <PricingTeaser />
      <CTA />
      <Footer />
    </main>
  );
}
