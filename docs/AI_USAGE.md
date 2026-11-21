# AI usage log

The course allows AI tools if we explain **what AI created, what we changed and how we tested it**.

| Date | Part | What AI generated | What we changed / decided | How it was tested |
|---|---|---|---|---|
| Week 10 | Project skeleton (Django + Angular) | Initial models, API endpoints, Angular catalog pages, seed data, tests | _fill in: e.g. chose the "Fits my car" idea, checked models against our ER diagram, renamed fields, changed design_ | `python manage.py test` (10 API tests pass), manual check in browser + Swagger |
| Week 11 | Stock limits, several orders, cart / checkout / orders pages, redesign | Stock check on quantity change, cancel → restock, cart and order pages, Year/Make/Model selector, new light design | _fill in_ | 16 API tests pass; manual run: 2 orders placed, quantity stops at stock |
| Week 12 | Admin panel with roles | Role → permissions sync (Managers group), product/order admin (filters, low-stock, actions), admin branding, "Admin panel" link, 12 admin tests; merged with Daulet's inventory app (admin actions use its order services) | _fill in_ | 60 tests pass; manual check with manager / admin / customer accounts |
| Week 13 | Customer account | Registration page + API (validation, auto sign-in), My account page (profile, address, password), My cars saved on the server, automatic token refresh, checkout pre-fill, 7 tests | _fill in_ | 67 tests pass; manual run: register → profile → 2 cars → new device restores car → checkout pre-filled |
| Week 14 | Catalog expansion | Product photos + seed photo folder, OEM numbers, specs, 12 categories / 22 cars / 64 parts, price range filter, reviews & ratings (buyers only), rating sort, order search, review moderation in admin, 11 tests | _fill in_ | 78 tests pass; manual run: price filter, buy → review → rating updates, search orders by number and part |
| Week 14 | Order process | Delivery (courier/pickup + fee rules) and payment choice at checkout, order page with timeline and history (OrderEvent), demo payment, customer cancellation with stock return, reorder, status history in admin, 9 tests | _fill in_ | 87 tests pass; manual run: card order → pay → cancel (refund); pickup + cash → manager ships → customer can't cancel |

_Add a row every time AI helps with a feature._
