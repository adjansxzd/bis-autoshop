# Architecture — BIS AutoShop

_Architecture & Security · owner: Salauatov Anuar (24B031995)_

## 1. Overview

Three-tier web application:

```
┌───────────────────────────┐   HTTPS / JSON (REST)   ┌──────────────────────────────┐   ORM   ┌──────────────┐
│ Angular 20 SPA            │ ──────────────────────▶ │ Django 5.2 + DRF             │ ──────▶ │ SQLite       │
│ pages, components,        │   JWT in Authorization  │ accounts · catalog · orders  │         │ (PostgreSQL  │
│ services (signals)        │   Accept-Language en/ru │ inventory · analytics        │ ◀────── │  in prod)    │
│ localhost:4200            │ ◀────────────────────── │ localhost:8000/api, /admin   │         └──────────────┘
└───────────────────────────┘                         └──────────────────────────────┘
          │ optional                                            │ media/ (photos, 3D models)
          ▼                                                     ▼
  Google Identity Services                              Swagger UI /api/docs/
```

## 2. Backend apps (Django)

| App | Owns | Key code |
|---|---|---|
| `accounts` | User with role (customer/manager/admin), saved cars, JWT auth, Google sign-in, sign-out | `models.User.save()` syncs role → staff flag + Managers group; `google.py` |
| `catalog` | Category, Brand, CarModel, Product (photo, 3D model, specs, OEM), Review | `views.ProductViewSet`, `global_search`, `reviews.py` |
| `orders` | Cart, Order, OrderItem, OrderEvent (history) | `services.py`: `place_order`, `change_order_status`, `pay_order`, `cancel_by_customer` |
| `inventory` (Daulet) | Warehouse, WarehouseStock (source of truth), Supplier, StockReceipt, StockMovement journal | `services.py`: atomic stock changes |
| `analytics` | No tables: sales report computed from orders | `services.report()`, admin page, `/api/analytics/summary/` |

**Business rules live in service functions**, not in views: the API, the admin panel and the tests all call the same `place_order` / `change_order_status`, so the rules (stock, status order, history) can't be bypassed.

## 3. Data model (main tables)

```
User 1─* GarageCar *─1 CarModel *─* Product *─1 Category
  │                                   │  └──*─1 Brand
  │ 1─1 Cart 1─* CartItem *─1─────────┤
  │ 1─* Order 1─* OrderItem *─1───────┤
  │        └─1─* OrderEvent           │
  │ 1─* Review *─1────────────────────┤
Warehouse 1─* WarehouseStock *─1──────┤
Supplier 1─* StockReceipt 1─* StockReceiptItem *─1 Product
StockMovement (journal: receipt / sale / return) → Warehouse, Product, Order?, StockReceipt?, User?
```

`Product.stock` is a read-only cache of the sum of `WarehouseStock`; it is never typed in by hand.

## 4. Frontend (Angular)

- **Standalone components + signals.** Pages: catalog, product, search, cart, order, orders, login, register, account, 404.
- **Core services:** `ApiService` (catalog), `CartService` (cart, guest cart in localStorage, checkout, orders), `AuthService` (JWT, refresh, Google), `GarageService` (selected car), `I18nService` (EN/RU), `ThemeService` (light/dark).
- **HTTP interceptor:** adds `Authorization: Bearer …` and `Accept-Language`; on 401 refreshes the token once (one shared refresh call) and repeats the request.
- **Heavy parts load lazily:** the 3D viewer (`@google/model-viewer`, three.js) is a separate chunk loaded only when a customer opens "3D".

## 5. Key flows

**Sign-in:** `POST /auth/login/` → access (2 h) + refresh (7 days). Refresh tokens rotate; sign-out blacklists the refresh token.

**Checkout:** `POST /orders/checkout/` → `place_order()` in one DB transaction: re-check stock (`SELECT … FOR UPDATE` style via atomic updates), create order lines, write off stock with journal entries, log "Order placed". Any error → nothing is saved.

**Status change:** `change_order_status()` allows only forward moves; cancel only from New/Paid and returns stock with a "return" journal entry; every change writes an `OrderEvent`.

## 6. Deployment view (planned)

| Part | Option |
|---|---|
| Backend | Render / PythonAnywhere, `gunicorn`, `DJANGO_DEBUG=0`, `HTTPS=1`, PostgreSQL |
| Frontend | `ng build` → Netlify / Vercel (static files) |
| Media | server disk or S3-compatible storage |
| Secrets | environment variables (`DJANGO_SECRET_KEY`, `GOOGLE_CLIENT_ID`), never in git |

## 7. Technology choices

| Choice | Why |
|---|---|
| Django + DRF | Admin panel and ORM out of the box, mature auth, easy tests |
| JWT (SimpleJWT) | Stateless API for a separate SPA; rotation + blacklist for sign-out |
| Angular 20 signals | Typed, structured SPA; the course stack |
| SQLite → PostgreSQL | Zero setup for development; one setting to switch |
| Service layer | One place for business rules used by API, admin and tests |
