import { Component, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { RegisterData } from '../../core/models';
import { TPipe } from '../../shared/t.pipe';
import { GoogleButton } from '../../components/google-button/google-button';

/** POST /api/auth/register/ — on success the user is signed in and sent back to where they came from. */
@Component({
  selector: 'app-register',
  imports: [FormsModule, RouterLink, TPipe, GoogleButton],
  template: `
    <div class="container wrap">
      <form class="card box" (ngSubmit)="submit()" #f="ngForm" novalidate>
        <h1>{{ 'reg.title' | t }}</h1>
        <p class="sub">{{ 'reg.sub' | t }}</p>

        <div class="row2">
          <label>{{ 'reg.first_name' | t }}
            <input type="text" name="first_name" [(ngModel)]="data.first_name" autocomplete="given-name" />
          </label>
          <label>{{ 'reg.last_name' | t }}
            <input type="text" name="last_name" [(ngModel)]="data.last_name" autocomplete="family-name" />
          </label>
        </div>

        <label>{{ 'reg.username' | t }} *
          <input type="text" name="username" [(ngModel)]="data.username" required autocomplete="username" [class.bad]="errors()['username']" />
          @if (errors()['username']) { <span class="error-text">{{ errors()['username'] }}</span> }
        </label>

        <label>{{ 'reg.email' | t }} *
          <input type="email" name="email" [(ngModel)]="data.email" required email autocomplete="email" [class.bad]="errors()['email']" />
          @if (errors()['email']) { <span class="error-text">{{ errors()['email'] }}</span> }
        </label>

        <label><span>{{ 'reg.phone' | t }} <em>({{ 'reg.optional' | t }})</em></span>
          <input type="tel" name="phone" [(ngModel)]="data.phone" placeholder="+7 700 123 45 67" autocomplete="tel" [class.bad]="errors()['phone']" />
          @if (errors()['phone']) { <span class="error-text">{{ errors()['phone'] }}</span> }
        </label>

        <div class="row2">
          <label>{{ 'reg.password' | t }} *
            <input type="password" name="password" [(ngModel)]="data.password" required minlength="8" autocomplete="new-password" [class.bad]="errors()['password']" />
          </label>
          <label>{{ 'reg.password2' | t }} *
            <input type="password" name="password2" [(ngModel)]="data.password2" required autocomplete="new-password"
                   [class.bad]="mismatch() || errors()['password2']" />
          </label>
        </div>
        @if (errors()['password']) { <span class="error-text">{{ errors()['password'] }}</span> }
        @else if (mismatch()) { <span class="error-text">{{ 'reg.mismatch' | t }}</span> }
        @else { <span class="hint">{{ 'reg.password_hint' | t }}</span> }

        @if (errors()['non_field_errors']) { <div class="error-text">{{ errors()['non_field_errors'] }}</div> }

        <button class="btn block" type="submit" [disabled]="busy() || !f.valid || mismatch()">{{ 'reg.submit' | t }}</button>
        <app-google-button [next]="next()" />
        <p class="alt">{{ 'reg.have_account' | t }} <a routerLink="/login" [queryParams]="{ next: next() }">{{ 'nav.login' | t }}</a></p>
      </form>
    </div>
  `,
  styles: `
    .wrap { padding-top: 40px; padding-bottom: 80px; display: grid; place-items: center; }
    .box { width: 100%; max-width: 480px; padding: 28px; display: flex; flex-direction: column; gap: 14px; }
    h1 { margin: 0; font-size: 26px; font-weight: 800; }
    .sub { margin: -6px 0 4px; color: var(--muted); }
    .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    label { display: flex; flex-direction: column; gap: 6px; font-size: 13px; font-weight: 600; color: var(--muted);
      input { color: var(--text); } em { font-style: normal; font-weight: 500; } }
    input.bad { border-color: var(--danger); }
    .hint { font-size: 12px; color: var(--muted); margin-top: -6px; }
    .error-text { margin-top: -2px; }
    .alt { margin: 0; text-align: center; font-size: 14px; color: var(--muted); a { color: var(--accent); font-weight: 700; } }
    @media (max-width: 480px) { .row2 { grid-template-columns: 1fr; } }
  `,
})
export class RegisterPage {
  private auth = inject(AuthService);
  private router = inject(Router);
  next = input<string>('/');

  data: RegisterData = { username: '', email: '', password: '', password2: '', first_name: '', last_name: '', phone: '' };
  busy = signal(false);
  errors = signal<Record<string, string>>({});

  mismatch() {
    return !!this.data.password2 && this.data.password !== this.data.password2;
  }

  submit() {
    this.busy.set(true);
    this.errors.set({});
    this.auth.register(this.data).subscribe({
      next: () => this.router.navigateByUrl(this.next() || '/'),
      error: (e) => {
        this.busy.set(false);
        // DRF returns {field: ["message", ...]} → show each message under its field
        const out: Record<string, string> = {};
        for (const [k, v] of Object.entries(e?.error ?? {})) out[k] = Array.isArray(v) ? v.join(' ') : String(v);
        if (!Object.keys(out).length) out['non_field_errors'] = 'Network error';
        this.errors.set(out);
      },
    });
  }
}
