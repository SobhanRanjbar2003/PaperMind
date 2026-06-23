'use client';

import { useTranslations } from 'next-intl';
import { Sparkles, ArrowRight, Library } from 'lucide-react';
import { Link } from '@/i18n/routing';
import { Button } from '@/components/ui/button';
import { UploadDropzone } from '@/components/upload/upload-dropzone';

export function Hero() {
  const t = useTranslations('Home');

  return (
    <section className="relative overflow-hidden">
      <div className="absolute inset-0 hero-gradient pointer-events-none" aria-hidden />
      <div className="absolute inset-0 -z-10 grid-bg opacity-40 dark:opacity-15 [mask-image:radial-gradient(70%_50%_at_50%_0%,black,transparent)]" />

      <div className="container relative pt-20 pb-12 sm:pt-28 sm:pb-16">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border bg-background/70 backdrop-blur px-3 py-1 text-xs font-medium text-muted-foreground">
            <Sparkles className="h-3 w-3 text-primary" />
            {t('heroEyebrow')}
          </div>
          <h1 className="font-display text-balance text-4xl sm:text-6xl font-semibold tracking-tighter leading-[1.05]">
            {t('heroTitleA')}{' '}
            <span className="bg-gradient-to-r from-primary to-brand-400 bg-clip-text text-transparent">
              {t('heroTitleB')}
            </span>
          </h1>
          <p className="mt-5 text-balance text-base sm:text-lg leading-relaxed text-muted-foreground">
            {t('heroSubtitle')}
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button size="lg" asChild>
              <a href="#upload">
                {t('ctaPrimary')} <ArrowRight className="h-4 w-4 rtl:rotate-180" />
              </a>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/library">
                <Library className="h-4 w-4" />
                {t('ctaSecondary')}
              </Link>
            </Button>
          </div>
        </div>

        <div className="mx-auto mt-14 max-w-2xl" id="upload">
          <UploadDropzone />
        </div>
      </div>
    </section>
  );
}
