import { DatePipe } from '@angular/common';
import { KaspiQr } from '../../shared/kaspi-qr';
import { Component, OnInit, computed, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { I18nService } from '../../core/i18n.service';

import { CartService, apiError } from '../../core/cart.service';
import { Order, OrderStatus } from '../../core/models';
import { KztPipe, TPipe } from '../../shared/t.pipe';

const STEPS: OrderStatus[] = ['new', 'paid', 'shipped', 'delivered'];

/**
 * One order: confirmation after checkout, status timeline, demo payment, cancellation, "order again".
 *   GET  /api/orders/{id}/         POST /api/orders/{id}/pay/
 *   POST /api/orders/{id}/cancel/  POST /api/orders/{id}/reorder/
 */
@Component({
  selector: 'app-order-detail',
  imports: [RouterLink, FormsModule, DatePipe, TPipe, KztPipe, KaspiQr],
  templateUrl: './order-detail.html',
  styleUrl: './order-detail.scss',
})
export class OrderDetailPage implements OnInit {
  private cart = inject(CartService);
  private router = inject(Router);
  private i18n = inject(I18nService);
  id = input.required<string>();
  placed = input<string>(); // ?placed=1 → show "thank you" banner

  order = signal<Order | null>(null);
  showThanks = signal(false);
  notFound = signal(false);
  busy = signal(false);
  error = signal('');
  confirmCancel = signal(false);
  reason = '';
  reorderMsg = signal('');

  /** timeline: 4 steps; cancelled orders show where they stopped */
  steps = computed(() => {
    const o = this.order();
    if (!o) return [];
    const reached = new Map(o.events.map((e) => [e.status, e.created_at]));
    const current = o.status === 'cancelled' ? this.lastReached(o) : o.status;
    const idx = STEPS.indexOf(current);
    return STEPS
      // cash orders are paid on delivery: the "paid" step is optional, hide it if it never happened
      .filter((s) => !(s === 'paid' && o.payment_method === 'cash' && !reached.has('paid')))
      .map((s) => ({ status: s, done: STEPS.indexOf(s) <= idx, at: reached.get(s) ?? null }));
  });

  ngOnInit() {
    // "Thank you" only once, right after checkout: drop ?placed=1 so a reload doesn't show it again
    if (this.placed()) {
      this.showThanks.set(true);
      this.router.navigate([], { queryParams: {}, replaceUrl: true });
    }
    this.load();
  }

  /** "shipped" means "ready for pickup" when the customer collects the order */
  statusKey(o: Order, status: string) {
    return status === 'shipped' && o.delivery_method === 'pickup' ? 'status.ready' : 'status.' + status;
  }

  /** history notes are stored in English on the server — show known ones in the current language */
  noteText(note: string, by: string | null) {
    const t = (k: string) => this.i18n.t(k);
    const known: [string, string][] = [
      ['Order placed', 'note.placed'],
      ['Paid online', 'note.paid_online'],
      ['Paid with Kaspi QR', 'note.paid_kaspi'],
      ['Changed by the shop', 'note.by_shop'],
      ['Changed in the admin panel', 'note.by_shop'],
    ];
    for (const [prefix, key] of known) if (note.startsWith(prefix)) return t(key);
    if (note.startsWith('Cancelled by customer')) {
      const reason = note.replace('Cancelled by customer', '').replace(' · refund issued (demo)', '').replace(/^: /, '');
      return t('note.cancelled') + (reason ? ': ' + reason : '') + (note.includes('refund') ? ' · ' + t('note.refund') : '');
    }
    return note || (by ? t('od.by_' + by) : '');
  }

  load() {
    this.cart.getOrder(Number(this.id())).subscribe({
      next: (o) => this.order.set(o),
      error: () => this.notFound.set(true),
    });
  }

  pay() {
    this.run(this.cart.pay(Number(this.id())));
  }

  cancel() {
    this.run(this.cart.cancelOrder(Number(this.id()), this.reason.trim()), () => this.confirmCancel.set(false));
  }

  reorder() {
    this.cart.reorder(Number(this.id())).subscribe({
      next: (r) => (r.added.length ? this.router.navigate(['/cart']) : this.reorderMsg.set('none')),
      error: (e) => this.error.set(apiError(e)),
    });
  }

  private run(call: ReturnType<CartService['pay']>, after?: () => void) {
    this.busy.set(true);
    this.error.set('');
    call.subscribe({
      next: (o) => {
        this.order.set(o);
        this.busy.set(false);
        after?.();
      },
      error: (e) => {
        this.busy.set(false);
        this.error.set(apiError(e));
      },
    });
  }

  private lastReached(o: Order): OrderStatus {
    const seen = o.events.map((e) => e.status).filter((s) => s !== 'cancelled');
    return (seen[seen.length - 1] as OrderStatus) ?? 'new';
  }
}
