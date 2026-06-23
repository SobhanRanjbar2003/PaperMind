import { cn } from '@/lib/utils';

interface LogoProps {
  className?: string;
  showWordmark?: boolean;
}

export function Logo({ className, showWordmark = true }: LogoProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <svg
        width="28"
        height="28"
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0"
        aria-hidden
      >
        <defs>
          <linearGradient id="lg-grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop stopColor="hsl(var(--primary))" />
            <stop offset="1" stopColor="hsl(var(--ring))" />
          </linearGradient>
        </defs>
        <rect width="32" height="32" rx="9" fill="url(#lg-grad)" />
        <path
          d="M9 22V10c0-.55.45-1 1-1h5.5c2.49 0 4.5 2.01 4.5 4.5S17.99 18 15.5 18H12v4H9zm3-7h3.5c1.38 0 2.5-1.12 2.5-2.5S16.88 10 15.5 10H12v5z"
          fill="white"
        />
      </svg>
      {showWordmark ? (
        <span className="font-display text-lg font-semibold tracking-tight">
          PaperMind
        </span>
      ) : null}
    </div>
  );
}
