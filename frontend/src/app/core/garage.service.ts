import { Injectable, computed, signal } from '@angular/core';

import { CarModel, GarageCar } from './models';

/**
 * "My garage": the car chosen in the Year / Make / Model selector.
 * Remembered in the browser, so the shop always shows parts that fit this car.
 */
@Injectable({ providedIn: 'root' })
export class GarageService {
  readonly car = signal<GarageCar | null>(this.load());
  readonly label = computed(() => {
    const c = this.car();
    return c ? `${c.year} ${c.make} ${c.model}` : '';
  });

  set(car: GarageCar | null) {
    this.car.set(car);
    try {
      car ? localStorage.setItem('garage', JSON.stringify(car)) : localStorage.removeItem('garage');
    } catch {}
  }

  /** Does a product with these compatible cars fit the selected car? */
  fits(cars: CarModel[]): boolean {
    const c = this.car();
    return !!c && cars.some((x) => x.id === c.carId);
  }

  private load(): GarageCar | null {
    try {
      const raw = localStorage.getItem('garage');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }
}
