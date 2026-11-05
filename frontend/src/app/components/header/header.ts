import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { I18nService, Lang } from '../../core/i18n.service';
import { ThemeService } from '../../core/theme.service';
import { TPipe } from '../../shared/t.pipe';

@Component({
  selector: 'app-header',
  imports: [RouterLink, FormsModule, TPipe],
  templateUrl: './header.html',
  styleUrl: './header.scss',
})
export class Header implements OnInit {
  private api = inject(ApiService);
  private router = inject(Router);
  i18n = inject(I18nService);
  theme = inject(ThemeService);

  apiOnline = signal<boolean | null>(null); // null = checking
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
}
