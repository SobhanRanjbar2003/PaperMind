import { setRequestLocale } from 'next-intl/server';
import { LibraryView } from '@/components/jobs/library-view';

export default async function LibraryPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <LibraryView />;
}
