import { Component, ElementRef, NgZone, OnInit, inject, input, signal, viewChild } from '@angular/core';
import { Router } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { apiError } from '../../core/cart.service';
import { I18nService } from '../../core/i18n.service';
import { ThemeService } from '../../core/theme.service';
import { TPipe } from '../../shared/t.pipe';

declare const google: any; // Google Identity Services, loaded from accounts.google.com when needed

const GSI_SRC = 'https://accounts.google.com/gsi/client';

/**
 * "Sign in with Google" button. Shown only when the backend has GOOGLE_CLIENT_ID set
 * (GET /api/auth/google/config/). Google returns an ID token → POST /api/auth/google/ → our JWT tokens.
 */
@Component({
  selector: 'app-google-button',
  imports: [TPipe],
  template: `
    @if (clientId()) {
      <div class="or"><span>{{ 'login.or' | t }}</span></div>
      <div #slot class="slot"></div>
      @if (error()) { <div class="error-text">{{ error() }}</div> }
    }
  `,
  styles: `
    :host { display: block; }
    .or { display: flex; align-items: center; gap: 12px; color: var(--muted); font-size: 13px; margin: 2px 0 12px;
      &::before, &::after { content: ''; flex: 1; height: 1px; background: var(--line); } }
    .slot { display: flex; justify-content: center; min-height: 44px; }
    .error-text { margin-top: 8px; text-align: center; }
  `,
})
export class GoogleButton implements OnInit {
  private auth = inject(AuthService);
  private router = inject(Router);
  private zone = inject(NgZone);
  private i18n = inject(I18nService);
  private theme = inject(ThemeService);
  next = input<string>('/');

  clientId = signal('');
  error = signal('');
  private slot = viewChild<ElementRef<HTMLDivElement>>('slot');

  ngOnInit() {
    this.auth.googleClientId().subscribe({
      next: (id) => {
        if (!id) return;
        this.clientId.set(id);
        loadScript().then(() => this.render(id), () => this.error.set(this.i18n.t('login.google_unavailable')));
      },
      error: () => {},
    });
  }

  private render(clientId: string): void {
    const el = this.slot()?.nativeElement;
    if (!el) {
      setTimeout(() => this.render(clientId), 50);
      return;
    }
    google.accounts.id.initialize({
      client_id: clientId,
      callback: (res: { credential: string }) => this.zone.run(() => this.signIn(res.credential)),
    });
    google.accounts.id.renderButton(el, {
      theme: this.theme.theme() === 'dark' ? 'filled_black' : 'outline',
      size: 'large',
      width: 340,
      text: 'continue_with',
      locale: this.i18n.lang(),
    });
  }

  private signIn(credential: string) {
    this.error.set('');
    this.auth.googleLogin(credential).subscribe({
      next: () => this.router.navigateByUrl(this.next() || '/'),
      error: (e) => this.error.set(apiError(e)),
    });
  }
}

let loading: Promise<void> | null = null;
function loadScript(): Promise<void> {
  if (typeof google !== 'undefined') return Promise.resolve();
  return (loading ??= new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = GSI_SRC;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => { loading = null; reject(); };
    document.head.appendChild(s);
  }));
}
