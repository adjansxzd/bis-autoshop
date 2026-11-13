import { Routes } from '@angular/router';

import { CartPage } from './pages/cart/cart';
import { Catalog } from './pages/catalog/catalog';
import { LoginPage } from './pages/login/login';
import { OrdersPage } from './pages/orders/orders';
import { ProductDetail } from './pages/product-detail/product-detail';
import { Search } from './pages/search/search';

export const routes: Routes = [
  { path: '', component: Catalog, title: 'AutoShop — Auto parts' },
  { path: 'product/:id', component: ProductDetail, title: 'AutoShop — Product' },
  { path: 'search', component: Search, title: 'AutoShop — Search' },
  { path: 'cart', component: CartPage, title: 'AutoShop — Cart' },
  { path: 'orders', component: OrdersPage, title: 'AutoShop — My orders' },
  { path: 'login', component: LoginPage, title: 'AutoShop — Sign in' },
  { path: '**', redirectTo: '' },
];
