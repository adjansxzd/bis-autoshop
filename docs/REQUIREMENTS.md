# Requirements — BIS AutoShop

_Systems Analysis & Requirements · owner: Bazarbayeva Aidana (24B031667)_

## 1. Problem and goal

Buying car parts online is risky: the same "brake pads" exist in dozens of sizes, and buyers often order a part that does not fit their car, then lose time on returns. Small shops in Kazakhstan still take orders by phone and keep stock in spreadsheets, so they sell parts they no longer have.

**Goal:** a web shop where a driver picks their car once and, within 3 clicks, finds and orders a part that is guaranteed to fit, while the shop sees real stock and processes orders in one admin panel.

## 2. Stakeholders

| Stakeholder | Interest |
|---|---|
| Customer (driver) | Find a part that fits, pay quickly, follow the order, cancel if needed |
| Guest (not signed in) | Browse, search, fill a cart before deciding to register |
| Store manager | Keep the catalog and prices up to date, receive stock, move orders forward |
| Administrator | Manage users and roles, see sales analytics |
| Supplier | Delivers stock (recorded as stock receipts) |

## 3. Functional requirements

| ID | Requirement | Priority | Where |
|---|---|---|---|
| FR-01 | The user can pick a car (make → model → year); the catalog then shows only compatible parts | Must | Home page, "Your car" bar |
| FR-02 | Catalog with filters: category, brand, price range, in stock; sorting by price, newest, rating | Must | Home page |
| FR-03 | Global search over three entity types: parts (name, SKU, OEM number), categories, car models | Must | Header search → /search |
| FR-04 | Product page: photo or 3D model, price, stock, specs, OEM numbers, compatible cars, reviews | Must | /product/:id |
| FR-05 | Cart limited by real stock; a guest cart moves to the account after sign-in | Must | /cart |
| FR-06 | Checkout: courier (1 500 ₸, free from 50 000 ₸) or pickup; payment by Kaspi QR (demo), card (demo) or on delivery | Must | /cart |
| FR-07 | Order page with status timeline New → Paid → Shipped / Ready for pickup → Delivered, history, payment, cancellation (only new/paid), "order again" | Must | /orders/:id |
| FR-08 | Registration, sign-in, Sign in with Google, account page (profile, address, language, password, saved cars) | Must | /register, /login, /account |
| FR-09 | Reviews and ratings: only buyers of a part, once, 1–5 stars; managers moderate | Should | Product page, admin |
| FR-10 | Admin panel with roles: customer / manager / admin; CRUD for catalog; order status changes; users only for admin | Must | /admin/ |
| FR-11 | Warehouse: stock receipts from suppliers, balances, stock journal; stock never edited by hand | Must | Admin → Inventory |
| FR-12 | Sales analytics: revenue, orders by status, top parts, revenue by category, low stock | Should | Admin → Sales analytics |
| FR-13 | Full interface and server messages in English and Russian; light and dark theme | Must | Header switches |

## 4. Non-functional requirements

| ID | Requirement | How it is met |
|---|---|---|
| NFR-01 Security | Passwords hashed, JWT with short access token, brute-force limit, role checks on the server | docs/SECURITY.md |
| NFR-02 Data integrity | Stock can't go negative; every stock change has a journal entry; order and stock change in one DB transaction | `orders/services.py`, `inventory/services.py`, tests |
| NFR-03 Usability | Main task (find a fitting part and order it) in ≤ 3 clicks after picking the car; works on phones (390 px) | UI, manual test checklist |
| NFR-04 Localization | EN/RU for UI and API errors | `I18nService`, `locale/ru` |
| NFR-05 Performance | Catalog page answer < 300 ms on demo data; 3D viewer loaded only when opened | lazy `model-viewer` chunk |
| NFR-06 Maintainability | Automated tests for every business rule; API documented in Swagger | 100+ tests, /api/docs/ |
| NFR-07 Offline demo | Fonts, photos and 3D models are bundled; no CDN needed (except optional Google sign-in) | `@fontsource`, `public/parts`, `seed_models` |

## 5. Use cases

**UC-1 Find a part that fits**
Actor: guest or customer. Precondition: none.
1. The user selects make, model and year and presses "Show parts".
2. The system saves the car (in the browser; in the account if signed in) and shows only compatible parts.
3. The user narrows down with filters or search and opens a part.
Alternative: the part doesn't fit → the product page shows "Does not fit your …" in red.

**UC-2 Place and pay for an order**
Actor: customer. Precondition: cart not empty.
1. The customer opens the cart; quantities are limited by stock.
2. Chooses delivery (courier/pickup), payment (Kaspi QR/card/on delivery), phone and address.
3. The system checks stock again, creates the order, writes off stock in one transaction and shows the order page.
4. For Kaspi QR / card: the customer pays (demo) → status Paid.
Exceptions: not enough stock → error with the available amount (EN/RU); guest → asked to sign in, the cart is kept.

**UC-3 Cancel an order**
Actor: customer. Precondition: status New or Paid.
1. The customer presses "Cancel order", optionally gives a reason.
2. Stock returns to the warehouse; a paid order gets a refund note; history records who and when.
Exception: shipped orders can't be cancelled.

**UC-4 Process orders (shop side)**
Actor: manager. The manager opens Orders in the admin panel, filters by status and moves orders forward ("Mark as shipped"). Statuses never go backwards.

**UC-5 Receive stock**
Actor: manager. The manager posts a stock receipt from a supplier; balances and the journal update; Product.stock (cache) follows.

**UC-6 Analyse sales**
Actor: manager/admin. Opens "Sales analytics", picks a period (7/30/90 days/all time) and sees revenue, top parts and low stock.

## 6. User stories (with acceptance criteria)

- **As a driver** I want to see only parts for my 2020 Camry, **so that** I don't order the wrong one.
  _Given I picked Toyota Camry 2020, when I open the catalog, then every part shown lists Camry 2018–2024 in "Fits these cars"._
- **As a guest** I want to put parts into a cart before registering, **so that** I don't lose my choice.
  _Given I'm not signed in, when I add a part and later sign in, then the part is in my account's cart._
- **As a customer in Kazakhstan** I want to pay with Kaspi QR, **so that** I pay the way I'm used to.
  _Given an order with Kaspi QR, when I confirm the payment, then the status becomes Paid and the history says "Paid with Kaspi QR"._
- **As a customer** I want to cancel an order before shipping, **so that** I get my money back.
  _Given a paid order, when I cancel, then the stock goes back and the history shows "refund issued"._
- **As a manager** I want to see which parts are running out, **so that** I order more in time.
  _Given parts with stock ≤ 5, when I open Sales analytics, then they are listed under "Low stock"._

## 7. Main business process (order)

```
Customer                         System                                   Manager
   │ pick car, add parts           │                                         │
   │──────────────────────────────▶│ check stock, keep cart                  │
   │ checkout (delivery, payment)  │                                         │
   │──────────────────────────────▶│ BEGIN TRANSACTION                       │
   │                               │  create Order + OrderItems              │
   │                               │  write off stock + journal (sale)       │
   │                               │ COMMIT → status NEW                     │
   │ pay (Kaspi QR / card demo)    │                                         │
   │──────────────────────────────▶│ status PAID, paid_at, history           │
   │                               │────────────────────────────────────────▶│ sees order in admin
   │                               │◀────────────────────────────────────────│ "Mark as shipped"
   │                               │ status SHIPPED / READY FOR PICKUP       │
   │                               │◀────────────────────────────────────────│ "Delivered"
   │ (cancel while NEW/PAID)       │ stock returns + journal (return)        │
```
