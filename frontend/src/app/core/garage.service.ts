import { HttpClient } from '@angular/common/http';
import { Injectable, computed, effect, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { environment } from '../../environments/environment';
import { AuthService } from './auth.service';
import { CarModel, GarageCar, SavedCar } from './models';

/**
 * "My garage".
 *  - car(): the car currently selected for shopping (filters the catalog). Kept in the browser.
 *  - saved(): cars stored in the user's account (GET /api/auth/garage/), same on every device.
 * Picking a car while signed in also saves it to the account.
 */
@Injectable({ providedIn: 'root' })
export class GarageService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private base = `${environment.apiUrl}/auth/garage/`;

  readonly car = signal<GarageCar | null>(this.loadLocal());
  readonly saved = signal<SavedCar[]>([]);
  readonly label = computed(() => {
    const c = this.car();
    return c ? `${c.year} ${c.make} ${c.model}` : '';
  });

  constructor() {
    effect(() => {
      if (this.auth.isLoggedIn()) {
        this.loadSaved();
      } else {
        this.saved.set([]);
      }
    });
  }

  /** Select a car for shopping (and remember it in the account when signed in). */
  set(car: GarageCar | null) {
    this.car.set(car);
    try {
      car ? localStorage.setItem('garage', JSON.stringify(car)) : localStorage.removeItem('garage');
    } catch {}
    if (car && this.auth.isLoggedIn() && !this.isSaved(car)) {
      this.save(car).subscribe({ error: () => {} });
    }
  }

  select(saved: SavedCar) {
    this.set({ carId: saved.car_id, make: saved.make, model: saved.model, year: saved.year });
  }

  isSaved(car: GarageCar) {
    return this.saved().some((s) => s.car_id === car.carId && s.year === car.year);
  }

  save(car: GarageCar): Observable<SavedCar> {
    return this.http
      .post<SavedCar>(this.base, { car_id: car.carId, year: car.year })
      .pipe(tap((s) => this.saved.update((list) => [s, ...list])));
  }

  remove(saved: SavedCar): Observable<void> {
    return this.http.delete<void>(`${this.base}${saved.id}/`).pipe(
      tap(() => {
        this.saved.update((list) => list.filter((s) => s.id !== saved.id));
        const c = this.car();
        if (c && c.carId === saved.car_id && c.year === saved.year) this.set(null);
      }),
    );
  }

  /** Does a product with these compatible cars fit the selected car? */
  fits(cars: CarModel[]): boolean {
    const c = this.car();
    return !!c && cars.some((x) => x.id === c.carId);
  }

  private loadSaved() {
    this.http.get<SavedCar[]>(this.base).subscribe((list) => {
      this.saved.set(list);
      // new device: no car picked yet → use the most recent saved one
      if (!this.car() && list.length) this.select(list[0]);
      // a car picked before signing in → keep it in the account too
      const c = this.car();
      if (c && !this.isSaved(c)) this.save(c).subscribe({ error: () => {} });
    });
  }

  private loadLocal(): GarageCar | null {
    try {
      const raw = localStorage.getItem('garage');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }
}
