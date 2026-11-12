# API reference

Base URL: `http://127.0.0.1:8000/api`. Interactive docs (Swagger): **http://127.0.0.1:8000/api/docs/**

Auth: JWT. Get a token from `POST /api/auth/login/`, then send header `Authorization: Bearer <access>`.

| Method | Endpoint | Who | What it does |
|---|---|---|---|
| GET | `/health/` | anyone | API status (frontend uses it for the "API connected" badge) |
| POST | `/auth/register/` | anyone | Create customer account `{username, email, password}` |
| POST | `/auth/login/` | anyone | Returns `{access, refresh}` JWT tokens |
| POST | `/auth/refresh/` | anyone | New access token from refresh token |
| GET / PATCH | `/auth/me/` | logged in | My profile |
| GET | `/products/` | anyone | Product list, paginated (12 per page) |
| GET | `/products/{id}/` | anyone | One product |
| POST / PUT / PATCH / DELETE | `/products/…` | manager, admin | Product CRUD (admin panel) |
| GET | `/categories/` · `/brands/` · `/cars/` | anyone | Reference data for filters (CRUD for manager/admin) |
| GET | `/search/?q=` | anyone | Global search across **products, categories, car models** |
| GET / DELETE | `/cart/` | logged in | View / empty my cart |
| POST | `/cart/items/` | logged in | Add `{product_id, quantity}` (checks stock) |
| PATCH / DELETE | `/cart/items/{id}/` | logged in | Change quantity (rejected above stock) / remove |
| GET | `/orders/` | logged in | My orders (manager/admin see all) |
| POST | `/orders/checkout/` | logged in | Cart → order `{shipping_address, phone}`; reduces stock |
| PATCH | `/orders/{id}/status/` | manager, admin | Change order status (cancelled → stock is returned) |

### Product filters
`/products/?category=brakes&brand=2&car=1&min_price=5000&max_price=40000&in_stock=true&search=pads&ordering=-price&page=2`

- `car` — **"Fits my car"**: only parts compatible with this car model id
- `ordering` — `price`, `-price`, `created_at`, `-created_at`, `name_en`
