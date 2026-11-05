import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { Brand, CarModel, Category, Page, Product, ProductQuery, SearchResult } from './models';

/** All HTTP calls to the Django backend live here, so components never build URLs themselves. */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  health(): Observable<{ status: string }> {
    return this.http.get<{ status: string }>(`${this.base}/health/`);
  }

  getProducts(query: ProductQuery = {}): Observable<Page<Product>> {
    let params = new HttpParams();
    // only send filters that are actually set
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '' && value !== false) {
        params = params.set(key, String(value));
      }
    });
    return this.http.get<Page<Product>>(`${this.base}/products/`, { params });
  }

  getProduct(id: number): Observable<Product> {
    return this.http.get<Product>(`${this.base}/products/${id}/`);
  }

  getCategories(): Observable<Category[]> {
    return this.http.get<Category[]>(`${this.base}/categories/`);
  }

  getBrands(): Observable<Brand[]> {
    return this.http.get<Brand[]>(`${this.base}/brands/`);
  }

  getCars(): Observable<CarModel[]> {
    return this.http.get<CarModel[]>(`${this.base}/cars/`);
  }

  search(q: string): Observable<SearchResult> {
    return this.http.get<SearchResult>(`${this.base}/search/`, { params: { q } });
  }
}
