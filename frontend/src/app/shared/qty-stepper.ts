import { Component, input, output } from '@angular/core';

/**
 * − [ 2 ] +   quantity picker that can never go below 1 or above `max` (the product's stock).
 */
@Component({
  selector: 'app-qty-stepper',
  template: `
    <div class="stepper" [class.small]="small()">
      <button type="button" (click)="change(value() - 1)" [disabled]="disabled() || value() <= 1" aria-label="Decrease">−</button>
      <input type="number" [value]="value()" [min]="1" [max]="max()" [disabled]="disabled()"
             (change)="change(+$any($event.target).value, $any($event.target))" aria-label="Quantity" />
      <button type="button" (click)="change(value() + 1)" [disabled]="disabled() || value() >= max()" aria-label="Increase">+</button>
    </div>
  `,
  styles: `
    /* Figma: "Quantity stepper" */
    .stepper {
      display: inline-flex; align-items: center; border-radius: var(--radius); background: var(--panel-2); padding: 0 4px;
      button { width: 40px; height: 48px; border: 0; background: none; color: var(--text); font-size: 18px; font-weight: 600; cursor: pointer; border-radius: 8px;
        &:hover:not(:disabled) { color: var(--accent); } &:disabled { opacity: .3; cursor: default; } }
      input { width: 44px; height: 48px; min-height: 0; padding: 0; border: 0; text-align: center; font: inherit; font-size: 14px; font-weight: 600; background: none; color: var(--text);
        outline: none; box-shadow: none !important; -moz-appearance: textfield;
        &::-webkit-outer-spin-button, &::-webkit-inner-spin-button { -webkit-appearance: none; } }
      &.small { button { width: 32px; height: 36px; } input { width: 34px; height: 36px; } }
    }
  `,
})
export class QtyStepper {
  value = input.required<number>();
  max = input<number>(99);
  small = input(false);
  disabled = input(false);
  valueChange = output<number>();

  change(next: number, el?: HTMLInputElement) {
    // clamp to 1..max — the stock limit
    const clamped = Math.max(1, Math.min(this.max(), Math.floor(next) || 1));
    if (el) el.value = String(clamped);
    if (clamped !== this.value()) this.valueChange.emit(clamped);
  }
}
