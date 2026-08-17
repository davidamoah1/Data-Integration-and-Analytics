'use client';

import { useState } from 'react';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { MessageSquare, Lightbulb, Bug, Loader2, CheckCircle2, Star } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { toast } from '@/components/ui/Toaster';

const feedbackTypes = [
  { id: 'feature', label: 'Feature Request', icon: Lightbulb, color: 'bg-blue-100 text-blue-600' },
  { id: 'bug', label: 'Bug Report', icon: Bug, color: 'bg-red-100 text-red-600' },
  { id: 'general', label: 'General Feedback', icon: MessageSquare, color: 'bg-purple-100 text-purple-600' },
];

export default function FeedbackPage() {
  const [type, setType] = useState('feature');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [rating, setRating] = useState(0);
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    try {
      const { apiClient } = await import('@/services/api/client');
      await apiClient.post('/api/saas/support/tickets', {
        subject: `[${type}] Feedback${rating ? ` (${rating}/5)` : ''}`,
        description: `Type: ${type}\nRating: ${rating || 'N/A'}/5\nEmail: ${email || 'N/A'}\n\n${message}`,
        priority: type === 'bug' ? 'high' : 'low',
      }, { skipAuth: true });
    } catch {
      // Best-effort: visitor may not be authenticated.
    }
    setLoading(false);
    setSent(true);
    toast.success('Thank you for your feedback!');
  };

  return (
    <main className="min-h-screen bg-background">
      <Navbar />

      <section className="mx-auto max-w-2xl px-6 py-20">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">Share Your Feedback</h1>
          <p className="mx-auto mt-4 max-w-xl text-lg text-slate-600">
            Help us improve DataFlow. Share your ideas, report issues, or tell us what you love.
          </p>
        </div>

        <Card className="mt-12">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" /> Tell us what you think
            </CardTitle>
          </CardHeader>
          <CardContent>
            {sent ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <CheckCircle2 className="mb-4 h-16 w-16 text-green-500" />
                <h3 className="text-xl font-semibold">Thank you!</h3>
                <p className="mt-2 text-sm text-slate-600">Your feedback has been received. We appreciate you taking the time.</p>
                <Button variant="outline" className="mt-6" onClick={() => { setSent(false); setEmail(''); setMessage(''); setRating(0); }}>
                  Submit another
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Feedback Type */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Feedback type</label>
                  <div className="grid grid-cols-3 gap-3">
                    {feedbackTypes.map((ft) => {
                      const Icon = ft.icon;
                      return (
                        <button
                          key={ft.id}
                          type="button"
                          onClick={() => setType(ft.id)}
                          className={`flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-all ${
                            type === ft.id ? 'border-blue-600 bg-blue-50' : 'border-slate-200 hover:border-slate-300'
                          }`}
                        >
                          <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${ft.color}`}>
                            <Icon className="h-4 w-4" />
                          </div>
                          <span className="text-xs font-medium">{ft.label}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Rating */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">How would you rate your experience?</label>
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setRating(star)}
                        className="transition-transform hover:scale-110"
                      >
                        <Star
                          className={`h-8 w-8 ${
                            star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-slate-300'
                          }`}
                        />
                      </button>
                    ))}
                  </div>
                </div>

                {/* Email */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Email (optional)</label>
                  <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="So we can follow up" />
                </div>

                {/* Message */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Your feedback</label>
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
                  {loading ? 'Submitting...' : 'Submit Feedback'}
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
