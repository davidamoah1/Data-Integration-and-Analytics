import type { Metadata } from 'next';
import { LandingContent } from '@/components/landing-v2/LandingContent';

export const metadata: Metadata = {
  title: 'DataFlow — Transform Data Into Decisions',
  description:
    'One platform for collecting, preparing, analyzing, visualizing, reporting, and presenting data across healthcare, education, business, government, research, and more.',
  keywords: [
    'data analytics platform',
    'business intelligence',
    'data visualization',
    'reporting platform',
    'ETL pipeline',
    'dashboard builder',
    'healthcare analytics',
    'education analytics',
    'research analytics',
    'data integration',
  ],
  authors: [{ name: 'DataFlow' }],
  creator: 'DataFlow',
  openGraph: {
    title: 'DataFlow — Transform Data Into Decisions',
    description:
      'One platform for collecting, preparing, analyzing, visualizing, reporting, and presenting data across healthcare, education, business, government, research, and more.',
    type: 'website',
    locale: 'en_US',
    siteName: 'DataFlow',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'DataFlow — Transform Data Into Decisions',
    description:
      'One platform for collecting, preparing, analyzing, visualizing, reporting, and presenting data.',
  },
  robots: {
    index: true,
    follow: true,
  },
  alternates: {
    canonical: '/',
  },
};

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'DataFlow',
  applicationCategory: 'BusinessApplication',
  operatingSystem: 'Web',
  description:
    'One platform for collecting, preparing, analyzing, visualizing, reporting, and presenting data across healthcare, education, business, government, research, and more.',
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'USD',
  },
};

export default function HomePage() {
  return (
    <main className="relative min-h-screen bg-background">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <LandingContent />
    </main>
  );
}
