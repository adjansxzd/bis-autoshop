import { Component, OnInit, computed, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { CartService, apiError } from '../../core/cart.service';
import { CartItem, DeliveryOptions } from '../../core/models';
import { GarageService } from '../../core/garage.service';
import { PartPhoto } from '../../shared/part-photo';
import { QtyStepper } from '../../shared/qty-stepper';
import { KztPipe, LocPipe, TPipe } from '../../shared/t.pipe';

/**
 * Cart + checkout.
 *  PATCH  /api/cart/items/{id}/  — change quantity (server rejects more than stock)
 *  DELETE /api/cart/items/{id}/  — remove
 *  POST   /api/orders/checkout/  — creates a new order, reduces stock, empties the cart
 */
@Component({
  selector: 'app-cart',
  imports: [FormsModule, RouterLink, PartPhoto, QtyStepper, TPipe, LocPipe, KztPipe],
  templateUrl: './cart.html',
  styleUrl: './cart.scss',
})
export class CartPage implements OnInit {
  cart = inject(CartService);
  auth = inject(AuthService);
  garage = inject(GarageService);
  private router = inject(Router);

  // checkout form
  delivery = signal<'courier' | 'pickup'>('courier');
  payment: 'card' | 'kaspi' | 'cash' = 'kaspi';
  address = '';
  phone = '';
  comment = '';
  options = signal<DeliveryOptions | null>(null);

  /** free-delivery progress bar (0–100 %) */
  freePct = computed(() => {
    const o = this.options();
    return o ? Math.min(100, (this.itemsTotal() / Number(o.free_from)) * 100) : 0;
  });
  /** true when every part in the cart fits the selected car */
  allFit = computed(() => {
    const items = this.cart.cart()?.items ?? [];
    return !!this.garage.car() && items.length > 0 && items.every((i) => this.garage.fits(i.product.compatible_cars));
  });

  error = signal('');
  itemErrors = signal<Record<number, string>>({});
  placing = signal(false);

  /** same rule as the backend: courier 1 500 ₸, free from 50 000 ₸; pickup free */
  itemsTotal = computed(() => Number(this.cart.cart()?.total ?? 0));
  deliveryCost = computed(() => {
    const o = this.options();
    if (!o || this.delivery() === 'pickup') return 0;
    return this.itemsTotal() >= Number(o.free_from) ? 0 : Number(o.courier_price);
  });
  toFree = computed(() => {
    const o = this.options();
    return o && this.delivery() === 'courier' ? Math.max(0, Number(o.free_from) - this.itemsTotal()) : 0;
  });

  ngOnInit() {
    this.cart.deliveryOptions().subscribe((o) => this.options.set(o));
  }

  constructor() {
    // pre-fill delivery details from the profile (My account)
    effect(() => {
      const u = this.auth.user();
      if (u) {
        if (!this.address) this.address = u.address ?? '';
        if (!this.phone) this.phone = u.phone ?? '';
      }
    });
  }

  setQty(item: CartItem, qty: number) {
    this.cart.setQuantity(item.id, qty).subscribe({
      next: () => this.itemErrors.update((m) => ({ ...m, [item.id]: '' })),
      error: (e) => this.itemErrors.update((m) => ({ ...m, [item.id]: apiError(e) })),
    });
  }

  remove(item: CartItem) {
    this.cart.remove(item.id).subscribe();
  }

  /** price label for a delivery option */
  deliveryCostFor(method: 'courier' | 'pickup') {
    const o = this.options();
    if (!o || method === 'pickup') return '';
    const free = this.itemsTotal() >= Number(o.free_from);
    return free ? '0 ₸' : Math.round(Number(o.courier_price)).toLocaleString('ru-RU') + ' ₸';
  }

  canPlace() {
    return !!this.phone.trim() && (this.delivery() === 'pickup' || !!this.address.trim());
  }

  checkout() {
    this.error.set('');
    if (!this.canPlace()) return;
    this.placing.set(true);
    this.cart
      .checkout({
        delivery_method: this.delivery(),
        payment_method: this.payment,
        shipping_address: this.address.trim(),
        phone: this.phone.trim(),
        comment: this.comment.trim(),
      })
      .subscribe({
        // the order page shows the confirmation and (for card) the payment step
        next: (order) => this.router.navigate(['/orders', order.id], { queryParams: { placed: 1 } }),
        error: (e) => {
          this.placing.set(false);
          this.error.set(apiError(e));
        },
      });
  }
}
