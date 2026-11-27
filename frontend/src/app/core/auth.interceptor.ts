import { HttpErrorResponse, HttpInterceptorFn, HttpRequest } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';

import { AuthService } from './auth.service';
import { I18nService } from './i18n.service';

const withToken = (req: HttpRequest<unknown>, token: string | null) =>
  token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

/** Accept-Language: the server answers error messages in the site's language (EN/RU) */
const withLang = (req: HttpRequest<unknown>, lang: string) => req.clone({ setHeaders: { 'Accept-Language': lang } });

/**
 * 1) Adds "Authorization: Bearer <access token>" to every API request.
 * 2) Adds "Accept-Language: en|ru" so API error messages come in the site's language.
 * 3) If the server answers 401 (access token expired), gets a new one with the refresh token
 *    and repeats the request once. If that fails too, the user is signed out.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  req = withLang(req, inject(I18nService).lang());
  const isAuthCall = /\/auth\/(login|refresh|register|google|logout)\//.test(req.url);

  return next(withToken(req, auth.token)).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status !== 401 || isAuthCall || !auth.refreshToken) return throwError(() => err);
      return auth.refresh().pipe(
        switchMap((access) => next(withToken(req, access))),
        catchError((refreshErr) => {
          auth.logout();
          return throwError(() => refreshErr);
        }),
      );
    }),
  );
};
