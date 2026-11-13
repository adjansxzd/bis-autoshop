import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../core/api.service';
import { GarageService } from '../../core/garage.service';
import { Brand, CarModel, Category, Product, ProductQuery } from '../../core/models';
import { ProductCard } from '../../components/product-card/product-card';
import { YmmSelector } from '../../components/ymm-selector/ymm-selector';
import { PartIcon } from '../../shared/part-icon';
import { LocPipe, TPipe } from '../../shared/t.pipe';

const PAGE_SIZE = 12; // must match PAGE_SIZE in Django settings

@Component({
  selector: 'app-catalog',
  imports: [FormsModule, ProductCard, YmmSelector, PartIcon, TPipe, LocPipe],
  templateUrl: './catalog.html',
  styleUrl: './catalog.scss',
})
export class Catalog implements OnInit {
  private api = inject(ApiService);
  garage = inject(GarageService);

  // reference data (GET /api/categories/, /api/brands/, /api/cars/)
  categories = signal<Category[]>([]);
  brands = signal<Brand[]>([]);
  cars = signal<CarModel[]>([]);

  // product list (GET /api/products/?...)
  products = signal<Product[]>([]);
  total = signal(0);
  loading = signal(true);
  error = signal(false);

  filters: ProductQuery = this.defaults();
  /** when a car is saved in "My garage", show only parts that fit it (can be switched off) */
  onlyMyCar = true;

  totalPages = computed(() => Math.max(1, Math.ceil(this.total() / PAGE_SIZE)));

  ngOnInit() {
    this.api.getCategories().subscribe((c) => this.categories.set(c));
    this.api.getBrands().subscribe((b) => this.brands.set(b));
    this.api.getCars().subscribe((c) => this.cars.set(c));
    this.load();
  }

  load() {
    this.loading.set(true);
    this.error.set(false);
    const car = this.garage.car();
    const query: ProductQuery = { ...this.filters, car: car && this.onlyMyCar ? car.carId : null };
    this.api.getProducts(query).subscribe({
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

  apply() {
    this.filters.page = 1;
    this.load();
  }

  onCarPicked() {
    this.onlyMyCar = true;
    this.apply();
    document.getElementById('parts')?.scrollIntoView({ behavior: 'smooth' });
  }

  pickCategory(slug: string) {
    this.filters.category = slug;
    this.apply();
  }

  goToPage(page: number) {
    this.filters.page = page;
    this.load();
    document.getElementById('parts')?.scrollIntoView({ behavior: 'smooth' });
  }

  reset() {
    this.filters = this.defaults();
    this.load();
  }

  private defaults(): ProductQuery {
    return { category: '', brand: null, in_stock: false, ordering: '-created_at', page: 1 };
  }
}
