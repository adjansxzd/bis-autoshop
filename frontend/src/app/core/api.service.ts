import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { Brand, CarModel, Category, Page, PriceRange, Product, ProductQuery, Review, ReviewsResponse, SearchResult } from './models';

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

  /** lowest / highest price, for the price slider (optionally within one category) */
  getPriceRange(category?: string): Observable<PriceRange> {
    const params: Record<string, string> = category ? { category } : {};
    return this.http.get<PriceRange>(`${this.base}/products/price-range/`, { params });
  }

  getReviews(productId: number): Observable<ReviewsResponse> {
    return this.http.get<ReviewsResponse>(`${this.base}/products/${productId}/reviews/`);
  }

  addReview(productId: number, rating: number, text: string): Observable<Review> {
    return this.http.post<Review>(`${this.base}/products/${productId}/reviews/`, { rating, text });
  }

  updateReview(id: number, rating: number, text: string): Observable<Review> {
    return this.http.patch<Review>(`${this.base}/reviews/${id}/`, { rating, text });
  }

  deleteReview(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/reviews/${id}/`);
  }

  search(q: string): Observable<SearchResult> {
    return this.http.get<SearchResult>(`${this.base}/search/`, { params: { q } });
  }
}
