<div align="center">

# 🔧 BIS AutoShop

**Online shop for auto parts & accessories: product catalog, cart and order processing**

_Basics of Information Systems (INFT3107) · KBTU · Group project · Topic #11 "Online Shop"_

![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django)
![DRF](https://img.shields.io/badge/REST_API-DRF-a30000)
![Angular](https://img.shields.io/badge/Angular-20-DD0031?logo=angular)
![SQLite](https://img.shields.io/badge/DB-SQLite-003B57?logo=sqlite)
![Status](https://img.shields.io/badge/status-Week_10_·_technical_foundation-ffb000)

</div>

## Aim

Build a web store where a driver selects their car and, within 3 clicks, finds and orders a part that is guaranteed to fit it.

## The problem we solve

Buying car parts online is risky: the same "brake pads" come in dozens of sizes, and buyers often order a part that doesn't fit their car. **AutoShop links every product to compatible car models** ("Fits my car"), so the customer only sees parts that fit.

## Objectives

1. Catalog with categories, brands and filters, with a **"Fits my car"** compatibility filter
2. User registration and login with roles: **customer, manager, admin**
3. Cart and checkout that store orders in the database and reduce stock
4. Admin panel: CRUD for products, categories, cars and order status
5. Global search across 3 entity types (parts, categories, car models)
6. Full interface in **English and Russian**

## Team

| Student ID | Name | Role |
|---|---|---|
| 24B031667 | Bazarbayeva Aidana | Systems Analysis & Requirements |
| 24B032154 | Konakbayev Daulet | Data & Database |
| 24B031630 | Altynbekova Aruzhan | Testing, Analytics & Integration |
| 24B031632 | Alzhanov Adilzhan | Application & Development |
| 24B031995 | Salauatov Anuar | Architecture & Security |

## Architecture

```
┌──────────────────────┐    HTTP / JSON    ┌───────────────────────┐   Django ORM   ┌──────────┐
│  Angular 20 (SPA)    │ ───────────────▶ │  Django REST API      │ ─────────────▶ │  SQLite  │
│  localhost:4200      │ ◀─────────────── │  localhost:8000/api   │ ◀───────────── │  db file │
│  ApiService (HTTP)   │   JWT in header   │  CORS · JWT · Swagger │                └──────────┘
└──────────────────────┘                   └───────────────────────┘
```

**How data moves (example, "Fits my car")**: the user picks *Toyota Camry* → Angular calls `GET /api/products/?car=1` → Django filters `Product ⋈ product_compatible_cars` → returns JSON → Angular renders the product cards.

### Data model (main tables)

`User (role)` · `Category` · `Brand` · `CarModel` · `Product` · `Product ↔ CarModel` (compatibility, M:N) · `Cart` · `CartItem` · `Order` · `OrderItem`

## Project structure

```
bis-autoshop/
├── backend/                 Django project
│   ├── config/              settings, root URLs
│   ├── accounts/            custom User with roles, register/login/me
│   ├── catalog/             products, categories, brands, car models, search, seed command
│   └── orders/              cart, checkout, orders + API tests
├── frontend/                Angular app
│   └── src/app/
│       ├── core/            ApiService (all HTTP calls), models, i18n + theme services
│       ├── components/      header, product card
│       ├── pages/           catalog, product detail, search
│       └── shared/          pipes (translate, price), icons
└── docs/                    API reference, AI usage log
```

## How to run

**Requirements:** Python 3.10+, Node.js 20+

### Windows (quick)
1. Double-click `setup_backend.bat` (first time only: installs packages, creates the DB, adds demo data)
2. Double-click `start_backend.bat` → API at http://127.0.0.1:8000/api/
3. Double-click `start_frontend.bat` → site at http://localhost:4200

### Manual (any OS)
```bash
# backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed           # demo data: 69 parts, 22 car models, 3 suppliers, 3 demo users
python manage.py runserver

# frontend (new terminal)
cd frontend
npm install
npm start
```

**After every `git pull`** (new packages / tables / demo data may have arrived):
```bash
cd backend && pip install -r requirements.txt && python manage.py migrate && python manage.py seed
cd ../frontend && npm install
```

| URL | What |
|---|---|
| http://localhost:4200 | Website |
| http://127.0.0.1:8000/api/docs/ | Swagger: all API endpoints, try them live |
| http://127.0.0.1:8000/admin/ | Admin panel (manager / admin only) |

`python manage.py seed` creates **local demo accounts** (`admin`, `manager`, `customer`, password printed in the console). They exist only in your local database; never use them on a deployed server.

## Order process (start to finish)

1. **Cart → checkout:** works for guests too (the cart is kept in the browser and moves to the account after sign-in). Choose **courier** (1 500 ₸, free from 50 000 ₸, with a progress bar) or **pickup** (free), payment **Kaspi QR (demo)**, **card online (demo)** or **on delivery**, phone, comment. Totals update live.
2. **Order page** (`/orders/{id}`): "Thank you" confirmation, **status timeline** New → Paid → Shipped (Ready for pickup) → Delivered, items, delivery & payment details, full **history** (who changed what and when).
3. **Payment:** **Kaspi QR** — the order page shows a QR code and the Kaspi steps, "I have paid (demo)" marks it paid; **card** — "Pay" button. Both are demo payments: no card data, no real money, the QR holds only the order number and amount.
4. **Cancellation:** the customer can cancel while the order is new or paid (reason optional); items go back to the warehouse, a paid order is marked refunded. After shipping, cancelling is blocked.
5. **Shop side:** managers move orders forward in the admin panel (statuses only go forward; history is recorded).
6. **Order again:** puts a past order's items back into the cart.

## Catalog

- **12 categories, 24 brands, 22 car models, 69 parts, 3 suppliers** (demo data in `backend/catalog/management/commands/seed_data.py`).
- **Photos:** upload in the admin panel, or put files named by SKU into `backend/catalog/seed_images/` (`BR-001.jpg`) and run `python manage.py seed`. Parts without their own photo show an illustrative photo of the same kind of part (64 of 69; free-licensed, see [docs/PHOTO_CREDITS.md](docs/PHOTO_CREDITS.md)); the rest show a category icon.
- **Product page:** description, OEM numbers, specs table, compatible cars.
- **3D view:** parts with a 3D model (brake disc, oil filter, tire — made in code by our team; spark plug, battery — free CC-BY models) get a **Photo / 3D** switch: rotate with the mouse, zoom with the wheel. Managers upload `.glb` files in the admin panel. The 3D library loads only when opened.
- **Filters:** category, brand, **price range** (slider + inputs), in stock, "Fits my car"; sort by price, newest, **best rated**, most reviewed.
- **Ratings & reviews:** only customers who **bought** a part can review it (once; edit/delete own). Average stars on cards; 5★…1★ breakdown on the product page; managers moderate reviews in the admin panel.
- **My orders:** search by order number, part name or SKU, filter by status.

## Customer account

- **Sign in with Google:** one button on Sign in / Create account (setup: [docs/GOOGLE_SIGN_IN.md](docs/GOOGLE_SIGN_IN.md)); a new Google user becomes a customer.
- **Registration** (`/register`): checks passwords match and are strong, email/username are free, phone format; the customer is signed in straight away.
- **My account** (`/account`): name, email, phone, **default delivery address** (pre-filled at checkout), language, change password.
- **My cars**: cars saved in the account, available on any device; one of them is "shopping for this car" and filters the catalog.
- **Stays signed in**: the access token lives 2 hours; the site renews it automatically with the refresh token (7 days, rotated on every renewal; "Sign out" revokes it).
- **Languages:** the whole interface **and the server's error messages** are in English or Russian.

## Admin panel & roles

| | Customer | Manager | Admin |
|---|:-:|:-:|:-:|
| Open the admin panel (`/admin/`) | ✗ | ✓ | ✓ |
| Products, categories, brands, car models (CRUD) | ✗ | ✓ | ✓ |
| Orders: change status, "Mark as shipped", cancel (only new/paid; stock returns to the warehouse) | ✗ | ✓ | ✓ |
| Warehouse: post stock receipts, view balances and the stock journal | ✗ | ✓ | ✓ |
| **Sales analytics**: revenue, orders by status, top parts, revenue by category, low stock (7 / 30 / 90 days) | ✗ | ✓ | ✓ |
| Users and roles | ✗ | ✗ | ✓ |

The **role field is the single source of truth**: changing a user's role automatically updates their admin access (`User.save()` → staff flag + "Managers" group). Products list has search, filters (stock / category / brand), low-stock highlighting and inline price editing. Stock itself is never typed in by hand: it changes only through the **warehouse** (stock receipts in, sales out, returns back), and every change is written to the stock journal. Staff see an "Admin panel" link in the shop header.

## API

Full list: [docs/API.md](docs/API.md) · live Swagger at `/api/docs/`

```
GET  /api/products/?car=1&category=brakes     catalog with filters
GET  /api/search/?q=toyota                    search in products + categories + cars
POST /api/auth/register/  ·  /api/auth/login/ JWT auth
POST /api/cart/items/  ·  /api/orders/checkout/
```

## Testing

```bash
cd backend
python manage.py test
```
**108 automated tests**, all passing. Full table and the manual demo checklist: [docs/TEST_PLAN.md](docs/TEST_PLAN.md).

They cover the **order process** (delivery fees, pickup, Kaspi QR and card demo payments, cancellation with stock return, status rules, history, reorder, RU error messages), the **catalog** (photos, 3D models, specs, OEM search, price range, rating sort, reviews), **accounts** (registration, profile, password, saved cars, Google sign-in), **security** (brute-force limit, sign-out, token rotation, security headers, blocked users, roles), the **admin panel** and **roles**, the **warehouse** (receipts, suppliers, journal always matches balances) and **sales analytics**.

## Documentation

| Document | Owner |
|---|---|
| [Requirements, use cases, user stories](docs/REQUIREMENTS.md) | Systems Analysis — Aidana |
| [Architecture](docs/ARCHITECTURE.md) · [Security](docs/SECURITY.md) | Architecture & Security — Anuar |
| [Test plan and report](docs/TEST_PLAN.md) | Testing & Analytics — Aruzhan |
| [API reference](docs/API.md) · [Google sign-in setup](docs/GOOGLE_SIGN_IN.md) · [Photo and 3D credits](docs/PHOTO_CREDITS.md) | Development — Adilzhan |

## AI usage

We used AI as a coding assistant. What it generated, what we changed and how we tested it is logged in [docs/AI_USAGE.md](docs/AI_USAGE.md).
