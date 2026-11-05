import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../core/api.service';
import { Brand, CarModel, Category, Product, ProductQuery } from '../../core/models';
import { ProductCard } from '../../components/product-card/product-card';
import { PartIcon } from '../../shared/part-icon';
import { LocPipe, TPipe } from '../../shared/t.pipe';

const PAGE_SIZE = 12; // must match PAGE_SIZE in Django settings

@Component({
  selector: 'app-catalog',
  imports: [FormsModule, ProductCard, PartIcon, TPipe, LocPipe],
  templateUrl: './catalog.html',
  styleUrl: './catalog.scss',
})
export class Catalog implements OnInit {
  private api = inject(ApiService);

  // reference data for the filters (GET /api/categories/, /api/brands/, /api/cars/)
  categories = signal<Category[]>([]);
  brands = signal<Brand[]>([]);
  cars = signal<CarModel[]>([]);

  // product list state (GET /api/products/?...)
  products = signal<Product[]>([]);
  total = signal(0);
  loading = signal(true);
  error = signal(false);

  // current filters
  filters: ProductQuery = { category: '', brand: null, car: null, in_stock: false, ordering: '-created_at', page: 1 };

  totalPages = computed(() => Math.max(1, Math.ceil(this.total() / PAGE_SIZE)));
  selectedCar = computed(() => this.cars().find((c) => c.id === this.carId()));
  private carId = signal<number | null>(null);

  ngOnInit() {
    this.api.getCategories().subscribe((c) => this.categories.set(c));
    this.api.getBrands().subscribe((b) => this.brands.set(b));
    this.api.getCars().subscribe((c) => this.cars.set(c));
    this.load();
  }

  load() {
    this.loading.set(true);
    this.error.set(false);
    this.carId.set(this.filters.car ?? null);
    this.api.getProducts(this.filters).subscribe({
      next: (page) => {
        this.products.set(page.results);
        this.total.set(page.count);
        this.loading.set(false);
      },
      error: () => {
        this.error.set(true);
        this.loading.set(false);
      },
    });
  }

  /** Any filter change resets to page 1 */
  apply() {
    this.filters.page = 1;
    this.load();
  }

  pickCategory(slug: string) {
    this.filters.category = slug;
    this.apply();
  }

  goToPage(page: number) {
    this.filters.page = page;
    this.load();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  reset() {
    this.filters = { category: '', brand: null, car: null, in_stock: false, ordering: '-created_at', page: 1 };
    this.load();
  }
}
