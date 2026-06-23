'use client';

import { useTranslations } from 'next-intl';
import { FileText, Network, Presentation, ListChecks } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

export function Features() {
  const t = useTranslations('Home');

  const items = [
    {
      icon: <FileText className="h-5 w-5" />,
      title: t('featureSummaryTitle'),
      body: t('featureSummaryBody'),
      accent: 'from-blue-500/15 to-blue-500/5',
    },
    {
      icon: <Network className="h-5 w-5" />,
      title: t('featureMindmapTitle'),
      body: t('featureMindmapBody'),
      accent: 'from-violet-500/15 to-violet-500/5',
    },
    {
      icon: <Presentation className="h-5 w-5" />,
      title: t('featurePptxTitle'),
      body: t('featurePptxBody'),
      accent: 'from-emerald-500/15 to-emerald-500/5',
    },
    {
      icon: <ListChecks className="h-5 w-5" />,
      title: t('featureQATitle'),
      body: t('featureQABody'),
      accent: 'from-amber-500/15 to-amber-500/5',
    },
  ];

  return (
    <section className="container py-16">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((it) => (
          <Card key={it.title} className="group overflow-hidden">
            <CardContent className="p-6">
              <div
                className={`mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br ${it.accent} text-primary`}
              >
                {it.icon}
              </div>
              <h3 className="font-display text-base font-semibold tracking-tight">{it.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{it.body}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
