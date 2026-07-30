'use client';

import dynamic from 'next/dynamic';

const Navbar = dynamic(() => import('./Navbar').then(m => m.Navbar), { ssr: true });
const Hero = dynamic(() => import('./Hero').then(m => m.Hero), { ssr: true });
const ProductPreview = dynamic(() => import('./ProductPreview').then(m => m.ProductPreview), { ssr: false, loading: () => <div className="min-h-[400px]" /> });
const Problem = dynamic(() => import('./Problem').then(m => m.Problem), { ssr: false, loading: () => <div className="min-h-[300px]" /> });
const HowItWorks = dynamic(() => import('./HowItWorks').then(m => m.HowItWorks), { ssr: false, loading: () => <div className="min-h-[300px]" /> });
const IndustryShowcase = dynamic(() => import('./IndustryShowcase').then(m => m.IndustryShowcase), { ssr: false, loading: () => <div className="min-h-[400px]" /> });
const Studios = dynamic(() => import('./Studios').then(m => m.Studios), { ssr: false, loading: () => <div className="min-h-[400px]" /> });
const SmartDataCapture = dynamic(() => import('./SmartDataCapture').then(m => m.SmartDataCapture), { ssr: false, loading: () => <div className="min-h-[400px]" /> });
const ReportingShowcase = dynamic(() => import('./ReportingShowcase').then(m => m.ReportingShowcase), { ssr: false, loading: () => <div className="min-h-[400px]" /> });
const Comparison = dynamic(() => import('./Comparison').then(m => m.Comparison), { ssr: false, loading: () => <div className="min-h-[400px]" /> });
const CustomerTypes = dynamic(() => import('./CustomerTypes').then(m => m.CustomerTypes), { ssr: false, loading: () => <div className="min-h-[300px]" /> });
const TemplateLibrary = dynamic(() => import('./TemplateLibrary').then(m => m.TemplateLibrary), { ssr: false, loading: () => <div className="min-h-[400px]" /> });
const Trust = dynamic(() => import('./Trust').then(m => m.Trust), { ssr: false, loading: () => <div className="min-h-[300px]" /> });
const Resources = dynamic(() => import('./Resources').then(m => m.Resources), { ssr: false, loading: () => <div className="min-h-[300px]" /> });
const CTA = dynamic(() => import('./CTA').then(m => m.CTA), { ssr: false, loading: () => <div className="min-h-[200px]" /> });
const Footer = dynamic(() => import('./Footer').then(m => m.Footer), { ssr: false, loading: () => <div className="min-h-[200px]" /> });

export function LandingContent() {
  return (
    <>
      <Navbar />
      <Hero />
      <ProductPreview />
      <Problem />
      <HowItWorks />
      <IndustryShowcase />
      <Studios />
      <SmartDataCapture />
      <ReportingShowcase />
      <Comparison />
      <CustomerTypes />
      <TemplateLibrary />
      <Trust />
      <Resources />
      <CTA />
      <Footer />
    </>
  );
}
