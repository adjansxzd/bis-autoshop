import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { environment } from '../../environments/environment';
import { User } from './models';

const TOKEN_KEY = 'access_token';

/**
 * Minimal sign-in so the cart and orders can be used (they need a logged-in user).
 * Login: POST /api/auth/login/ → JWT access token, sent with every request by authInterceptor.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  readonly user = signal<User | null>(null);
  readonly isLoggedIn = computed(() => this.user() !== null);

  constructor() {
    if (this.token) this.loadMe();
  }

  get token(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  }

  login(username: string, password: string): Observable<{ access: string }> {
    return this.http.post<{ access: string }>(`${this.base}/auth/login/`, { username, password }).pipe(
      tap((res) => {
        try {
          localStorage.setItem(TOKEN_KEY, res.access);
        } catch {}
        this.loadMe();
      }),
    );
  }

  logout() {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch {}
    this.user.set(null);
  }

  private loadMe() {
    this.http.get<User>(`${this.base}/auth/me/`).subscribe({
      next: (u) => this.user.set(u),
      error: () => this.logout(), // expired or invalid token
    });
  }
}
