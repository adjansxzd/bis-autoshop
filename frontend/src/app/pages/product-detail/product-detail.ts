import { Component, OnInit, computed, inject, input, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { CartService, apiError } from '../../core/cart.service';
import { GarageService } from '../../core/garage.service';
import { Product } from '../../core/models';
import { PartIcon } from '../../shared/part-icon';
import { QtyStepper } from '../../shared/qty-stepper';
import { KztPipe, LocPipe, TPipe } from '../../shared/t.pipe';

@Component({
  selector: 'app-product-detail',
  imports: [RouterLink, PartIcon, QtyStepper, TPipe, LocPipe, KztPipe],
  templateUrl: './product-detail.html',
  styleUrl: './product-detail.scss',
})
export class ProductDetail implements OnInit {
  private api = inject(ApiService);
  private auth = inject(AuthService);
  private router = inject(Router);
  cart = inject(CartService);
  garage = inject(GarageService);
  id = input.required<string>(); // from route /product/:id

  product = signal<Product | null>(null);
  error = signal(false);
  qty = signal(1);
  busy = signal(false);
  message = signal('');
  addError = signal('');

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
