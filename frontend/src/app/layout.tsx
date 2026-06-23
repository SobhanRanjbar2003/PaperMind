import './globals.css';
import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = {
  title: {
    default: 'PaperMind — Books, distilled.',
    template: '%s · PaperMind',
  },
  description: 'Turn any book into a structured summary, mind map, slide deck, and quizzes.',
  applicationName: 'PaperMind',
  openGraph: {
    title: 'PaperMind — Books, distilled.',
    description: 'Turn any book into a study system: summary, mind map, slides, quizzes.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'PaperMind',
    description: 'Turn any book into a study system.',
  },
  icons: {
    icon: '/favicon.svg',
    shortcut: '/favicon.svg',
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#0a0d14' },
  ],
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return children;
}
