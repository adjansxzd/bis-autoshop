import { Component, computed, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { CartService, apiError } from '../../core/cart.service';
import { GarageService } from '../../core/garage.service';
import { Product } from '../../core/models';
import { PartPhoto } from '../../shared/part-photo';
import { Stars } from '../../shared/stars';
import { KztPipe, LocPipe, TPipe } from '../../shared/t.pipe';

@Component({
  selector: 'app-product-card',
  imports: [RouterLink, PartPhoto, Stars, TPipe, LocPipe, KztPipe],
  template: `
    @let p = product();
    <article class="pc">
      <a class="visual" [routerLink]="['/product', p.id]" tabindex="-1">
        <app-part-photo [product]="p" [alt]="p | loc: 'name'" />
        @if (p.model_3d) { <span class="b3d" [title]="'model3d.has' | t">3D</span> }
      </a>
      <div class="body">
        <div class="meta">{{ p.brand.name }}&nbsp;&nbsp;/&nbsp;&nbsp;{{ p.sku }}</div>
        <a class="name" [routerLink]="['/product', p.id]">{{ p | loc: 'name' }}</a>
        @if (p.rating_count) {
          <div class="rating"><app-stars [value]="p.rating_avg ?? 0" [size]="13" /> <span>{{ p.rating_avg }} ({{ p.rating_count }})</span></div>
        }
        <!-- fitment line only when the list is not already filtered by the car -->
        @if (garage.car() && showFit()) {
          <div class="fit" [class.no]="!fits()">{{ fits() ? '✓ ' + ('product.fits_yours' | t) : ('product.not_fit' | t) }} {{ garage.car()!.model }}</div>
        }
        <div class="stock" [class.out]="!p.in_stock" [class.low]="p.in_stock && p.stock <= 5">
          @if (!p.in_stock) { {{ 'product.out_of_stock' | t }} }
          @else if (p.stock <= 5) { {{ 'product.only' | t }} {{ p.stock }} {{ 'product.left' | t }} }
          @else { {{ 'product.in_stock' | t }} }
        </div>
        <div class="foot">
          <span class="price">{{ p.price | kzt }}</span>
          <button type="button" class="btn add" [disabled]="!p.in_stock || maxed() || busy()" (click)="add()"
                  [title]="maxed() ? ('product.max_reached' | t) : ''">
            @if (justAdded()) { ✓ {{ 'product.added_short' | t }} }
            @else if (!p.in_stock) { {{ 'product.sold_out' | t }} }
            @else { {{ 'product.add' | t }} }
          </button>
        </div>
        @if (error()) { <div class="error-text">{{ error() }}</div> }
      </div>
    </article>
  `,
  styles: `
    /* Figma: "Product card" component */
    .pc { display: flex; flex-direction: column; height: 100%; padding: 10px; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius);
      transition: box-shadow .15s, border-color .15s; &:hover { box-shadow: var(--shadow-hover); } }
    .visual { position: relative; display: grid; place-items: center; aspect-ratio: 4 / 3; border-radius: 8px; overflow: hidden; background: var(--panel-2); }
    .body { padding: 12px 4px 2px; display: flex; flex-direction: column; gap: 6px; flex: 1; }
    .b3d { position: absolute; top: 8px; right: 8px; padding: 3px 7px; border-radius: 6px; background: var(--text); color: var(--panel); font-size: 11px; font-weight: 700; letter-spacing: .04em; }
    .meta { font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .02em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .name { font-size: 15px; font-weight: 600; line-height: 1.35; text-decoration: none; color: var(--text); &:hover { color: var(--accent); } }
    .rating { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--warn); &.none { color: var(--muted); font-size: 12px; } }
    .fit { font-size: 12px; font-weight: 500; color: var(--ok); &.no { color: var(--muted); } }
    .stock { font-size: 12px; font-weight: 500; color: var(--ok); &.low { color: var(--warn); } &.out { color: var(--danger); } }
    .foot { margin-top: auto; padding-top: 10px; display: flex; justify-content: space-between; align-items: center; gap: 10px; }
    .price { font-size: 19px; font-weight: 700; letter-spacing: -0.01em; white-space: nowrap; }
    .add { min-height: 40px; padding: 0 14px; font-size: 13px; }
  `,
})
export class ProductCard {
  private cart = inject(CartService);
  private auth = inject(AuthService);
  private router = inject(Router);
  garage = inject(GarageService);

  product = input.required<Product>();
  /** false when the catalog is already filtered by the selected car (then every card would say "fits") */
  showFit = input(true);
  busy = signal(false);
  justAdded = signal(false);
  error = signal('');

  fits = computed(() => this.garage.fits(this.product().compatible_cars));
  /** stock limit: button is disabled once the whole stock is in the cart */
  maxed = computed(() => this.cart.inCart(this.product().id) >= this.product().stock);

  add() {
    this.busy.set(true);
    this.error.set('');
    this.cart.add(this.product(), 1).subscribe({
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
