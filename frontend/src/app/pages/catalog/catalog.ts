import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

import { ApiService } from '../../core/api.service';
import { GarageService } from '../../core/garage.service';
import { Brand, CarModel, Category, Product, ProductQuery, sortCategories } from '../../core/models';
import { KztPipe } from '../../shared/t.pipe';
import { ProductCard } from '../../components/product-card/product-card';
import { YmmSelector } from '../../components/ymm-selector/ymm-selector';
import { LocPipe, TPipe } from '../../shared/t.pipe';

const PAGE_SIZE = 12; // must match PAGE_SIZE in Django settings

@Component({
  selector: 'app-catalog',
  imports: [FormsModule, ProductCard, YmmSelector, TPipe, LocPipe, KztPipe],
  templateUrl: './catalog.html',
  styleUrl: './catalog.scss',
})
export class Catalog implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);
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

  /** cheapest / most expensive product (in the chosen category) → limits of the price slider */
  priceBounds = signal<{ min: number; max: number }>({ min: 0, max: 0 });

  totalPages = computed(() => Math.max(1, Math.ceil(this.total() / PAGE_SIZE)));
  pages = computed(() => Array.from({ length: this.totalPages() }, (_, i) => i + 1));

  /** categories in the order of the seed data (brakes, oil, filters, …) */
  sortedCategories = computed(() => sortCategories(this.categories()));
  allBrands = signal(false);
  visibleBrands = computed(() => {
    const list = this.brands();
    if (this.allBrands()) return list;
    // keep the selected brand visible even when the list is collapsed
    const first = list.slice(0, 6);
    const sel = list.find((b) => b.id === this.filters.brand);
    return sel && !first.includes(sel) ? [...first, sel] : first;
  });
  currentCategory() {
    return this.categories().find((c) => c.slug === this.filters.category);
  }

  ngOnInit() {
    this.api.getCategories().subscribe((c) => this.categories.set(c));
    this.api.getBrands().subscribe((b) => this.brands.set(b));
    this.api.getCars().subscribe((c) => this.cars.set(c));
    // header links: /?category=brakes#parts
    this.route.queryParamMap.subscribe((q) => {
      const slug = q.get('category') ?? '';
      if (slug !== this.filters.category || !this.started) this.pickCategory(slug);
      this.started = true;
    });
  }

  private started = false;
  private request?: Subscription;

  load() {
    // cancel a request still in flight: otherwise an older, slower answer could overwrite the newer one
    this.request?.unsubscribe();
    this.loading.set(true);
    this.error.set(false);
    const car = this.garage.car();
    const query: ProductQuery = { ...this.filters, car: car && this.onlyMyCar ? car.carId : null };
    this.request = this.api.getProducts(query).subscribe({
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

  pickCategory(slug: string, scroll = false) {
    this.filters.category = slug;
    // price limits differ per category: reset the price filter and reload the slider limits
    this.filters.min_price = null;
    this.filters.max_price = null;
    this.loadPriceBounds();
    this.apply();
    if (scroll) document.getElementById('parts')?.scrollIntoView({ behavior: 'smooth' });
  }

  pickBrand(id: number | null) {
    this.filters.brand = id;
    this.apply();
  }

  /** Price slider/inputs: keep min ≤ max and inside the bounds, then reload */
  setPrice(which: 'min' | 'max', raw: number | string | null) {
    const { min, max } = this.priceBounds();
    let value = raw === null || raw === '' ? null : Math.round(Number(raw));
    if (value !== null) value = Math.min(max, Math.max(min, value));
    if (which === 'min') {
      this.filters.min_price = value === min ? null : value;
      if (value !== null && this.filters.max_price != null && value > this.filters.max_price) this.filters.max_price = value;
    } else {
      this.filters.max_price = value === max ? null : value;
      if (value !== null && this.filters.min_price != null && value < this.filters.min_price) this.filters.min_price = value;
    }
    this.apply();
  }

  clearPrice() {
    this.filters.min_price = null;
    this.filters.max_price = null;
    this.apply();
  }

  private loadPriceBounds() {
    this.api.getPriceRange(this.filters.category || undefined).subscribe((r) => {
      this.priceBounds.set({ min: Math.floor(Number(r.min ?? 0)), max: Math.ceil(Number(r.max ?? 0)) });
    });
  }

  goToPage(page: number) {
    this.filters.page = page;
    this.load();
    document.getElementById('parts')?.scrollIntoView({ behavior: 'smooth' });
  }

  reset() {
    this.filters = this.defaults();
    this.loadPriceBounds();
    this.load();
  }

  private defaults(): ProductQuery {
    return { category: '', brand: null, in_stock: false, min_price: null, max_price: null, ordering: '-created_at', page: 1 };
  }
}
