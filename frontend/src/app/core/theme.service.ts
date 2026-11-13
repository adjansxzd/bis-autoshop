import { Injectable, signal } from '@angular/core';

export type Theme = 'dark' | 'light';

/**
 * Dark / light theme. Sets <html data-theme="..."> and the CSS variables in styles.scss do the rest.
 * Choice is remembered in localStorage; first visit follows the operating system setting.
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly theme = signal<Theme>(this.initialTheme());

  constructor() {
    this.apply(this.theme());
  }

  toggle() {
    this.set(this.theme() === 'dark' ? 'light' : 'dark');
  }

  set(theme: Theme) {
    this.theme.set(theme);
    // Cross-fade the whole page in one go (View Transitions API). Without it the background
    // animated while cards switched instantly, which looked broken. Older browsers just switch.
    const doc = document as Document & { startViewTransition?: (cb: () => void) => unknown };
    if (doc.startViewTransition && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      doc.startViewTransition(() => this.apply(theme));
    } else {
      this.apply(theme);
    }
    try {
      localStorage.setItem('theme', theme);
    } catch {}
  }

  private apply(theme: Theme) {
    document.documentElement.setAttribute('data-theme', theme);
  }

  private initialTheme(): Theme {
    try {
      const saved = localStorage.getItem('theme');
      if (saved === 'dark' || saved === 'light') return saved;
    } catch {}
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
}
