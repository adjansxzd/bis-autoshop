# Security — BIS AutoShop

_Architecture & Security · owner: Salauatov Anuar (24B031995)_

## 1. What we protect

| Asset | Threat | Measure | Test |
|---|---|---|---|
| Customer accounts | Password guessing | Max **10 sign-in / registration attempts per minute per IP** (`ScopedRateThrottle`, scope `auth`) → HTTP 429 | `SecurityTests.test_login_is_rate_limited` |
| Passwords | Leak of the database | Django PBKDF2 hashing; strong-password validators (length, common, numeric, similar to name) | `AccountTests` (weak password rejected) |
| Sessions (JWT) | Stolen token | Access token lives 2 h; refresh tokens **rotate** (each can be used once) and are **blacklisted on sign-out** | `test_refresh_token_rotates_and_old_one_dies`, `test_logout_blacklists_refresh_token` |
| Roles | Customer acting as manager | Role is read-only in the API; `User.save()` derives staff/superuser flags from the role; staff-only endpoints use `IsAdminUser` | `test_customer_cannot_change_own_role`, `AdminPanelRoleTests`, analytics tests |
| Orders | Seeing / cancelling someone else's order | Querysets filtered by `request.user`; services check the owner again | `test_cannot_cancel_after_shipping_or_someone_elses_order` |
| Stock & money | Ordering more than in stock, double write-off, status going backwards | Server-side checks in `place_order` in one transaction; status rules in `change_order_status` | inventory + order tests |
| Blocked users | Signing in after being blocked | `is_active = False` → login and Google sign-in refused | `test_blocked_user_cannot_sign_in` |
| Google sign-in | Forged token | Token signature, audience (our client ID) and expiry checked with Google's keys (`google-auth`); only verified emails | `GoogleSignInTests.test_invalid_token_is_rejected` |
| File uploads | Malicious "photo" / "3D model" | `ImageField` (Pillow checks it's an image); `.glb` must start with `glTF` and be ≤ 10 MB | `test_only_binary_gltf_is_accepted` |
| Browser | Clickjacking, MIME sniffing, referrer leaks | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin` | `test_security_headers` |
| Payments | Card data theft | **No card data is collected at all** — card and Kaspi QR are demo payments; the QR holds only order number and amount | design |
| Secrets | Keys in git | `.env` is git-ignored; production refuses to start with the dev `SECRET_KEY` | settings |

## 2. Production settings (`DJANGO_DEBUG=0`)

- `DJANGO_SECRET_KEY` must be set (the server won't start with the dev key).
- `HTTPS=1` turns on: redirect to HTTPS, secure cookies, HSTS (30 days), proxy SSL header.
- `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` list only our domains.
- Run `python manage.py check --deploy` before going live.

## 3. Roles and permissions

| Action | Guest | Customer | Manager | Admin |
|---|:-:|:-:|:-:|:-:|
| Browse, search, guest cart | ✓ | ✓ | ✓ | ✓ |
| Place / pay / cancel own orders, reviews (buyers only) | | ✓ | ✓ | ✓ |
| Admin panel: catalog, orders, warehouse, analytics | | | ✓ | ✓ |
| Users and roles | | | | ✓ |

## 4. Known limits (honest list)

- The Django admin login itself has no rate limit (only API sign-in has). For production: add `django-axes` or put the admin behind a VPN.
- JWT tokens are kept in `localStorage` (simple for an SPA); an XSS bug could read them. Angular escapes all output by default and we never insert user HTML; the only `bypassSecurityTrustHtml` is for the QR code SVG we generate ourselves.
- SQLite is fine for the demo; production should use PostgreSQL.
