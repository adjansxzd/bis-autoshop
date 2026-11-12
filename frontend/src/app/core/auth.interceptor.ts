import { HttpInterceptorFn } from '@angular/common/http';

/** Adds "Authorization: Bearer <token>" to every API request when the user is logged in. */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  let token: string | null = null;
  try {
    token = localStorage.getItem('access_token');
  } catch {}
  return next(token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req);
};
