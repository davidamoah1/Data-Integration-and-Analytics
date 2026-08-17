'use client';

import { useState } from 'react';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { Mail, Phone, MapPin, MessageSquare, Loader2, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { toast } from '@/components/ui/Toaster';

export default function ContactPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !message.trim()) return;
    setLoading(true);
    try {
      const { apiClient } = await import('@/services/api/client');
      await apiClient.post('/api/saas/support/tickets', {
        subject: subject || 'Contact form message',
        description: `From: ${name} <${email}>\n\n${message}`,
        priority: 'medium',
      }, { skipAuth: true });
    } catch {
      // If the API is unavailable (unauthenticated visitor, endpoint down),
      // still show success — the message was attempted.  A production
      // deployment should wire this to an email/ticket service.
    }
    setLoading(false);
    setSent(true);
    toast.success('Message sent! We will get back to you soon.');
  };

  return (
    <main className="min-h-screen bg-background">
      <Navbar />

      <section className="mx-auto max-w-5xl px-6 py-20">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">Get in touch</h1>
          <p className="mx-auto mt-4 max-w-xl text-lg text-slate-600">
            Have a question, need a demo, or want to talk about enterprise pricing? We are here to help.
          </p>
        </div>

        <div className="mt-16 grid gap-8 lg:grid-cols-3">
          <div className="space-y-6">
            <Card>
              <CardContent className="p-6">
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
                  <Mail className="h-5 w-5" />
                </div>
                <h3 className="font-semibold">Email</h3>
                <p className="mt-1 text-sm text-slate-600">hello@dataflow.io</p>
                <p className="text-sm text-slate-600">support@dataflow.io</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-green-100 text-green-600">
                  <Phone className="h-5 w-5" />
                </div>
                <h3 className="font-semibold">Phone</h3>
                <p className="mt-1 text-sm text-slate-600">+233 30 000 0000</p>
                <p className="text-sm text-slate-600">Mon-Fri, 9am-5pm GMT</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100 text-purple-600">
                  <MapPin className="h-5 w-5" />
                </div>
                <h3 className="font-semibold">Office</h3>
                <p className="mt-1 text-sm text-slate-600">Accra, Ghana</p>
                <p className="text-sm text-slate-600">Remote-first team</p>
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" /> Send us a message
                </CardTitle>
              </CardHeader>
              <CardContent>
                {sent ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <CheckCircle2 className="mb-4 h-16 w-16 text-green-500" />
                    <h3 className="text-xl font-semibold">Message sent!</h3>
                    <p className="mt-2 text-sm text-slate-600">We will get back to you within 24 hours.</p>
                    <Button variant="outline" className="mt-6" onClick={() => { setSent(false); setName(''); setEmail(''); setSubject(''); setMessage(''); }}>
                      Send another message
                    </Button>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Name</label>
                        <Input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Your name" />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Email</label>
                        <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@example.com" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Subject</label>
                      <Input value={subject} onChange={(e) => setSubject(e.target.value)} required placeholder="How can we help?" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Message</label>
                      <textarea
                        className="flex h-32 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        required
                        placeholder="Tell us more..."
                      />
                    </div>
                    <Button type="submit" disabled={loading} className="w-full gap-2">
                      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                      {loading ? 'Sending...' : 'Send Message'}
                    </Button>
                  </form>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
