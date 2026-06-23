'use client';

import { useTranslations } from 'next-intl';
import { Check, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { PresentationTemplate } from '@/types/api';

interface PalettePickerProps {
  templates: PresentationTemplate[];
  selected: string | null;
  onSelect: (name: string | null) => void;
  disabled?: boolean;
}

export function PalettePicker({
  templates,
  selected,
  onSelect,
  disabled,
}: PalettePickerProps) {
  const t = useTranslations('Presentation');

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={() => onSelect(null)}
        disabled={disabled}
        className={cn(
          'group flex w-full items-center gap-3 rounded-xl border bg-card p-3 text-start transition-all',
          selected === null
            ? 'border-primary ring-2 ring-primary/30 bg-primary/5'
            : 'hover:border-primary/40 hover:shadow-sm',
          disabled && 'opacity-50 pointer-events-none',
        )}
      >
        <div className="grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br from-primary/20 to-primary/0 text-primary">
          <Sparkles className="h-4 w-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium">{t('letAIDecide')}</div>
        </div>
        {selected === null ? <Check className="h-4 w-4 text-primary" /> : null}
      </button>

      <div className="grid gap-2 sm:grid-cols-2">
        {templates.map((tpl) => {
          const active = selected === tpl.name;
          return (
            <button
              key={tpl.name}
              type="button"
              onClick={() => onSelect(tpl.name)}
              disabled={disabled}
              className={cn(
                'group flex items-center gap-3 rounded-xl border bg-card p-3 text-start transition-all',
                active
                  ? 'border-primary ring-2 ring-primary/30 bg-primary/5'
                  : 'hover:border-primary/40 hover:shadow-sm',
                disabled && 'opacity-50 pointer-events-none',
              )}
            >
              <PalettePreview colors={tpl.colors} />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{tpl.name}</div>
                {tpl.description ? (
                  <div className="text-xs text-muted-foreground line-clamp-2">
                    {tpl.description}
                  </div>
                ) : null}
              </div>
              {active ? <Check className="h-4 w-4 text-primary" /> : null}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function PalettePreview({ colors }: { colors: PresentationTemplate['colors'] }) {
  return (
    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border bg-background overflow-hidden">
      <div className="grid h-full w-full grid-cols-3">
        <div style={{ background: `#${colors.primary}` }} />
        <div style={{ background: `#${colors.secondary}` }} />
        <div style={{ background: `#${colors.accent}` }} />
      </div>
    </div>
  );
}
