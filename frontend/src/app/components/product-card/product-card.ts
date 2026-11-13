import { Component, computed, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { CartService, apiError } from '../../core/cart.service';
import { GarageService } from '../../core/garage.service';
import { Product } from '../../core/models';
import { PartIcon } from '../../shared/part-icon';
import { KztPipe, LocPipe, TPipe } from '../../shared/t.pipe';

@Component({
  selector: 'app-product-card',
  imports: [RouterLink, PartIcon, TPipe, LocPipe, KztPipe],
  template: `
    @let p = product();
    <article class="card pc">
      <a class="visual" [routerLink]="['/product', p.id]">
        <span class="ic"><app-part-icon [name]="p.category.icon" [size]="40" /></span>
        @if (garage.car()) {
          <span class="fit" [class.no]="!fits()">
            {{ fits() ? '✓ ' + ('product.fits_yours' | t) + ' ' + garage.car()!.model : ('product.not_fit' | t) + ' ' + garage.car()!.model }}
          </span>
        }
      </a>
      <div class="body">
        <div class="meta"><span>{{ p.brand.name }}</span><span class="mono">{{ p.sku }}</span></div>
        <a class="name" [routerLink]="['/product', p.id]">{{ p | loc: 'name' }}</a>
        <div class="stock" [class.out]="!p.in_stock" [class.low]="p.in_stock && p.stock <= 5">
          @if (!p.in_stock) { {{ 'product.out_of_stock' | t }} }
          @else if (p.stock <= 5) { {{ p.stock }} {{ 'product.left' | t }} }
          @else { {{ 'product.in_stock' | t }} }
        </div>
        <div class="foot">
          <span class="price">{{ p.price | kzt }}</span>
          <button type="button" class="btn add" [disabled]="!p.in_stock || maxed() || busy()" (click)="add()"
                  [title]="maxed() ? ('product.max_reached' | t) : ('product.add' | t)" [attr.aria-label]="'product.add' | t">
            @if (justAdded()) {
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 5 5 9-10"/></svg>
            } @else {
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h2l2.4 11.2a2 2 0 0 0 2 1.6h7.7a2 2 0 0 0 2-1.5L21 8H6.2"/><path d="M14 4v6M11 7h6"/></svg>
            }
          </button>
        </div>
        @if (error()) { <div class="error-text">{{ error() }}</div> }
      </div>
    </article>
  `,
  styles: `
    .pc { display: flex; flex-direction: column; height: 100%; overflow: hidden; transition: transform .15s, box-shadow .15s;
      &:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(16,24,40,.12); } }
    .visual { position: relative; display: grid; place-items: center; aspect-ratio: 16 / 9;
      background: linear-gradient(180deg, var(--panel-2), var(--panel)); border-bottom: 1px solid var(--line); }
    .ic { display: grid; place-items: center; width: 76px; height: 76px; border-radius: 50%; background: var(--accent-soft); color: var(--accent); }
    .fit { position: absolute; left: 10px; top: 10px; right: 10px; width: fit-content; font-size: 12px; font-weight: 700;
      padding: 4px 9px; border-radius: 999px; background: var(--ok-soft); color: var(--ok);
      &.no { background: var(--panel); color: var(--muted); border: 1px solid var(--line); } }
    .body { padding: 14px 16px 16px; display: flex; flex-direction: column; gap: 6px; flex: 1; }
    .meta { display: flex; justify-content: space-between; gap: 8px; font-size: 12px; color: var(--muted); font-weight: 600; .mono { font-size: 11px; } }
    .name { font-weight: 700; line-height: 1.3; text-decoration: none; color: var(--text); &:hover { color: var(--accent); } }
    .stock { font-size: 13px; font-weight: 600; color: var(--ok); &.low { color: var(--warn); } &.out { color: var(--danger); } }
    .foot { margin-top: auto; padding-top: 8px; display: flex; justify-content: space-between; align-items: center; }
    .price { font-size: 20px; font-weight: 800; letter-spacing: -0.02em; }
    .add { width: 44px; height: 40px; padding: 0; }
  `,
})
export class ProductCard {
  private cart = inject(CartService);
  private auth = inject(AuthService);
  private router = inject(Router);
  garage = inject(GarageService);

  product = input.required<Product>();
  busy = signal(false);
  justAdded = signal(false);
  error = signal('');

  fits = computed(() => this.garage.fits(this.product().compatible_cars));
  /** stock limit: button is disabled once the whole stock is in the cart */
  maxed = computed(() => this.cart.inCart(this.product().id) >= this.product().stock);

  add() {
    if (!this.auth.isLoggedIn()) {
      this.router.navigate(['/login'], { queryParams: { next: this.router.url } });
      return;
    }
    this.busy.set(true);
    this.error.set('');
    this.cart.add(this.product().id, 1).subscribe({
      next: () => {
        this.busy.set(false);
        this.justAdded.set(true);
        setTimeout(() => this.justAdded.set(false), 1200);
      },
      error: (e) => {
        this.busy.set(false);
        this.error.set(apiError(e));
      },
    });
  }
}
