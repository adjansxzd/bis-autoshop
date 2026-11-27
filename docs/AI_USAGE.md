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
| Week 15 | Redesign | Interface rebuilt from our Figma file (colours/fonts = Figma variables), simplified after review (one place for categories and the car, no slogans), 404 page, category photos from Wikimedia Commons (free licenses, credited) | _fill in_ | Frontend build; screenshots of catalog, product, cart, order, phone width |
| Week 15 | Demo Kaspi QR, guest cart, RU server errors | Kaspi QR payment step (demo), guest cart moved to the account after sign-in, Django translations for API errors + `Accept-Language` | _fill in_ | 108 tests pass (Kaspi payment, RU errors); manual run as guest → sign in → Kaspi pay |
| Week 15 | 3D view | `model-viewer` Photo/3D switch, `.glb` upload with validation; brake disc, oil filter and tire models generated in code (`seed_models/make_models.py`); spark plug and battery from Poly Pizza (CC-BY) | _fill in_ | 3D tests; models checked in the browser |
| Week 15 | Google sign-in, security, analytics | Google ID-token sign-in, brute-force limit, refresh-token rotation + sign-out blacklist, security headers; sales analytics (API + admin page) | _fill in_ | Security / Google (mocked) / analytics tests |
| Week 15 | Documentation | Drafts of REQUIREMENTS, ARCHITECTURE, SECURITY, TEST_PLAN | _each owner reviews and edits their document_ | — |

_Add a row every time AI helps with a feature._
