'use client';

import { Command } from 'cmdk';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/i18n/routing';
import { useUIStore } from '@/store/ui';
import { useJobsStore } from '@/store/jobs';
import { useTheme } from 'next-themes';
import { useEffect } from 'react';
import { BookOpen, Home, Upload, Library, Moon, PanelLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

export function CommandPalette() {
  const t = useTranslations('Command');
  const open = useUIStore((s) => s.commandOpen);
  const setOpen = useUIStore((s) => s.setCommandOpen);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const router = useRouter();
  const recents = useJobsStore((s) => s.recents);
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen(!open);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, setOpen]);

  const go = (path: string) => {
    setOpen(false);
    router.push(path);
  };

  return (
    <>
      {open ? (
        <div
          className="fixed inset-0 z-50 grid place-items-start pt-[12vh] bg-black/40 backdrop-blur-sm animate-fade-in"
          onClick={() => setOpen(false)}
        >
          <div
            className="relative w-full max-w-xl mx-auto rounded-2xl border bg-popover shadow-2xl overflow-hidden animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            <Command label="Command Menu" className="bg-popover">
              <div className="px-3 border-b border-border">
                <Command.Input
                  placeholder={t('placeholder')}
                  className={cn(
                    'h-12 w-full bg-transparent outline-none placeholder:text-muted-foreground text-sm',
                  )}
                />
              </div>
              <Command.List className="max-h-96 overflow-y-auto p-2">
                <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
                  {t('emptyTitle')}
                </Command.Empty>

                <Command.Group heading={t('groupNavigation')} className="text-xs text-muted-foreground px-2 py-1">
                  <Item icon={<Home className="h-4 w-4" />} onSelect={() => go('/')}>
                    Home
                  </Item>
                  <Item icon={<Library className="h-4 w-4" />} onSelect={() => go('/library')}>
                    Library
                  </Item>
                </Command.Group>

                <Command.Group heading={t('groupActions')} className="text-xs text-muted-foreground px-2 py-1">
                  <Item icon={<Upload className="h-4 w-4" />} onSelect={() => go('/')}>
                    {t('actionNewJob')}
                  </Item>
                  <Item
                    icon={<Moon className="h-4 w-4" />}
                    onSelect={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  >
                    {t('actionToggleTheme')}
                  </Item>
                  <Item icon={<PanelLeft className="h-4 w-4" />} onSelect={toggleSidebar}>
                    {t('actionToggleSidebar')}
                  </Item>
                </Command.Group>

                {recents.length > 0 ? (
                  <Command.Group heading={t('groupRecents')} className="text-xs text-muted-foreground px-2 py-1">
                    {recents.slice(0, 8).map((r) => (
                      <Item
                        key={r.jobId}
                        icon={<BookOpen className="h-4 w-4" />}
                        onSelect={() => go(`/jobs/${r.jobId}`)}
                      >
                        <span className="truncate">{r.filename}</span>
                      </Item>
                    ))}
                  </Command.Group>
                ) : null}
              </Command.List>
            </Command>
          </div>
        </div>
      ) : null}
    </>
  );
}

function Item({
  children,
  icon,
  onSelect,
}: {
  children: React.ReactNode;
  icon?: React.ReactNode;
  onSelect: () => void;
}) {
  return (
    <Command.Item
      onSelect={onSelect}
      className="flex items-center gap-2.5 rounded-md px-2 py-2 text-sm text-foreground cursor-pointer data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground"
    >
      {icon}
      <span className="truncate">{children}</span>
    </Command.Item>
  );
}
