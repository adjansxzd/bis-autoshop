import { Component, computed, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { GarageService } from '../../core/garage.service';
import { CarModel, GarageCar } from '../../core/models';
import { TPipe } from '../../shared/t.pipe';

/**
 * Year / Make / Model selector (the standard "fitment" search of auto parts shops).
 * Make → Model → Year narrows down to one CarModel row; the result is saved to "My garage".
 */
@Component({
  selector: 'app-ymm-selector',
  imports: [FormsModule, TPipe],
  template: `
    <div class="ymm" [class.saved]="garage.car() && !editing() && !addMode()">
      @if (garage.car() && !editing() && !addMode()) {
        <span class="lbl">{{ 'ymm.saved' | t }}:</span>
        <strong>{{ garage.label() }}</strong>
        <button type="button" class="btn ghost sm" (click)="startEdit()">{{ 'ymm.change' | t }}</button>
        <button type="button" class="link" (click)="clear()">{{ 'ymm.clear' | t }}</button>
      } @else {
        @if (!addMode()) { <span class="lbl">{{ 'ymm.title' | t }}</span> }
        <select [(ngModel)]="make" (ngModelChange)="model = ''; year = null" [attr.aria-label]="'ymm.make' | t">
          <option value="">{{ 'ymm.make' | t }}</option>
          @for (m of makes(); track m) { <option [value]="m">{{ m }}</option> }
        </select>
        <select [(ngModel)]="model" (ngModelChange)="year = null" [disabled]="!make" [attr.aria-label]="'ymm.model' | t">
          <option value="">{{ 'ymm.model' | t }}</option>
          @for (m of models(); track m) { <option [value]="m">{{ m }}</option> }
        </select>
        <select [(ngModel)]="year" [disabled]="!model" [attr.aria-label]="'ymm.year' | t">
          <option [ngValue]="null">{{ 'ymm.year' | t }}</option>
          @for (y of years(); track y) { <option [ngValue]="y">{{ y }}</option> }
        </select>
        <button type="button" class="btn" [disabled]="!year" (click)="save()">{{ (addMode() ? 'ymm.add' : 'ymm.go') | t }}</button>
        @if (editing()) { <button type="button" class="link" (click)="editing.set(false)">{{ 'reviews.cancel' | t }}</button> }
      }
    </div>
  `,
  styles: `
    /* one compact bar: [label] [Make] [Model] [Year] [Show parts] */
    .ymm { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; padding: 16px 20px; border-radius: var(--radius); background: var(--panel); }
    :host(.flat) .ymm { padding: 0; background: none; }
    .lbl { font-size: 15px; font-weight: 600; margin-right: 4px; }
    select { flex: 1; min-width: 140px; font-size: 14px; }
    .btn { flex-shrink: 0; }
    .saved { background: var(--ok-soft); .lbl { color: var(--ok); font-weight: 500; } strong { font-size: 16px; font-weight: 600; margin-right: auto; } }
    .link { background: none; border: 0; color: var(--muted); font: inherit; font-size: 14px; cursor: pointer; text-decoration: underline; }
    @media (max-width: 760px) { .lbl { flex-basis: 100%; } select { min-width: calc(50% - 6px); } .btn { flex: 1 1 100%; } .saved strong { flex-basis: 100%; } }
  `,
})
export class YmmSelector {
  garage = inject(GarageService);
  cars = input.required<CarModel[]>();
  picked = output<GarageCar | null>();
  /** account page: always show the pickers (to add another car) */
  addMode = input(false);

  editing = signal(false);
  make = '';
  model = '';
  year: number | null = null;

  makes = computed(() => [...new Set(this.cars().map((c) => c.make))].sort());
  models() {
    return [...new Set(this.cars().filter((c) => c.make === this.make).map((c) => c.model))].sort();
  }
  years() {
    const rows = this.cars().filter((c) => c.make === this.make && c.model === this.model);
    const ys = new Set<number>();
    rows.forEach((r) => { for (let y = r.year_to; y >= r.year_from; y--) ys.add(y); });
    return [...ys].sort((a, b) => b - a);
  }

  startEdit() {
    const c = this.garage.car();
    if (c) { this.make = c.make; this.model = c.model; this.year = c.year; }
    this.editing.set(true);
  }

  save() {
    const row = this.cars().find(
      (c) => c.make === this.make && c.model === this.model && this.year! >= c.year_from && this.year! <= c.year_to,
    );
    if (!row || !this.year) return;
    const car: GarageCar = { carId: row.id, make: row.make, model: row.model, year: this.year };
    this.garage.set(car);
    this.editing.set(false);
    if (this.addMode()) { this.make = ''; this.model = ''; this.year = null; }
    this.picked.emit(car);
  }

  clear() {
    this.garage.set(null);
    this.make = ''; this.model = ''; this.year = null;
    this.picked.emit(null);
  }
}
