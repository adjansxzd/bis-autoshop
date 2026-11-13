import { Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';

import { CartService } from '../../core/cart.service';
import { Order } from '../../core/models';
import { KztPipe, TPipe } from '../../shared/t.pipe';

/** GET /api/orders/ — all orders of the logged-in user (a user can have many). */
@Component({
  selector: 'app-orders',
  imports: [RouterLink, DatePipe, TPipe, KztPipe],
  template: `
    <div class="container wrap">
      <h1>{{ 'orders.title' | t }} @if (orders().length) { <span>{{ orders().length }}</span> }</h1>
      @if (loading()) {
        <p class="muted">{{ 'catalog.loading' | t }}</p>
      } @else if (!orders().length) {
        <div class="card empty"><p>{{ 'orders.empty' | t }}</p><a class="btn" routerLink="/">{{ 'cart.to_catalog' | t }}</a></div>
      } @else {
        <ul class="list">
          @for (o of orders(); track o.id) {
            <li class="card order">
              <header>
                <div><strong>{{ 'orders.order' | t }} #{{ o.id }}</strong><span class="muted"> · {{ o.created_at | date: 'dd.MM.yyyy HH:mm' }}</span></div>
                <span class="status" [attr.data-s]="o.status">{{ 'status.' + o.status | t }}</span>
              </header>
              <table>
                @for (it of o.items; track it.id) {
                  <tr><td>{{ it.product_name }}</td><td class="q">× {{ it.quantity }}</td><td class="r">{{ it.subtotal | kzt }}</td></tr>
                }
              </table>
              <footer><span class="muted">{{ o.shipping_address }} · {{ o.phone }}</span><strong>{{ o.total | kzt }}</strong></footer>
            </li>
          }
        </ul>
      }
    </div>
  `,
  styles: `
    .wrap { padding-top: 28px; padding-bottom: 56px; max-width: 860px; }
    h1 { font-size: 30px; font-weight: 800; margin: 0 0 20px; span { font-size: 16px; vertical-align: middle; background: var(--panel-2); padding: 3px 10px; border-radius: 999px; color: var(--muted); } }
    .muted { color: var(--muted); }
    .list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 14px; }
    .order { padding: 18px 20px; }
    header, footer { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
    footer { padding-top: 12px; border-top: 1px solid var(--line); font-size: 14px; strong { font-size: 18px; } }
    table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; td { padding: 6px 0; } .q { color: var(--muted); width: 60px; } .r { text-align: right; font-weight: 600; width: 120px; } }
    .status { font-size: 12px; font-weight: 800; padding: 4px 10px; border-radius: 999px; background: var(--panel-2);
      &[data-s='new'] { background: var(--accent-soft); color: var(--accent); }
      &[data-s='delivered'], &[data-s='paid'], &[data-s='shipped'] { background: var(--ok-soft); color: var(--ok); }
      &[data-s='cancelled'] { color: var(--muted); text-decoration: line-through; } }
    .empty { padding: 40px; text-align: center; p { color: var(--muted); margin: 0 0 18px; } }
  `,
})
export class OrdersPage implements OnInit {
  private cart = inject(CartService);
  orders = signal<Order[]>([]);
  loading = signal(true);

  ngOnInit() {
    this.cart.orders().subscribe({
      next: (page) => { this.orders.set(page.results); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }
}
