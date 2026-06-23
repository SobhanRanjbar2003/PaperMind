'use client';

import { useTranslations } from 'next-intl';

export function HowItWorks() {
  const t = useTranslations('Home');
  const steps = [
    { n: '01', title: t('step1Title'), body: t('step1Body') },
    { n: '02', title: t('step2Title'), body: t('step2Body') },
    { n: '03', title: t('step3Title'), body: t('step3Body') },
  ];

  return (
    <section className="container py-16">
      <div className="mb-10 max-w-2xl">
        <h2 className="font-display text-3xl font-semibold tracking-tight">
          {t('howItWorksTitle')}
        </h2>
      </div>
      <div className="grid gap-6 sm:grid-cols-3">
        {steps.map((s) => (
          <div
            key={s.n}
            className="relative rounded-2xl border bg-card p-6 transition-colors hover:border-primary/40"
          >
            <span className="font-display text-4xl font-semibold text-primary/30">
              {s.n}
            </span>
            <h3 className="mt-3 font-display text-lg font-semibold">{s.title}</h3>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{s.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
