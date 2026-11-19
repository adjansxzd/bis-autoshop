import { Component, OnInit, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { apiError } from '../../core/cart.service';
import { GarageService } from '../../core/garage.service';
import { I18nService } from '../../core/i18n.service';
import { CarModel, SavedCar, User } from '../../core/models';
import { YmmSelector } from '../../components/ymm-selector/ymm-selector';
import { TPipe } from '../../shared/t.pipe';

/**
 * My account:
 *  - personal details + default delivery address   PATCH /api/auth/me/
 *  - My cars (saved in the account)                 GET/POST/DELETE /api/auth/garage/
 *  - change password                                POST /api/auth/password/
 */
@Component({
  selector: 'app-account',
  imports: [FormsModule, RouterLink, YmmSelector, TPipe],
  templateUrl: './account.html',
  styleUrl: './account.scss',
})
export class AccountPage implements OnInit {
  private api = inject(ApiService);
  private router = inject(Router);
  auth = inject(AuthService);
  garage = inject(GarageService);
  i18n = inject(I18nService);

  cars = signal<CarModel[]>([]);

  // profile form (a copy, so typing doesn't change the header until saved)
  form: Partial<User> = {};
  profileState = signal<'idle' | 'saving' | 'saved'>('idle');
  profileErrors = signal<Record<string, string>>({});

  // password form
  oldPassword = '';
  newPassword = '';
  pwState = signal<'idle' | 'saving' | 'saved'>('idle');
  pwError = signal('');

  constructor() {
    // fill the form once the profile has loaded
    effect(() => {
      const u = this.auth.user();
      if (u && !this.form.username) this.form = { ...u };
    });
  }

  ngOnInit() {
    if (!this.auth.token) {
      this.router.navigate(['/login'], { queryParams: { next: '/account' } });
      return;
    }
    this.api.getCars().subscribe((c) => this.cars.set(c));
  }

  saveProfile() {
    this.profileState.set('saving');
    this.profileErrors.set({});
    const { first_name, last_name, email, phone, address, preferred_language } = this.form;
    this.auth.updateProfile({ first_name, last_name, email, phone, address, preferred_language }).subscribe({
      next: (u) => {
        this.profileState.set('saved');
        if (u.preferred_language) this.i18n.setLang(u.preferred_language);
        setTimeout(() => this.profileState.set('idle'), 2000);
      },
      error: (e) => {
        this.profileState.set('idle');
        const out: Record<string, string> = {};
        for (const [k, v] of Object.entries(e?.error ?? {})) out[k] = Array.isArray(v) ? v.join(' ') : String(v);
        this.profileErrors.set(out);
      },
    });
  }

  isCurrent(s: SavedCar) {
    const c = this.garage.car();
    return !!c && c.carId === s.car_id && c.year === s.year;
  }

  removeCar(s: SavedCar) {
    this.garage.remove(s).subscribe();
  }

  changePassword() {
    this.pwState.set('saving');
    this.pwError.set('');
    this.auth.changePassword(this.oldPassword, this.newPassword).subscribe({
      next: () => {
        this.pwState.set('saved');
        this.oldPassword = '';
        this.newPassword = '';
      },
      error: (e) => {
        this.pwState.set('idle');
        this.pwError.set(apiError(e));
      },
    });
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/']);
  }
}
