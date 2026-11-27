import { Component, computed, inject, input } from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';
import qrcode from 'qrcode-generator';

/**
 * QR code for the demo "Kaspi QR" payment.
 * The code holds only a demo text (order number + amount), not a real payment link: no money can be paid with it.
 */
@Component({
  selector: 'app-kaspi-qr',
  template: `<div class="qr" [innerHTML]="svg()" role="img" [attr.aria-label]="'QR ' + text()"></div>`,
  styles: `
    .qr { width: 100%; max-width: 220px; aspect-ratio: 1; margin: 0 auto; padding: 10px; background: #fff; border-radius: 12px; }
    .qr ::ng-deep svg { width: 100%; height: 100%; display: block; }
  `,
})
export class KaspiQr {
  private sanitizer = inject(DomSanitizer);
  text = input.required<string>();
  svg = computed(() => {
    const qr = qrcode(0, 'M');
    qr.addData(this.text());
    qr.make();
    // SVG generated locally from our own text → safe to insert
    return this.sanitizer.bypassSecurityTrustHtml(qr.createSvgTag({ cellSize: 4, margin: 0, scalable: true }));
  });
}
