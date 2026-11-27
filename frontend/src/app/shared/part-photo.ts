import { Component, computed, input, signal } from '@angular/core';

import { PartIcon } from './part-icon';
import { SKU_PHOTOS } from './part-photos';
import { photoUrl } from './photo';

/**
 * Picture of a part:
 *  1. the product's own photo (uploaded in the admin panel), else
 *  2. an illustrative photo of this kind of part (frontend/public/parts/sku/<SKU>.jpg — free-licensed, see docs/PHOTO_CREDITS.md), else
 *  3. the category line icon.
 */
@Component({
  selector: 'app-part-photo',
  imports: [PartIcon],
  template: `
    @if (src() && failed() !== src()) {
      <img [src]="src()" [alt]="alt()" loading="lazy" [style.object-fit]="fit()" (error)="failed.set(src())" />
    } @else {
      <span class="ic"><app-part-icon [name]="product().category.icon" [size]="iconSize()" /></span>
    }
  `,
  styles: `
    :host { position: absolute; inset: 0; display: grid; place-items: center; background: var(--panel-2); }
    img { width: 100%; height: 100%; display: block; }
    .ic { color: var(--muted); opacity: .45; }
  `,
})
export class PartPhoto {
  product = input.required<{ sku: string; image?: string | null; category: { slug: string; icon: string } }>();
  alt = input('');
  iconSize = input(44);
  fit = input<'cover' | 'contain'>('cover');
  /** remembers which src failed to load (so another product's photo is tried again) */
  failed = signal('');
  src = computed(() => {
    const p = this.product();
    if (p.image) return photoUrl(p.image);
    return SKU_PHOTOS.has(p.sku) ? `parts/sku/${p.sku}.jpg` : '';
  });
}
