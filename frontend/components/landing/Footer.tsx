import Link from 'next/link';

const columns = [
  {
    title: 'Product',
    links: [
      { label: 'Features', href: '#features' },
      { label: 'Solutions', href: '#solutions' },
      { label: 'Industries', href: '#industries' },
      { label: 'Pricing', href: '/pricing' },
      { label: 'Templates', href: '/templates' },
    ],
  },
  {
    title: 'Company',
    links: [
      { label: 'About', href: '/about' },
      { label: 'Contact', href: '/contact' },
      { label: 'Help Center', href: '/help' },
      { label: 'System Status', href: '/status' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { label: 'Workflow', href: '#workflow' },
      { label: 'Login', href: '/login' },
      { label: 'Sign Up', href: '/signup' },
      { label: 'Feedback', href: '/feedback' },
      { label: 'Privacy Policy', href: '/privacy' },
      { label: 'Terms of Service', href: '/terms' },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white py-12">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-blue-500 text-sm font-bold text-white shadow-sm shadow-blue-500/30">
                D
              </div>
              <span className="text-base font-bold text-slate-900">DataFlow</span>
            </div>
            <p className="mt-3 text-sm text-slate-500">
              An intelligent analytics platform for businesses, researchers, and organizations.
            </p>
          </div>

          {columns.map((col) => (
            <div key={col.title}>
              <h4 className="text-sm font-semibold text-slate-900">{col.title}</h4>
              <ul className="mt-3 space-y-2">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <Link href={link.href} className="text-sm text-slate-500 transition-colors hover:text-blue-600">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 border-t border-slate-200 pt-6 text-center text-sm text-slate-400">
          © {new Date().getFullYear()} DataFlow. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
