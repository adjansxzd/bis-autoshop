# API reference

Base URL: `http://127.0.0.1:8000/api`. Interactive docs (Swagger): **http://127.0.0.1:8000/api/docs/**

Auth: JWT. Get a token from `POST /api/auth/login/`, then send header `Authorization: Bearer <access>`.
Language: send `Accept-Language: ru` to get error messages in Russian (default English).

| Method | Endpoint | Who | What it does |
|---|---|---|---|
| GET | `/health/` | anyone | API status (frontend uses it for the "API connected" badge) |
| POST | `/auth/register/` | anyone | Create customer account `{username, email, password, password2, first_name?, last_name?, phone?}` → returns user + JWT tokens (signed in at once) |
| POST | `/auth/login/` | anyone | Returns `{access, refresh}` JWT tokens. Max 10 attempts/min per IP (429 after) |
| POST | `/auth/refresh/` | anyone | New access token **and a new refresh token** (rotation: the old refresh token stops working) |
| POST | `/auth/logout/` | anyone | Sign out `{refresh}` — the refresh token is blacklisted |
| GET | `/auth/google/config/` | anyone | Google OAuth client ID (`""` = Google sign-in switched off) |
| POST | `/auth/google/` | anyone | Sign in with Google `{credential}` (Google ID token) → `{user, access, refresh, created}` |
| GET / PATCH | `/auth/me/` | logged in | My profile: name, email, phone, delivery address, language (role can't be changed) |
| POST | `/auth/password/` | logged in | Change password `{old_password, new_password}` |
| GET / POST | `/auth/garage/` | logged in | My cars: list / save `{car_id, year}` (year must be in the model's range) |
| DELETE | `/auth/garage/{id}/` | logged in | Remove a saved car (only your own) |
| GET | `/products/` | anyone | Product list, paginated (12 per page) |
| GET | `/products/{id}/` | anyone | One product: photo, 3D model (`model_3d`, .glb), OEM numbers, specs, average rating |
| GET | `/products/price-range/?category=` | anyone | Lowest and highest price (for the price slider) |
| GET | `/products/{id}/reviews/` | anyone | Reviews + summary (average, count, 5★…1★), `can_review`, `my_review` |
| POST | `/products/{id}/reviews/` | buyers | Leave a review `{rating 1–5, text}` — only after buying the product, once |
| PATCH / DELETE | `/reviews/{id}/` | author (manager/admin may delete any) | Edit / delete a review |
| POST / PUT / PATCH / DELETE | `/products/…` | manager, admin | Product CRUD (admin panel) |
| GET | `/categories/` · `/brands/` · `/cars/` | anyone | Reference data for filters (CRUD for manager/admin) |
| GET | `/search/?q=` | anyone | Global search across **products, categories, car models** |
| GET / DELETE | `/cart/` | logged in | View / empty my cart |
| POST | `/cart/items/` | logged in | Add `{product_id, quantity}` (checks stock) |
| PATCH / DELETE | `/cart/items/{id}/` | logged in | Change quantity (rejected above stock) / remove |
| GET | `/orders/?q=&status=` | logged in | My orders (manager/admin see all); search by order number (`12` or `#12`), part name, SKU, address; filter by status |
| POST | `/orders/checkout/` | logged in | Cart → order `{delivery_method: courier\|pickup, payment_method: kaspi\|card\|cash, shipping_address (courier only), phone, comment}`; writes off stock; courier 1 500 ₸, free from 50 000 ₸ |
| GET | `/orders/delivery-options/` | anyone | Courier price, free-delivery threshold, pickup address |
| GET | `/orders/{id}/` | owner / staff | Order with items, totals, status history (`events`), `can_pay`, `can_cancel` |
| POST | `/orders/{id}/pay/` | owner | Demo online payment for Kaspi QR / card orders (status new → paid; no card data) |
| POST | `/orders/{id}/cancel/` | owner | Cancel own order `{reason?}` while new or paid; stock returns to the warehouse, paid → refund (demo) |
| POST | `/orders/{id}/reorder/` | owner | "Order again": items back into the cart (as many as in stock) |
| PATCH | `/orders/{id}/status/` | manager, admin | Change order status (cancelled → stock is returned) |
| GET | `/analytics/summary/?days=30` | manager, admin | Sales report: revenue, orders, average order, by status / payment / delivery, daily revenue, top parts, by category, low stock (`days` = 7, 30, 90 or 0 = all time) |

### Product filters
`/products/?category=brakes&brand=2&car=1&min_price=5000&max_price=40000&in_stock=true&search=pads&ordering=-price&page=2`

- `car` — **"Fits my car"**: only parts compatible with this car model id
- `ordering` — `price`, `-price`, `created_at`, `-created_at`, `name_en`, `-rating_avg` (best rated), `-rating_count` (most reviewed)
- `search` — also matches OEM numbers
