'use client';

import { useEffect } from 'react';
import { useRouter } from '@/i18n/routing';
import { useUIStore } from '@/store/ui';

/**
 * Global keyboard shortcuts:
 *   ⌘K / Ctrl+K      → command palette  (handled inside CommandPalette)
 *   ⌘B / Ctrl+B      → toggle sidebar
 *   ⌘N / Ctrl+N      → new book (go to upload / home)
 */
export function KeyboardShortcuts() {
  const router = useRouter();
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const isMod = e.metaKey || e.ctrlKey;
      if (!isMod) return;
      const key = e.key.toLowerCase();

      if (key === 'b') {
        e.preventDefault();
        toggleSidebar();
        return;
      }
      if (key === 'n' && !e.shiftKey) {
        e.preventDefault();
        router.push('/');
        return;
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [router, toggleSidebar]);

  return null;
}
