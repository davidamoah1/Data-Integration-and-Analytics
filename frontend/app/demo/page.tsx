'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Navbar } from '@/components/landing-v2/Navbar';
import { Footer } from '@/components/landing-v2/Footer';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { toast } from '@/components/ui/Toaster';
import { Calendar, Clock, Users, CheckCircle2, Loader2, ArrowRight, Sparkles, BarChart3, Database, Bot } from 'lucide-react';

const demoFeatures = [
  { icon: Database, title: 'Data Collection & Preparation', description: 'Upload, clean, and validate datasets with AI-powered semantic analysis.' },
  { icon: BarChart3, title: 'Dashboards & Analytics', description: 'Build interactive dashboards with KPIs, charts, and real-time data.' },
  { icon: Bot, title: 'AI Assistant', description: 'Ask questions in natural language and get instant insights from your data.' },
  { icon: Sparkles, title: 'Smart Data Capture', description: 'OCR-powered paper form digitization with confidence scoring.' },
];

const timeSlots = [
  '9:00 AM', '10:00 AM', '11:00 AM',
  '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM',
];

const industries = [
  'Healthcare', 'Education', 'Business', 'Government', 'Research', 'Other',
];

export default function DemoPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [company, setCompany] = useState('');
  const [industry, setIndustry] = useState('');
  const [teamSize, setTeamSize] = useState('');
  const [date, setDate] = useState('');
  const [timeSlot, setTimeSlot] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    await new Promise((r) => setTimeout(r, 1500));
    setLoading(false);
    setSubmitted(true);
    toast.success('Demo request received! We will confirm your slot via email.');
  };

  return (
    <main className="min-h-screen bg-white">
      <Navbar />

      {/* Hero */}
      <section className="relative overflow-hidden pt-32 pb-12 sm:pt-36">
        <div className="absolute inset-0 -z-10 bg-dot-pattern opacity-40" />
        <div className="absolute -top-40 right-0 -z-10 h-[500px] w-[500px] rounded-full bg-blue-500/10 blur-[120px]" />
        <div className="absolute -bottom-40 left-0 -z-10 h-[400px] w-[400px] rounded-full bg-violet-500/10 blur-[100px]" />

        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-4 py-1.5 text-sm font-medium text-slate-600 shadow-sm backdrop-blur-sm">
            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse-soft" />
            30-minute personalized walkthrough
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Book a <span className="gradient-text">Demo</span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
            See how DataFlow can transform your organization's data workflow — from collection to decision-making. Our team will tailor the demo to your industry and use case.
          </p>
        </div>
      </section>

      {/* Features preview */}
      <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {demoFeatures.map((feature) => {
            const Icon = feature.icon;
            return (
              <div key={feature.title} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:shadow-md">
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="font-semibold text-slate-900">{feature.title}</h3>
                <p className="mt-2 text-sm text-slate-600">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Booking form */}
      <section className="mx-auto max-w-3xl px-4 pb-24 sm:px-6 lg:px-8">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <Calendar className="h-5 w-5 text-blue-600" />
              Schedule Your Demo
            </CardTitle>
          </CardHeader>
          <CardContent>
            {submitted ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <CheckCircle2 className="mb-4 h-16 w-16 text-green-500" />
                <h3 className="text-xl font-semibold text-slate-900">Demo request received!</h3>
                <p className="mt-2 max-w-sm text-sm text-slate-600">
                  Thank you, {name.split(' ')[0] || 'there'}! We will send a confirmation email to <span className="font-medium">{email}</span> shortly with your demo details.
                </p>
                <div className="mt-8 flex gap-3">
                  <Link href="/signup">
                    <Button className="gap-2">
                      Start Free Trial <ArrowRight size={16} />
                    </Button>
                  </Link>
                  <Button variant="outline" onClick={() => { setSubmitted(false); setName(''); setEmail(''); setCompany(''); setIndustry(''); setTeamSize(''); setDate(''); setTimeSlot(''); setMessage(''); }}>
                    Book another demo
                  </Button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Full Name</label>
                    <Input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Jane Doe" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Work Email</label>
                    <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="jane@company.com" />
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Company / Organization</label>
                    <Input value={company} onChange={(e) => setCompany(e.target.value)} required placeholder="Acme Inc." />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Industry</label>
                    <select
                      value={industry}
                      onChange={(e) => setIndustry(e.target.value)}
                      required
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <option value="">Select industry</option>
                      {industries.map((ind) => (
                        <option key={ind} value={ind}>{ind}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">Team Size</label>
                  <div className="flex flex-wrap gap-2">
                    {['1-10', '11-50', '51-200', '200+'].map((size) => (
                      <button
                        key={size}
                        type="button"
                        onClick={() => setTeamSize(size)}
                        className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
                          teamSize === size
                            ? 'border-blue-500 bg-blue-50 text-blue-700'
                            : 'border-slate-200 text-slate-600 hover:border-slate-300'
                        }`}
                      >
                        {size}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700 flex items-center gap-1">
                      <Calendar className="h-4 w-4" /> Preferred Date
                    </label>
                    <Input
                      type="date"
                      value={date}
                      onChange={(e) => setDate(e.target.value)}
                      required
                      min={new Date().toISOString().split('T')[0]}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700 flex items-center gap-1">
                      <Clock className="h-4 w-4" /> Preferred Time (GMT)
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {timeSlots.map((slot) => (
                        <button
                          key={slot}
                          type="button"
                          onClick={() => setTimeSlot(slot)}
                          className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
                            timeSlot === slot
                              ? 'border-blue-500 bg-blue-50 text-blue-700'
                              : 'border-slate-200 text-slate-600 hover:border-slate-300'
                          }`}
                        >
                          {slot}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">
                    What would you like to see in the demo? <span className="text-slate-400">(optional)</span>
                  </label>
                  <textarea
                    className="flex h-24 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Tell us about your use case, challenges, or specific features you'd like to explore..."
                  />
                </div>

                <div className="flex items-center gap-2 rounded-lg bg-slate-50 p-3 text-xs text-slate-500">
                  <Users className="h-4 w-4 shrink-0" />
                  Demos are typically 30 minutes. We will send a calendar invite with a video call link to your email.
                </div>

                <Button type="submit" disabled={loading} className="w-full gap-2">
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                  {loading ? 'Submitting...' : 'Request Demo'}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </section>

      <Footer />
    </main>
  );
}
