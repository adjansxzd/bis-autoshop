import { Component, computed, input, output, signal } from '@angular/core';

/**
 * ★★★★☆ — shows a rating (read-only), or lets the user pick 1–5 when `editable` is true.
 */
@Component({
  selector: 'app-stars',
  template: `
    <span class="stars" [class.editable]="editable()" [style.font-size.px]="size()"
          [attr.role]="editable() ? 'radiogroup' : 'img'" [attr.aria-label]="label()">
      @for (i of [1, 2, 3, 4, 5]; track i) {
        @if (editable()) {
          <button type="button" [class.on]="i <= (hover() || value())" (mouseenter)="hover.set(i)" (mouseleave)="hover.set(0)"
                  (click)="valueChange.emit(i)" [attr.aria-label]="i + ' / 5'" [attr.aria-checked]="i === value()" role="radio">★</button>
        } @else {
          <i [class.on]="i <= full()" [class.half]="i === full() + 1 && hasHalf()">★</i>
        }
      }
    </span>
  `,
  styles: `
    .stars { display: inline-flex; gap: 1px; line-height: 1; color: var(--line); }
    i { font-style: normal; position: relative; }
    i.on, button.on { color: #f5a400; }
    i.half { background: linear-gradient(90deg, #f5a400 50%, var(--line) 50%); -webkit-background-clip: text; background-clip: text; color: transparent; }
    button { background: none; border: 0; padding: 0 2px; font: inherit; color: var(--line); cursor: pointer; transition: transform .1s;
      &:hover { transform: scale(1.15); } }
  `,
})
export class Stars {
  value = input<number>(0);
  size = input<number>(14);
  editable = input(false);
  valueChange = output<number>();
  hover = signal(0);

  full = computed(() => Math.floor(this.value() + 0.25));
  hasHalf = computed(() => this.value() - Math.floor(this.value()) >= 0.25 && this.value() - Math.floor(this.value()) < 0.75);
  label = computed(() => `${this.value()} / 5`);
}
