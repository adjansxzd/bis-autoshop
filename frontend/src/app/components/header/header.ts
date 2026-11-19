import { Component, OnInit, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { NavigationEnd, Router, RouterLink, RouterLinkActive } from '@angular/router';
import { filter, map } from 'rxjs';

import { environment } from '../../../environments/environment';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { CartService } from '../../core/cart.service';
import { GarageService } from '../../core/garage.service';
import { I18nService, Lang } from '../../core/i18n.service';
import { ThemeService } from '../../core/theme.service';
import { TPipe } from '../../shared/t.pipe';

@Component({
  selector: 'app-header',
  imports: [RouterLink, RouterLinkActive, FormsModule, TPipe],
  templateUrl: './header.html',
  styleUrl: './header.scss',
})
export class Header implements OnInit {
  private api = inject(ApiService);
  private router = inject(Router);
  i18n = inject(I18nService);
  theme = inject(ThemeService);
  auth = inject(AuthService);
  cart = inject(CartService);
  garage = inject(GarageService);

  readonly adminUrl = environment.adminUrl;
  apiOnline = signal<boolean | null>(null); // null = checking

  /** true on /login and /register: hide search, cart, garage etc. so nothing distracts from the form */
  readonly minimal = toSignal(
    this.router.events.pipe(
      filter((e) => e instanceof NavigationEnd),
      map(() => /^\/(login|register)(\?|$)/.test(this.router.url)),
    ),
    { initialValue: /^\/(login|register)(\?|$)/.test(location.pathname) },
  );
  query = '';

  ngOnInit() {
    // Proves the frontend ↔ backend connection: calls GET /api/health/
    this.api.health().subscribe({
      next: () => this.apiOnline.set(true),
      error: () => this.apiOnline.set(false),
    });
  }

  search() {
    const q = this.query.trim();
    if (q) this.router.navigate(['/search'], { queryParams: { q } });
  }

  setLang(lang: Lang) {
    this.i18n.setLang(lang);
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/']);
  }
}
