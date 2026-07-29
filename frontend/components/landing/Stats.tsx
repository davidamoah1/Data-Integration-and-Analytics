import { Reveal } from './Reveal';

const stats = [
  { value: '10+', label: 'Industries served' },
  { value: '5', label: 'Workflow templates' },
  { value: '100%', label: 'Browser-based' },
  { value: '24/7', label: 'System availability' },
];

export function Stats() {
  return (
    <section className="bg-slate-950 py-16">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal>
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-4xl font-bold text-transparent">
                  {stat.value}
                </p>
                <p className="mt-1 text-sm text-slate-400">{stat.label}</p>
              </div>
            ))}
          </div>
        </Reveal>
      </div>
    </section>
  );
}
