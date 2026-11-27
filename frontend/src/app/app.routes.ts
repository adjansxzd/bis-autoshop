import { Routes } from '@angular/router';

import { AccountPage } from './pages/account/account';
import { CartPage } from './pages/cart/cart';
import { Catalog } from './pages/catalog/catalog';
import { LoginPage } from './pages/login/login';
import { OrderDetailPage } from './pages/order-detail/order-detail';
import { OrdersPage } from './pages/orders/orders';
import { RegisterPage } from './pages/register/register';
import { ProductDetail } from './pages/product-detail/product-detail';
import { Search } from './pages/search/search';
import { NotFoundPage } from './pages/not-found/not-found';

export const routes: Routes = [
  { path: '', component: Catalog, title: 'AutoShop — Auto parts' },
  { path: 'product/:id', component: ProductDetail, title: 'AutoShop — Product' },
  { path: 'search', component: Search, title: 'AutoShop — Search' },
  { path: 'cart', component: CartPage, title: 'AutoShop — Cart' },
  { path: 'orders', component: OrdersPage, title: 'AutoShop — My orders' },
  { path: 'orders/:id', component: OrderDetailPage, title: 'AutoShop — Order' },
  { path: 'login', component: LoginPage, title: 'AutoShop — Sign in' },
  { path: 'register', component: RegisterPage, title: 'AutoShop — Create account' },
  { path: 'account', component: AccountPage, title: 'AutoShop — My account' },
  { path: '**', component: NotFoundPage, title: 'AutoShop — Page not found' },
];
