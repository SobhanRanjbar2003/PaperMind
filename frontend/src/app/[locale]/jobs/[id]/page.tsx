import { setRequestLocale } from 'next-intl/server';
import { JobDetailView } from '@/components/jobs/job-detail-view';

export default async function JobPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  return <JobDetailView jobId={id} />;
}
