import { Component, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { TPipe } from '../../shared/t.pipe';
import { GoogleButton } from '../../components/google-button/google-button';

/** Simple sign-in form (POST /api/auth/login/). Needed so the cart and orders can be used. */
@Component({
  selector: 'app-login',
  imports: [FormsModule, RouterLink, TPipe, GoogleButton],
  template: `
    <div class="container wrap">
      <form class="card box" (ngSubmit)="submit()">
        <h1>{{ 'login.title' | t }}</h1>
        <label>{{ 'login.username' | t }}<input type="text" name="u" [(ngModel)]="username" required autocomplete="username" /></label>
        <label>{{ 'login.password' | t }}<input type="password" name="p" [(ngModel)]="password" required autocomplete="current-password" /></label>
        @if (error()) { <div class="error-text">{{ 'login.error' | t }}</div> }
        <button class="btn block" type="submit" [disabled]="busy() || !username || !password">{{ 'login.submit' | t }}</button>
        <app-google-button [next]="next()" />
        <p class="alt">{{ 'login.no_account' | t }} <a routerLink="/register" [queryParams]="{ next: next() }">{{ 'login.create' | t }}</a></p>
        <p class="demo">{{ 'login.demo' | t }}: <code>customer</code> / <code>demo12345</code></p>
      </form>
    </div>
  `,
  styles: `
    .wrap { padding-top: 56px; padding-bottom: 80px; display: grid; place-items: center; }
    .box { width: 100%; max-width: 400px; padding: 28px; display: flex; flex-direction: column; gap: 14px; }
    h1 { margin: 0 0 4px; font-size: 26px; font-weight: 800; }
    label { display: flex; flex-direction: column; gap: 6px; font-size: 13px; font-weight: 600; color: var(--muted); input { color: var(--text); } }
    .alt { margin: 0; text-align: center; font-size: 14px; color: var(--muted); a { color: var(--accent); font-weight: 700; } }
    .demo { margin: 4px 0 0; font-size: 13px; color: var(--muted); text-align: center; code { font-family: var(--mono); color: var(--text); } }
  `,
})
export class LoginPage {
  private auth = inject(AuthService);
  private router = inject(Router);
  next = input<string>('/'); // ?next=/cart → go back there after login

  username = '';
  password = '';
  busy = signal(false);
  error = signal(false);

  submit() {
    this.busy.set(true);
    this.error.set(false);
    this.auth.login(this.username, this.password).subscribe({
      next: () => this.router.navigateByUrl(this.next() || '/'),
      error: () => {
        this.busy.set(false);
        this.error.set(true);
      },
    });
  }
}
