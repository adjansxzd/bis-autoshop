import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, finalize, map, shareReplay, tap } from 'rxjs';

import { environment } from '../../environments/environment';
import { RegisterData, User } from './models';

const ACCESS_KEY = 'access_token';
const REFRESH_KEY = 'refresh_token';

interface Tokens {
  access: string;
  refresh?: string;
}

/**
 * Sign-in state.
 *  - login / register return two JWT tokens: access (2 h) and refresh (7 days)
 *  - authInterceptor adds the access token to every request
 *  - when access expires, the interceptor calls refresh() once and repeats the request,
 *    so the user stays signed in for up to 7 days without noticing
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  readonly user = signal<User | null>(null);
  readonly isLoggedIn = computed(() => this.user() !== null);

  constructor() {
    // deferred: the HTTP interceptor needs this service, so don't call the API while it is being created
    if (this.token) queueMicrotask(() => this.loadMe());
  }

  get token(): string | null {
    return read(ACCESS_KEY);
  }

  get refreshToken(): string | null {
    return read(REFRESH_KEY);
  }

  login(username: string, password: string): Observable<Tokens> {
    return this.http
      .post<Tokens>(`${this.base}/auth/login/`, { username, password })
      .pipe(tap((t) => this.start(t)));
  }

  /** POST /api/auth/register/ — the backend signs the new user in straight away. */
  register(data: RegisterData): Observable<User> {
    return this.http.post<Tokens & { user: User }>(`${this.base}/auth/register/`, data).pipe(
      tap((res) => this.start(res)),
      map((res) => res.user),
    );
  }

  /** "Sign in with Google": GET /api/auth/google/config/ → client ID ("" = switched off on the server) */
  googleClientId(): Observable<string> {
    return this.http.get<{ client_id: string }>(`${this.base}/auth/google/config/`).pipe(map((r) => r.client_id));
  }

  /** POST /api/auth/google/ — the server checks Google's ID token and returns our own JWT tokens */
  googleLogin(credential: string): Observable<User> {
    return this.http.post<Tokens & { user: User }>(`${this.base}/auth/google/`, { credential }).pipe(
      tap((res) => this.start(res)),
      map((res) => res.user),
    );
  }

  private refreshing: Observable<string> | null = null;

  /**
   * Exchange the refresh token for a new access token (used by the interceptor).
   * Several requests can fail with 401 at the same moment: they all share ONE refresh call,
   * because the server rotates refresh tokens (an old one can be used only once).
   */
  refresh(): Observable<string> {
    this.refreshing ??= this.http
      .post<Tokens>(`${this.base}/auth/refresh/`, { refresh: this.refreshToken })
      .pipe(
        tap((t) => {
          write(ACCESS_KEY, t.access);
          if (t.refresh) write(REFRESH_KEY, t.refresh);
        }),
        map((t) => t.access),
        finalize(() => (this.refreshing = null)),
        shareReplay(1),
      );
    return this.refreshing;
  }

  updateProfile(changes: Partial<User>): Observable<User> {
    return this.http.patch<User>(`${this.base}/auth/me/`, changes).pipe(tap((u) => this.user.set(u)));
  }

  changePassword(old_password: string, new_password: string): Observable<void> {
    return this.http.post<void>(`${this.base}/auth/password/`, { old_password, new_password });
  }

  logout() {
    // tell the server to blacklist the refresh token (best effort), then forget both tokens
    const refresh = this.refreshToken;
    if (refresh) this.http.post(`${this.base}/auth/logout/`, { refresh }).subscribe({ error: () => {} });
    write(ACCESS_KEY, null);
    write(REFRESH_KEY, null);
    this.user.set(null);
  }

  private start(tokens: Tokens) {
    write(ACCESS_KEY, tokens.access);
    if (tokens.refresh) write(REFRESH_KEY, tokens.refresh);
    this.loadMe();
  }

  private loadMe() {
    this.http.get<User>(`${this.base}/auth/me/`).subscribe({
      next: (u) => this.user.set(u),
      error: () => this.logout(), // both tokens invalid
    });
  }
}

function read(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function write(key: string, value: string | null) {
  try {
    value === null ? localStorage.removeItem(key) : localStorage.setItem(key, value);
  } catch {}
}
