import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';
import { CartService, apiError } from '../../core/cart.service';
import { CartItem, Order } from '../../core/models';
import { PartIcon } from '../../shared/part-icon';
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
  imports: [FormsModule, RouterLink, PartIcon, QtyStepper, TPipe, LocPipe, KztPipe],
  templateUrl: './cart.html',
  styleUrl: './cart.scss',
})
export class CartPage {
  cart = inject(CartService);
  auth = inject(AuthService);

  address = '';
  phone = '';
  error = signal('');
  itemErrors = signal<Record<number, string>>({});
  placing = signal(false);
  placed = signal<Order | null>(null);

  setQty(item: CartItem, qty: number) {
    this.cart.setQuantity(item.id, qty).subscribe({
      next: () => this.itemErrors.update((m) => ({ ...m, [item.id]: '' })),
      error: (e) => this.itemErrors.update((m) => ({ ...m, [item.id]: apiError(e) })),
    });
  }

  remove(item: CartItem) {
    this.cart.remove(item.id).subscribe();
  }

  checkout() {
    this.error.set('');
    if (!this.address.trim() || !this.phone.trim()) return;
    this.placing.set(true);
    this.cart.checkout(this.address.trim(), this.phone.trim()).subscribe({
      next: (order) => {
        this.placing.set(false);
        this.placed.set(order);
        this.address = '';
      },
      error: (e) => {
        this.placing.set(false);
        this.error.set(apiError(e));
      },
    });
  }
}
