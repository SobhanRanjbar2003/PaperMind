import { setRequestLocale } from 'next-intl/server';
import { QAView } from '@/components/qa/qa-view';

export default async function QAPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  return <QAView jobId={id} />;
}
