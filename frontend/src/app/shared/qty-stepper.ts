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
    .stepper {
      display: inline-flex; align-items: center; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; background: var(--panel);
      button { width: 38px; height: 40px; border: 0; background: none; color: var(--text); font-size: 18px; cursor: pointer;
        &:hover:not(:disabled) { background: var(--panel-2); } &:disabled { opacity: .3; cursor: default; } }
      input { width: 46px; height: 40px; border: 0; border-left: 1px solid var(--line); border-right: 1px solid var(--line);
        text-align: center; font: inherit; font-weight: 700; background: none; color: var(--text); outline: none; -moz-appearance: textfield;
        &::-webkit-outer-spin-button, &::-webkit-inner-spin-button { -webkit-appearance: none; } }
      &.small { button { width: 30px; height: 32px; } input { width: 38px; height: 32px; } }
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
