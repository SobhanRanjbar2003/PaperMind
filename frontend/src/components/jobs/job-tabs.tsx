'use client';

import { usePathname } from 'next/navigation';
import { Link } from '@/i18n/routing';
import { useTranslations, useLocale } from 'next-intl';
import { FileText, Network, Presentation, ListChecks } from 'lucide-react';
import { cn } from '@/lib/utils';

export function JobTabs({ jobId }: { jobId: string }) {
  const t = useTranslations('Job');
  const locale = useLocale();
  const pathname = usePathname();

  const tabs = [
    {
      href: `/jobs/${jobId}`,
      label: t('tabsSummary'),
      icon: <FileText className="h-4 w-4" />,
    },
    {
      href: `/jobs/${jobId}/mindmap`,
      label: t('tabsMindmap'),
      icon: <Network className="h-4 w-4" />,
    },
    {
      href: `/jobs/${jobId}/presentation`,
      label: t('tabsPresentation'),
      icon: <Presentation className="h-4 w-4" />,
    },
    {
      href: `/jobs/${jobId}/qa`,
      label: t('tabsQA'),
      icon: <ListChecks className="h-4 w-4" />,
    },
  ];

  return (
    <nav className="container border-b border-border">
      <div className="flex items-center gap-1 overflow-x-auto scrollbar-thin">
        {tabs.map((tab) => {
          const target = `/${locale}${tab.href}`;
          const isActive =
            pathname === target ||
            (tab.href === `/jobs/${jobId}` && pathname === `/${locale}/jobs/${jobId}`);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                'inline-flex items-center gap-2 whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors',
                isActive
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground',
              )}
            >
              {tab.icon}
              {tab.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
