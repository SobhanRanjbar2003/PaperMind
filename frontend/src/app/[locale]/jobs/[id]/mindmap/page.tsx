import { setRequestLocale } from 'next-intl/server';
import { MindmapView } from '@/components/mindmap/mindmap-view';

export default async function MindmapPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  return <MindmapView jobId={id} />;
}
