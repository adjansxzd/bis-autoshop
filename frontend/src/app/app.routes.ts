import { Routes } from '@angular/router';

import { Catalog } from './pages/catalog/catalog';
import { ProductDetail } from './pages/product-detail/product-detail';
import { Search } from './pages/search/search';

export const routes: Routes = [
  { path: '', component: Catalog, title: 'BIS AutoShop — Catalog' },
  { path: 'product/:id', component: ProductDetail, title: 'BIS AutoShop — Product' },
  { path: 'search', component: Search, title: 'BIS AutoShop — Search' },
  { path: '**', redirectTo: '' },
];
