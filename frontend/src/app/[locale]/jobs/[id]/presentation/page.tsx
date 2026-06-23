import { setRequestLocale } from 'next-intl/server';
import { PresentationView } from '@/components/presentation/presentation-view';

export default async function PresentationPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  return <PresentationView jobId={id} />;
}
