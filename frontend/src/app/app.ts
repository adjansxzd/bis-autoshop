import { Component } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';

import { Header } from './components/header/header';
import { TPipe } from './shared/t.pipe';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, Header, TPipe],
  template: `
    <app-header />
    <main class="page"><router-outlet /></main>
    <footer class="site-footer">
      <div class="container cols">
        <div class="brand">
          <a routerLink="/" class="logo">AutoShop</a>
          <p>{{ 'footer.text' | t }}</p>
        </div>
        <ul>
          <li>{{ 'footer.address' | t }}</li>
          <li>{{ 'footer.delivery' | t }}</li>
          <li>© 2026 AutoShop · {{ 'footer.project' | t }}</li>
        </ul>
        <ul>
          <li>+7 727 355 20 20</li>
          <li><a routerLink="/orders">{{ 'nav.orders' | t }}</a></li>
          <li><a routerLink="/account">{{ 'nav.account' | t }}</a></li>
        </ul>
        <ul>
          <li>{{ 'footer.hours' | t }}</li>
          <li><a routerLink="/cart">{{ 'nav.cart' | t }}</a></li>
        </ul>
      </div>
    </footer>
  `,
  styles: `
    :host { display: flex; flex-direction: column; min-height: 100vh; }
    .page { flex: 1; }
    .site-footer { background: var(--panel); border-top: 1px solid var(--line); margin-top: 48px; padding: 40px 0; font-size: 13px; color: var(--muted); }
    .cols { display: grid; grid-template-columns: 1.6fr 1fr 1fr 1fr; gap: 24px; }
    .logo { font-size: 26px; font-weight: 700; color: var(--text); text-decoration: none; letter-spacing: -0.02em; }
    .brand p { margin: 6px 0 0; font-size: 14px; }
    ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
    a { color: inherit; text-decoration: none; &:hover { color: var(--accent); } }
    @media (max-width: 760px) { .cols { grid-template-columns: 1fr 1fr; } .brand { grid-column: 1 / -1; } }
  `,
})
export class App {}
