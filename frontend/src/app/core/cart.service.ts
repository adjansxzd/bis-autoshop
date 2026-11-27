import { HttpClient } from '@angular/common/http';
import { Injectable, computed, effect, inject, signal } from '@angular/core';
import { Observable, catchError, concatMap, from, of, tap, toArray } from 'rxjs';

import { environment } from '../../environments/environment';
import { AuthService } from './auth.service';
import { I18nService } from './i18n.service';
import { Cart, CartItem, CheckoutData, DeliveryOptions, Order, Page, Product } from './models';

const GUEST_KEY = 'guest_cart';
type GuestLine = { product: Product; quantity: number };

/**
 * Cart and orders (all checks are done again on the server):
 *  - quantity can never be more than product.stock
 *  - out-of-stock products cannot be added
 *  - every checkout creates a NEW order, so a user can have many orders
 *
 * Guest cart: without signing in, items are kept in the browser (localStorage).
 * After sign-in they are moved into the user's server cart (the server checks stock again).
 * Guest cart items have negative ids (-productId) so the cart page can tell them apart.
 */
@Injectable({ providedIn: 'root' })
export class CartService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private i18n = inject(I18nService);
  private base = environment.apiUrl;

  readonly cart = signal<Cart | null>(null);
  readonly count = computed(() => (this.cart()?.items ?? []).reduce((n, i) => n + i.quantity, 0));

  constructor() {
    // signed in → move the guest cart to the server, then load the server cart; signed out → show the guest cart
    effect(() => (this.auth.isLoggedIn() ? this.mergeGuestCart() : this.cart.set(this.guestCart())));
  }

  load() {
    if (!this.auth.isLoggedIn()) {
      this.cart.set(this.guestCart());
      return;
    }
    this.http.get<Cart>(`${this.base}/cart/`).subscribe((c) => this.cart.set(c));
  }

  // ---------- guest cart (browser only) ----------
  private readGuest(): GuestLine[] {
    try {
      return JSON.parse(localStorage.getItem(GUEST_KEY) || '[]');
    } catch {
      return [];
    }
  }

  private writeGuest(lines: GuestLine[]) {
    try {
      lines.length ? localStorage.setItem(GUEST_KEY, JSON.stringify(lines)) : localStorage.removeItem(GUEST_KEY);
    } catch {}
    this.cart.set(this.guestCart());
  }

  private guestCart(): Cart {
    const items: CartItem[] = this.readGuest().map((l) => ({
      id: -l.product.id,
      product: l.product,
      quantity: l.quantity,
      subtotal: String(Number(l.product.price) * l.quantity),
    }));
    return { id: 0, items, total: String(items.reduce((sum, i) => sum + Number(i.subtotal), 0)) };
  }

  /** after sign-in: add every guest line to the server cart (lines over the stock limit are skipped by the server) */
  private mergeGuestCart() {
    const lines = this.readGuest();
    if (!lines.length) return this.load();
    from(lines)
      .pipe(
        concatMap((l) =>
          this.http.post(`${this.base}/cart/items/`, { product_id: l.product.id, quantity: l.quantity }).pipe(catchError(() => of(null))),
        ),
        toArray(),
      )
      .subscribe(() => {
        try {
          localStorage.removeItem(GUEST_KEY);
        } catch {}
        this.load();
      });
  }

  /** How many of this product are already in the cart */
  inCart(productId: number): number {
    return this.cart()?.items.find((i) => i.product.id === productId)?.quantity ?? 0;
  }

  add(product: Product, quantity = 1): Observable<unknown> {
    if (!this.auth.isLoggedIn()) {
      const lines = this.readGuest();
      const line = lines.find((l) => l.product.id === product.id);
      const next = (line?.quantity ?? 0) + quantity;
      if (next > product.stock) return guestError(this.i18n.t('err.only_in_stock').replace('{n}', String(product.stock)));
      if (line) { line.quantity = next; line.product = product; } else lines.push({ product, quantity });
      this.writeGuest(lines);
      return of(null);
    }
    return this.http
      .post<CartItem>(`${this.base}/cart/items/`, { product_id: product.id, quantity })
      .pipe(tap(() => this.load()));
  }

  setQuantity(itemId: number, quantity: number): Observable<unknown> {
    if (itemId < 0) {
      const lines = this.readGuest();
      const line = lines.find((l) => l.product.id === -itemId);
      if (line) line.quantity = Math.max(1, Math.min(quantity, line.product.stock));
      this.writeGuest(lines);
      return of(null);
    }
    return this.http
      .patch<CartItem>(`${this.base}/cart/items/${itemId}/`, { quantity })
      .pipe(tap(() => this.load()));
  }

  remove(itemId: number): Observable<unknown> {
    if (itemId < 0) {
      this.writeGuest(this.readGuest().filter((l) => l.product.id !== -itemId));
      return of(null);
    }
    return this.http.delete<void>(`${this.base}/cart/items/${itemId}/`).pipe(tap(() => this.load()));
  }

  /** POST /api/orders/checkout/ — delivery (courier/pickup) and payment (card online/cash on delivery) */
  checkout(data: CheckoutData): Observable<Order> {
    return this.http.post<Order>(`${this.base}/orders/checkout/`, data).pipe(tap(() => this.load()));
  }

  deliveryOptions(): Observable<DeliveryOptions> {
    return this.http.get<DeliveryOptions>(`${this.base}/orders/delivery-options/`);
  }

  getOrder(id: number): Observable<Order> {
    return this.http.get<Order>(`${this.base}/orders/${id}/`);
  }

  /** demo online payment: new → paid (no card data is sent) */
  pay(id: number): Observable<Order> {
    return this.http.post<Order>(`${this.base}/orders/${id}/pay/`, {});
  }

  cancelOrder(id: number, reason: string): Observable<Order> {
    return this.http.post<Order>(`${this.base}/orders/${id}/cancel/`, { reason });
  }

  /** "Order again": puts the order's items back into the cart */
  reorder(id: number): Observable<{ added: string[]; skipped: string[] }> {
    return this.http.post<{ added: string[]; skipped: string[] }>(`${this.base}/orders/${id}/reorder/`, {}).pipe(tap(() => this.load()));
  }

  /** GET /api/orders/?q=&status=&page= — search by order number, product or SKU; filter by status */
  orders(filters: { q?: string; status?: string; page?: number } = {}): Observable<Page<Order>> {
    const params: Record<string, string> = {};
    if (filters.q) params['q'] = filters.q;
    if (filters.status) params['status'] = filters.status;
    if (filters.page && filters.page > 1) params['page'] = String(filters.page);
    return this.http.get<Page<Order>>(`${this.base}/orders/`, { params });
  }
}

/** same shape as an HTTP error, so apiError() shows the message */
function guestError(message: string): Observable<never> {
  return new Observable((sub) => sub.error({ error: { detail: message } }));
}

/** Turns a DRF error response into one readable line, e.g. "Only 8 in stock." */
export function apiError(err: any): string {
  const e = err?.error;
  if (!e || err?.status === 0) return document.documentElement.lang === 'ru' ? 'Сервер недоступен' : 'Server is not reachable';
  const ru = document.documentElement.lang === 'ru';
  // a crash page (HTML) or another non-JSON answer: show a short message, not the whole page
  if (typeof e === 'string' || err?.status >= 500) {
    return typeof e === 'string' && e.length < 200 && !e.trimStart().startsWith('<') ? e : ru ? 'Ошибка сервера, попробуйте ещё раз' : 'Server error, please try again';
  }
  const first = Object.values(e)[0] as any;
  return Array.isArray(first) ? String(first[0]) : String(first ?? 'Error');
}
