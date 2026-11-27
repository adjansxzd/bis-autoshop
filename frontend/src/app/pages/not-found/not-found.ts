import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { TPipe } from '../../shared/t.pipe';

/** Figma: "12 Page not found" */
@Component({
  selector: 'app-not-found',
  imports: [RouterLink, TPipe],
  template: `
    <div class="container wrap">
      <div class="card box">
        <div class="code">404</div>
        <h1>{{ 'nf.title' | t }}</h1>
        <p>{{ 'nf.sub' | t }}</p>
        <div class="row">
          <a class="btn" routerLink="/">{{ 'nf.home' | t }} →</a>
          <a class="btn ghost" routerLink="/orders">{{ 'nav.orders' | t }}</a>
        </div>
      </div>
    </div>
  `,
  styles: `
    .wrap { padding-top: 48px; }
    .box { max-width: 656px; margin: 0 auto; padding: 56px 32px; text-align: center; border: 0; }
    .code { font-size: 96px; font-weight: 700; line-height: 1; letter-spacing: -0.04em; color: var(--accent); }
    h1 { font-size: 28px; font-weight: 600; margin: 20px 0 8px; }
    p { color: var(--muted); margin: 0 0 28px; }
    .row { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
  `,
})
export class NotFoundPage {}
