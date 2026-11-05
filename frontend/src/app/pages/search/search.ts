import { Component, inject, input, signal, effect } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { SearchResult } from '../../core/models';
import { ProductCard } from '../../components/product-card/product-card';
import { PartIcon } from '../../shared/part-icon';
import { LocPipe, TPipe } from '../../shared/t.pipe';

/** Global search page: one query → products, categories and car models (GET /api/search/?q=). */
@Component({
  selector: 'app-search',
  imports: [RouterLink, ProductCard, PartIcon, TPipe, LocPipe],
  templateUrl: './search.html',
  styleUrl: './search.scss',
})
export class Search {
  private api = inject(ApiService);
  q = input<string>(''); // ?q= query param

  result = signal<SearchResult | null>(null);
  loading = signal(false);

  constructor() {
    // re-run search whenever ?q= changes
    effect(() => {
      const q = (this.q() || '').trim();
      if (q.length < 2) {
        this.result.set(null);
        return;
      }
      this.loading.set(true);
      this.api.search(q).subscribe({
        next: (r) => { this.result.set(r); this.loading.set(false); },
        error: () => this.loading.set(false),
      });
    });
  }

  isEmpty(r: SearchResult) {
    return !r.products.length && !r.categories.length && !r.cars.length;
  }
}
