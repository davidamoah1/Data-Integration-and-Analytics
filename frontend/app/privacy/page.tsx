'use client';

import Link from 'next/link';
import { Shield } from 'lucide-react';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Shield size={20} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Privacy Policy</h1>
            <p className="text-sm text-slate-500">Last updated: January 2025</p>
          </div>
        </div>

        <div className="space-y-6 rounded-xl border border-slate-200 bg-white p-8 text-sm leading-relaxed text-slate-700">
          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">1. Information We Collect</h2>
            <p>We collect information you provide directly, including your name, email, organization details, and data you upload for processing. We also collect usage data such as login times, IP addresses, and device information for security and analytics purposes.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">2. How We Use Your Information</h2>
            <p>We use your information to: (a) provide and maintain the Service, (b) authenticate your identity, (c) communicate with you about your account, (d) improve and optimize the Service, (e) detect and prevent fraud or abuse, and (f) comply with legal obligations.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">3. Data Storage and Security</h2>
            <p>Your data is stored securely using industry-standard encryption. Passwords are hashed using bcrypt. Authentication tokens are JWT-based with expiration. We implement rate limiting, session management, and audit logging to protect your account.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">4. Data Retention</h2>
            <p>We retain your data for as long as your account is active. You may request deletion of your account and associated data at any time. Some data may be retained for legal or backup purposes after account deletion.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">5. Data Sharing</h2>
            <p>We do not sell, trade, or rent your personal data to third parties. We may share data with service providers who assist us in operating the Service, subject to confidentiality obligations. We may disclose data when required by law.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">6. Your Rights</h2>
            <p>You have the right to: (a) access your personal data, (b) correct inaccurate data, (c) request deletion of your data, (d) export your data, and (e) opt out of marketing communications. Contact us at <a href="mailto:privacy@dataflow.io" className="text-primary hover:underline">privacy@dataflow.io</a> to exercise these rights.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">7. Cookies</h2>
            <p>We use essential cookies for authentication and session management. We do not use tracking cookies for advertising. You can control cookies through your browser settings.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">8. Children&apos;s Privacy</h2>
            <p>The Service is not intended for children under 16. We do not knowingly collect data from children under 16. If you believe we have collected such data, please contact us for deletion.</p>
          </section>

          <section>
            <h2 className="mb-2 text-lg font-semibold text-slate-900">9. Changes to This Policy</h2>
            <p>We may update this Privacy Policy from time to time. We will notify you of significant changes via email or through the Service.</p>
          </section>
        </div>

        <div className="mt-6 flex items-center justify-between">
          <Link href="/signup" className="text-sm text-primary hover:underline">← Back to Sign Up</Link>
          <Link href="/terms" className="text-sm text-primary hover:underline">Terms of Service →</Link>
        </div>
      </div>
    </div>
  );
}
