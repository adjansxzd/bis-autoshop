# Test plan and report — BIS AutoShop

_Testing, Analytics & Integration · owner: Altynbekova Aruzhan (24B031630)_

## 1. Strategy

| Level | What | Tool | How to run |
|---|---|---|---|
| Unit / service | Business rules: stock, statuses, delivery fee, payments, roles, analytics numbers | Django `TestCase` | `cd backend` → `python manage.py test` |
| API integration | Every endpoint the site uses, with JWT, EN/RU errors | DRF `APITestCase` | same command |
| Admin panel | Role access, actions ("Mark as shipped", "Cancel"), filters | Django test client | same command |
| UI / end-to-end | The main process in a real browser, both languages, both themes, phone width | Manual checklist below (run before each demo) | `start_backend.bat` + `start_frontend.bat` |

Test data: `python manage.py seed` (12 categories, 22 car models, 69 parts, 3 suppliers, demo users `admin` / `manager` / `customer`, password `demo12345`, local only). Tests create their own database and media folder, so they never touch real data.

## 2. Automated tests (108)

| Area | Test class | Count | Covers |
|---|---|---|---|
| Shop flow | `orders.ShopFlowTests` | 31 | catalog, filters, "fits my car", 3-entity search, cart limits, checkout, several orders per user, stock write-off, own orders only |
| Order process | `orders.OrderProcessTests` | 12 | delivery fee & free delivery, pickup, **Kaspi QR** and card demo payment, cancel + stock return + refund note, status rules, history, reorder, **RU error messages** |
| Catalog | `catalog.CatalogTests`, `Product3DModelTests` | 13 | photos, specs, OEM search, price range, rating sort, reviews (buyers only, once), **3D models** |
| Accounts | `accounts.AccountTests`, `AdminPanelRoleTests` | 19 | registration validation, profile, password change, saved cars, role → admin access |
| Google sign-in | `accounts.GoogleSignInTests` | 4 | off without client ID, new user = customer, existing email = same account, forged token rejected |
| Security | `accounts.SecurityTests` | 6 | brute-force limit (429), sign-out blacklist, refresh rotation, security headers, blocked user, role can't be self-changed |
| Warehouse | `inventory.*` (Daulet) | 20 | receipts, suppliers, journal always matches balances, no double write-off/return |
| Analytics | `analytics.AnalyticsTests` | 3 | staff only, revenue = orders (cancelled excluded), top parts, admin page |

**Result (26 Nov 2026): 108 tests, all passed** (`Ran 108 tests … OK`).

## 3. Manual end-to-end checklist (before the demo)

| # | Step | Expected | ✓ |
|---|---|---|---|
| 1 | Open the site, switch EN ↔ RU and light ↔ dark | All texts change; no English left in RU | |
| 2 | Pick Toyota → Camry → 2020 → "Show parts" | Only compatible parts; checkbox "Only parts for Camry" | |
| 3 | Filter: category Brakes, price slider, sort by rating | List and count update | |
| 4 | Search "camry", then "04465" (OEM) | Parts, categories and cars found; OEM finds the pad | |
| 5 | Open "Ventilated brake disc" → **3D** | Model rotates with the mouse | |
| 6 | As a guest add 2 parts → Cart → "Sign in to check out" as `customer` | After sign-in the 2 parts are in the cart | |
| 7 | Try quantity above stock | Stepper stops; server error in the current language | |
| 8 | Checkout: courier + **Kaspi QR** | Order page with QR; "I have paid (demo)" → status Paid, history updated | |
| 9 | Cancel the order with a reason | Status Cancelled, refund note, stock back | |
| 10 | Admin as `manager`: Orders → "Mark as shipped" on a new order | Customer's timeline shows Shipped | |
| 11 | Admin → Inventory → post a stock receipt | Balance and journal grow | |
| 12 | Admin → **Sales analytics** (7 / 30 days) | Revenue, top parts, low stock match the orders | |
| 13 | Phone width (F12 → device toolbar, 390 px) | Header, cart and product page usable | |
| 14 | Open a wrong URL `/abc` | "Page not found" page | |

## 4. Defects found and fixed during the project (examples)

| Defect | Fix |
|---|---|
| Admin "history" inline broke the order form | Shown as a read-only field |
| A rejected "add to cart" (more than in stock) left an empty cart line that crashed checkout | The line is removed; checkout ignores empty lines (regression test) |
| Stale catalog answer overwrote a newer one when moving the price slider fast | Previous request is cancelled |
| Search page category chips didn't filter | Link to `/?category=…` |
| Server errors were English in the RU interface | `Accept-Language` + Russian translations |
| Two parallel token refreshes signed the user out (after refresh rotation) | One shared refresh call |

## 5. Integration points checked

Frontend ↔ API (health badge "API connected"), JWT refresh, Google Identity Services (mocked in tests, manual with a real client ID), media files (photos, `.glb`), lazy 3D chunk.
