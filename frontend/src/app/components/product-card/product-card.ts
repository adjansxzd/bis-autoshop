import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { Product } from '../../core/models';
import { PartIcon } from '../../shared/part-icon';
import { KztPipe, LocPipe, TPipe } from '../../shared/t.pipe';

@Component({
  selector: 'app-product-card',
  imports: [RouterLink, PartIcon, TPipe, LocPipe, KztPipe],
  template: `
    @let p = product();
    <a class="card" [routerLink]="['/product', p.id]">
      <div class="visual">
        <app-part-icon [name]="p.category.icon" [size]="56" />
        <span class="sku">{{ p.sku }}</span>
      </div>
      <div class="body">
        <span class="brand">{{ p.brand.name }}</span>
        <h3>{{ p | loc: 'name' }}</h3>
        <div class="foot">
          <span class="price">{{ p.price | kzt }}</span>
          <span class="stock" [class.out]="!p.in_stock">
            {{ p.in_stock ? ('product.in_stock' | t) : ('product.out_of_stock' | t) }}
          </span>
        </div>
      </div>
    </a>
  `,
  styles: `
    .card {
      display: flex; flex-direction: column; height: 100%; text-decoration: none; color: var(--text);
      background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden;
      transition: border-color .15s, transform .15s;
      &:hover { border-color: var(--accent); transform: translateY(-2px); }
    }
    .visual {
      position: relative; display: grid; place-items: center; aspect-ratio: 16 / 10;
      color: var(--accent);
      background:
        repeating-linear-gradient(135deg, transparent 0 10px, color-mix(in srgb, var(--line) 45%, transparent) 10px 11px),
        var(--panel-2);
      border-bottom: 1px solid var(--line);
    }
    .sku {
      position: absolute; left: 10px; top: 10px; font-family: var(--mono); font-size: 11px;
      color: var(--muted); background: var(--bg); border: 1px solid var(--line); padding: 2px 6px; border-radius: 3px;
    }
    .body { padding: 14px 16px 16px; display: flex; flex-direction: column; gap: 6px; flex: 1; }
    .brand { font-family: var(--mono); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }
    h3 { margin: 0; font-size: 15px; font-weight: 500; line-height: 1.35; }
    .foot { margin-top: auto; padding-top: 10px; display: flex; justify-content: space-between; align-items: baseline; }
    .price { font-family: var(--display); font-size: 22px; font-weight: 600; }
    .stock { font-size: 12px; color: var(--ok); &.out { color: var(--danger); } }
  `,
})
export class ProductCard {
  product = input.required<Product>();
}
