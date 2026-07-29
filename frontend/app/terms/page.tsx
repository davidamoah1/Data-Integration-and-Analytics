'use client';

import Link from 'next/link';
import { FileText } from 'lucide-react';

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <FileText size={20} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Terms of Service</h1>
            <p className="text-sm text-slate-500">Last updated: January 2025</p>
          </div>
        </div>

        <div className="space-y-6 rounded-xl border border-slate-200 bg-white p-8 text-sm leading-relaxed text-slate-700">
          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">1. Acceptance of Terms</h2>
            <p>By accessing and using DataFlow (&quot;the Service&quot;), you agree to be bound by these Terms of Service and all applicable laws and regulations. If you do not agree with any of these terms, you are prohibited from using or accessing this Service.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">2. Use of the Service</h2>
            <p>You may use the Service only for lawful purposes and in accordance with these Terms. You are responsible for maintaining the confidentiality of your account and password and for restricting access to your computer. You agree not to use the Service for any unlawful or prohibited purpose.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">3. Data and Privacy</h2>
            <p>You retain all rights to your data uploaded to the Service. We process your data in accordance with our Privacy Policy. We do not sell your data to third parties. You may request deletion of your data at any time.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">4. Account Security</h2>
            <p>You are responsible for safeguarding your account credentials. We implement industry-standard security measures including password hashing, JWT-based authentication, and session management. You must notify us immediately of any unauthorized use of your account.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">5. Acceptable Use</h2>
            <p>You agree not to: (a) upload malicious or copyrighted material without permission, (b) attempt to access other users&apos; data, (c) use the Service to transmit spam or harmful code, (d) reverse engineer or disrupt the Service, or (e) use the Service in violation of applicable laws.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">6. Subscription and Billing</h2>
            <p>Free and paid plans may be available. Paid subscriptions are billed in advance on a recurring basis. You may cancel your subscription at any time. Refunds are subject to our refund policy.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">7. Service Modifications</h2>
            <p>We reserve the right to modify or discontinue the Service at any time. We will provide reasonable notice of any significant changes that affect your use of the Service.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">8. Limitation of Liability</h2>
            <p>The Service is provided &quot;as is&quot; without warranties of any kind. We are not liable for any indirect, incidental, or consequential damages arising from your use of the Service.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">9. Contact</h2>
            <p>If you have questions about these Terms, please contact us at <a href="mailto:support@dataflow.io" className="text-primary hover:underline">support@dataflow.io</a>.</p>
          </section>
        </div>

        <div className="mt-6 flex items-center justify-between">
          <Link href="/signup" className="text-sm text-primary hover:underline">← Back to Sign Up</Link>
          <Link href="/privacy" className="text-sm text-primary hover:underline">Privacy Policy →</Link>
        </div>
      </div>
    </div>
  );
}
