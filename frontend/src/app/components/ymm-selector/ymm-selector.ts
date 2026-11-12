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
    <div class="ymm">
      <h3>{{ 'ymm.title' | t }}</h3>
      @if (garage.car() && !editing()) {
        <div class="saved">
          <div>
            <span class="lbl">{{ 'ymm.saved' | t }}</span>
            <strong>{{ garage.label() }}</strong>
          </div>
          <div class="saved-actions">
            <button type="button" class="btn ghost" (click)="startEdit()">{{ 'ymm.change' | t }}</button>
            <button type="button" class="link" (click)="clear()">{{ 'ymm.clear' | t }}</button>
          </div>
        </div>
      } @else {
        <div class="fields">
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
          <button type="button" class="btn" [disabled]="!year" (click)="save()">{{ 'ymm.go' | t }}</button>
        </div>
      }
    </div>
  `,
  styles: `
    .ymm { background: var(--panel); color: var(--text); border-radius: 16px; padding: 20px; box-shadow: 0 10px 40px rgba(0,0,0,.25); }
    h3 { margin: 0 0 14px; font-size: 17px; }
    .fields { display: grid; grid-template-columns: 1fr 1fr .8fr auto; gap: 10px; select { height: 46px; } .btn { height: 46px; } }
    .saved { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;
      padding: 12px 14px; border-radius: 12px; background: var(--ok-soft); border: 1px solid var(--ok);
      .lbl { display: block; font-size: 12px; color: var(--ok); font-weight: 700; text-transform: uppercase; letter-spacing: .06em; }
      strong { font-size: 18px; } }
    .saved-actions { display: flex; align-items: center; gap: 10px; }
    .link { background: none; border: 0; color: var(--muted); font: inherit; cursor: pointer; text-decoration: underline; }
    @media (max-width: 760px) { .fields { grid-template-columns: 1fr 1fr; .btn { grid-column: 1 / -1; } } }
  `,
})
export class YmmSelector {
  garage = inject(GarageService);
  cars = input.required<CarModel[]>();
  picked = output<GarageCar | null>();

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
    this.picked.emit(car);
  }

  clear() {
    this.garage.set(null);
    this.make = ''; this.model = ''; this.year = null;
    this.picked.emit(null);
  }
}
