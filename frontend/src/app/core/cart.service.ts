import { HttpClient } from '@angular/common/http';
import { Injectable, computed, effect, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { environment } from '../../environments/environment';
import { AuthService } from './auth.service';
import { Cart, CartItem, Order, Page } from './models';

/**
 * Cart and orders (all checks are done again on the server):
 *  - quantity can never be more than product.stock
 *  - out-of-stock products cannot be added
 *  - every checkout creates a NEW order, so a user can have many orders
 */
@Injectable({ providedIn: 'root' })
export class CartService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private base = environment.apiUrl;

  readonly cart = signal<Cart | null>(null);
  readonly count = computed(() => (this.cart()?.items ?? []).reduce((n, i) => n + i.quantity, 0));

  constructor() {
    // load the cart when the user logs in, clear it on logout
    effect(() => (this.auth.isLoggedIn() ? this.load() : this.cart.set(null)));
  }

  load() {
    this.http.get<Cart>(`${this.base}/cart/`).subscribe((c) => this.cart.set(c));
  }

  /** How many of this product are already in the cart */
  inCart(productId: number): number {
    return this.cart()?.items.find((i) => i.product.id === productId)?.quantity ?? 0;
  }

  add(productId: number, quantity = 1): Observable<CartItem> {
    return this.http
      .post<CartItem>(`${this.base}/cart/items/`, { product_id: productId, quantity })
      .pipe(tap(() => this.load()));
  }

  setQuantity(itemId: number, quantity: number): Observable<CartItem> {
    return this.http
      .patch<CartItem>(`${this.base}/cart/items/${itemId}/`, { quantity })
      .pipe(tap(() => this.load()));
  }

  remove(itemId: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/cart/items/${itemId}/`).pipe(tap(() => this.load()));
  }

  checkout(shipping_address: string, phone: string): Observable<Order> {
    return this.http
      .post<Order>(`${this.base}/orders/checkout/`, { shipping_address, phone })
      .pipe(tap(() => this.load()));
  }

  orders(): Observable<Page<Order>> {
    return this.http.get<Page<Order>>(`${this.base}/orders/`);
  }
}

/** Turns a DRF error response into one readable line, e.g. "Only 8 in stock." */
export function apiError(err: any): string {
  const e = err?.error;
  if (!e) return 'Network error';
  if (typeof e === 'string') return e;
  const first = Object.values(e)[0] as any;
  return Array.isArray(first) ? String(first[0]) : String(first ?? 'Error');
}
