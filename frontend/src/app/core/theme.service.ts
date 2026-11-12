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
    this.apply(theme);
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
