import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { Router, RouterLink } from '@angular/router';

import { CartService } from '../../core/cart.service';
import { Order } from '../../core/models';
import { KztPipe, TPipe } from '../../shared/t.pipe';

/** GET /api/orders/ — all orders of the logged-in user (a user can have many). */
@Component({
  selector: 'app-orders',
  imports: [RouterLink, FormsModule, DatePipe, TPipe, KztPipe],
  template: `
    <div class="container wrap">
      <h1>{{ 'orders.title' | t }} @if (total()) { <span>{{ total() }}</span> }</h1>

      <!-- search by order number / part name / SKU + status filter -->
      <div class="tools">
        <label class="search">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          <input type="text" [(ngModel)]="q" (ngModelChange)="onSearch()" [placeholder]="'orders.search' | t" />
          @if (q) { <button type="button" (click)="q = ''; reload()">✕</button> }
        </label>
        <div class="chips" role="group">
          @for (s of statuses; track s) {
            <button type="button" [class.on]="status === s" (click)="status = s; reload()">{{ (s ? 'status.' + s : 'orders.all') | t }}</button>
          }
        </div>
      </div>

      @if (loading() && !orders().length) {
        <p class="muted">{{ 'catalog.loading' | t }}</p>
      } @else if (!orders().length && (q || status)) {
        <div class="card empty"><p>{{ 'orders.nothing_found' | t }}</p></div>
      } @else if (!orders().length) {
        <div class="card empty"><p>{{ 'orders.empty' | t }}</p><a class="btn" routerLink="/">{{ 'cart.to_catalog' | t }}</a></div>
      } @else {
        <ul class="list">
          @for (o of orders(); track o.id) {
            <li class="card order" [routerLink]="['/orders', o.id]" tabindex="0" (keydown.enter)="open(o.id)">
              <header>
                <div><strong>{{ 'orders.order' | t }} #{{ o.id }}</strong><span class="muted"> · {{ o.created_at | date: 'dd.MM.yyyy HH:mm' }}</span></div>
                <span class="status" [attr.data-s]="o.status">{{ (o.status === 'shipped' && o.delivery_method === 'pickup' ? 'status.ready' : 'status.' + o.status) | t }}</span>
              </header>
              <table>
                @for (it of o.items; track it.id) {
                  <tr><td>{{ it.product_name }}</td><td class="q">× {{ it.quantity }}</td><td class="r">{{ it.subtotal | kzt }}</td></tr>
                }
              </table>
              <footer><span class="muted">{{ (o.delivery_method === 'pickup' ? 'co.pickup' : 'co.courier') | t }} · {{ (o.payment_method === 'card' ? 'co.card' : 'co.cash') | t }}</span>
                <span class="right">@if (o.can_pay) { <em class="pay">{{ 'od.not_paid' | t }}</em> } <strong>{{ o.total | kzt }}</strong> <span class="go">→</span></span></footer>
            </li>
          }
        </ul>
        @if (hasMore()) {
          <button class="btn ghost block more" (click)="loadMore()" [disabled]="loading()">{{ 'orders.more' | t }}</button>
        }
      }
    </div>
  `,
  styles: `
    .wrap { padding-top: 28px; padding-bottom: 56px; max-width: 860px; }
    h1 { font-size: 30px; font-weight: 800; margin: 0 0 20px; span { font-size: 16px; vertical-align: middle; background: var(--panel-2); padding: 3px 10px; border-radius: 999px; color: var(--muted); } }
    .muted { color: var(--muted); }
    .list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 14px; }
    .order { padding: 18px 20px; cursor: pointer; transition: border-color .15s; &:hover, &:focus-visible { border-color: var(--accent); outline: none; } }
    .right { display: flex; align-items: center; gap: 10px; } .go { color: var(--muted); }
    .pay { font-style: normal; font-size: 12px; font-weight: 700; color: var(--accent); }
    header, footer { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
    footer { padding-top: 12px; border-top: 1px solid var(--line); font-size: 14px; strong { font-size: 18px; } }
    table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; td { padding: 6px 0; } .q { color: var(--muted); width: 60px; } .r { text-align: right; font-weight: 600; width: 120px; } }
    .status { font-size: 12px; font-weight: 800; padding: 4px 10px; border-radius: 999px; background: var(--panel-2);
      &[data-s='new'] { background: var(--accent-soft); color: var(--accent); }
      &[data-s='delivered'], &[data-s='paid'], &[data-s='shipped'] { background: var(--ok-soft); color: var(--ok); }
      &[data-s='cancelled'] { color: var(--muted); text-decoration: line-through; } }
    .tools { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 16px; }
    .search { flex: 1; min-width: 220px; display: flex; align-items: center; gap: 8px; padding: 0 12px; height: 42px; color: var(--muted);
      background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
      &:focus-within { border-color: var(--accent); }
      input { flex: 1; min-width: 0; border: 0; outline: 0; background: none; color: var(--text); font: inherit; padding: 0; box-shadow: none; }
      button { background: none; border: 0; color: var(--muted); cursor: pointer; } }
    .chips { display: flex; gap: 6px; flex-wrap: wrap;
      button { border: 1px solid var(--line); background: var(--panel); color: var(--text); border-radius: 999px; padding: 7px 12px; font: inherit; font-size: 13px; font-weight: 600; cursor: pointer;
        &.on { background: var(--text); color: var(--panel); border-color: var(--text); } } }
    .more { margin-top: 14px; }
    .empty { padding: 40px; text-align: center; p { color: var(--muted); margin: 0 0 18px; } }
  `,
})
export class OrdersPage implements OnInit, OnDestroy {
  private cart = inject(CartService);
  private router = inject(Router);
  orders = signal<Order[]>([]);
  total = signal(0);
  hasMore = signal(false);
  loading = signal(true);

  q = '';
  status = '';
  readonly statuses = ['', 'new', 'paid', 'shipped', 'delivered', 'cancelled'];
  private page = 1;
  private timer: ReturnType<typeof setTimeout> | undefined;

  ngOnInit() {
    this.reload();
  }

  ngOnDestroy() {
    clearTimeout(this.timer);
  }

  open(id: number) {
    this.router.navigate(['/orders', id]);
  }

  /** wait until the user stops typing for 300 ms, then search */
  onSearch() {
    clearTimeout(this.timer);
    this.timer = setTimeout(() => this.reload(), 300);
  }

  reload() {
    this.page = 1;
    this.fetch(false);
  }

  loadMore() {
    this.page += 1;
    this.fetch(true);
  }

  private fetch(append: boolean) {
    this.loading.set(true);
    this.cart.orders({ q: this.q.trim(), status: this.status, page: this.page }).subscribe({
      next: (res) => {
        this.orders.set(append ? [...this.orders(), ...res.results] : res.results);
        this.total.set(res.count);
        this.hasMore.set(!!res.next);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }
}
