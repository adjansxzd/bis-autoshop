import { Component, OnInit, computed, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { CartService, apiError } from '../../core/cart.service';
import { GarageService } from '../../core/garage.service';
import { I18nService } from '../../core/i18n.service';
import { Product, ReviewsResponse } from '../../core/models';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { PartIcon } from '../../shared/part-icon';
import { PhotoPipe } from '../../shared/photo';
import { Stars } from '../../shared/stars';
import { QtyStepper } from '../../shared/qty-stepper';
import { KztPipe, LocPipe, TPipe } from '../../shared/t.pipe';

@Component({
  selector: 'app-product-detail',
  imports: [RouterLink, FormsModule, DatePipe, PartIcon, QtyStepper, Stars, PhotoPipe, TPipe, LocPipe, KztPipe],
  templateUrl: './product-detail.html',
  styleUrl: './product-detail.scss',
})
export class ProductDetail implements OnInit {
  private api = inject(ApiService);
  private router = inject(Router);
  cart = inject(CartService);
  garage = inject(GarageService);
  auth = inject(AuthService);
  i18n = inject(I18nService);
  id = input.required<string>(); // from route /product/:id

  product = signal<Product | null>(null);
  error = signal(false);
  qty = signal(1);
  busy = signal(false);
  message = signal('');
  addError = signal('');

  // reviews: GET/POST /api/products/{id}/reviews/, PATCH/DELETE /api/reviews/{id}/
  reviews = signal<ReviewsResponse | null>(null);
  editing = signal(false);       // writing a new review or editing mine
  myRating = 0;
  myText = '';
  reviewError = signal('');
  reviewBusy = signal(false);

  /** bar widths for the 5★…1★ distribution */
  bars = computed(() => {
    const r = this.reviews();
    if (!r) return [];
    return [5, 4, 3, 2, 1].map((s) => {
      const n = r.summary.distribution[String(s)] ?? 0;
      return { stars: s, n, pct: r.summary.count ? (n / r.summary.count) * 100 : 0 };
    });
  });

  /** how many more can still be added = stock minus what is already in the cart */
  available = computed(() => {
    const p = this.product();
    return p ? Math.max(0, p.stock - this.cart.inCart(p.id)) : 0;
  });

  ngOnInit() {
    this.api.getProduct(Number(this.id())).subscribe({
      next: (p) => this.product.set(p),
      error: () => this.error.set(true),
    });
    this.loadReviews();
  }

  loadReviews() {
    this.api.getReviews(Number(this.id())).subscribe((r) => this.reviews.set(r));
  }

  startReview() {
    const mine = this.reviews()?.my_review;
    this.myRating = mine?.rating ?? 0;
    this.myText = mine?.text ?? '';
    this.reviewError.set('');
    this.editing.set(true);
  }

  saveReview() {
    if (!this.myRating) return;
    const mine = this.reviews()?.my_review;
    this.reviewBusy.set(true);
    const call = mine
      ? this.api.updateReview(mine.id, this.myRating, this.myText.trim())
      : this.api.addReview(Number(this.id()), this.myRating, this.myText.trim());
    call.subscribe({
      next: () => this.afterReviewChange(),
      error: (e) => {
        this.reviewBusy.set(false);
        this.reviewError.set(apiError(e));
      },
    });
  }

  deleteReview() {
    const mine = this.reviews()?.my_review;
    if (mine) this.api.deleteReview(mine.id).subscribe(() => this.afterReviewChange());
  }

  /** spec label in the current language */
  specLabel(s: { en: string; ru: string }) {
    return this.i18n.lang() === 'ru' ? s.ru || s.en : s.en || s.ru;
  }

  /** demo specs store "Winter / Зима" in one value — show the part for the current language */
  specValue(s: { value: string }) {
    const parts = s.value.split(' / ');
    if (parts.length !== 2) return s.value;
    return this.i18n.lang() === 'ru' ? parts[1] : parts[0];
  }

  private afterReviewChange() {
    this.reviewBusy.set(false);
    this.editing.set(false);
    this.loadReviews();
    // refresh the product so the average on the page updates
    this.api.getProduct(Number(this.id())).subscribe((p) => this.product.set(p));
  }

  add() {
    const p = this.product();
    if (!p) return;
    if (!this.auth.isLoggedIn()) {
      this.router.navigate(['/login'], { queryParams: { next: this.router.url } });
      return;
    }
    this.busy.set(true);
    this.message.set('');
    this.addError.set('');
    this.cart.add(p.id, Math.min(this.qty(), this.available())).subscribe({
      next: () => {
        this.busy.set(false);
        this.message.set('ok');
        this.qty.set(1);
      },
      error: (e) => {
        this.busy.set(false);
        this.addError.set(apiError(e));
      },
    });
  }
}
