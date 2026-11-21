// TypeScript shapes of the JSON returned by the Django REST API.

export interface Category {
  id: number;
  name_en: string;
  name_ru: string;
  slug: string;
  parent: number | null;
  icon: string;
  product_count: number;
}

export interface Brand {
  id: number;
  name: string;
  country: string;
}

export interface CarModel {
  id: number;
  make: string;
  model: string;
  year_from: number;
  year_to: number;
  label: string;
}

export interface Product {
  id: number;
  sku: string;
  name_en: string;
  name_ru: string;
  description_en: string;
  description_ru: string;
  price: string; // Decimal comes as string
  stock: number;
  in_stock: boolean;
  image_url: string;
  image: string | null; // uploaded photo URL (null → show the category icon)
  oem_numbers: string;
  specs: Spec[];
  rating_avg: number | null;
  rating_count: number;
  is_active: boolean;
  category: Category;
  brand: Brand;
  compatible_cars: CarModel[];
}

export interface Spec {
  en: string;
  ru: string;
  value: string;
}

export interface Review {
  id: number;
  rating: number;
  text: string;
  author: string;
  is_mine: boolean;
  created_at: string;
}

export interface ReviewsResponse {
  summary: { avg: number | null; count: number; distribution: Record<string, number> };
  can_review: boolean;
  my_review: Review | null;
  results: Review[];
}

export interface PriceRange {
  min: string | null;
  max: string | null;
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface SearchResult {
  query: string;
  products: Product[];
  categories: Category[];
  cars: CarModel[];
}

export interface ProductQuery {
  category?: string;
  brand?: number | null;
  car?: number | null;
  in_stock?: boolean;
  min_price?: number | null;
  max_price?: number | null;
  search?: string;
  ordering?: string;
  page?: number;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  address: string;
  preferred_language: 'en' | 'ru';
  role: 'customer' | 'manager' | 'admin';
}

/** A car saved in the user's account ("My cars"), GET /api/auth/garage/ */
export interface SavedCar {
  id: number;
  car_id: number;
  make: string;
  model: string;
  year: number;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  password2: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
}

export interface CartItem {
  id: number;
  product: Product;
  quantity: number;
  subtotal: string;
}

export interface Cart {
  id: number;
  items: CartItem[];
  total: string;
}

export interface OrderItem {
  id: number;
  product: number;
  product_name: string;
  quantity: number;
  unit_price: string;
  subtotal: string;
}

export type OrderStatus = 'new' | 'paid' | 'shipped' | 'delivered' | 'cancelled';

export interface OrderEvent {
  status: OrderStatus;
  note: string;
  by: 'customer' | 'shop' | null;
  created_at: string;
}

export interface Order {
  id: number;
  status: OrderStatus;
  delivery_method: 'courier' | 'pickup';
  payment_method: 'card' | 'cash';
  shipping_address: string;
  phone: string;
  comment: string;
  items_total: string;
  delivery_cost: string;
  total: string;
  paid_at: string | null;
  items: OrderItem[];
  events: OrderEvent[];
  can_pay: boolean;
  can_cancel: boolean;
  created_at: string;
}

export interface CheckoutData {
  delivery_method: 'courier' | 'pickup';
  payment_method: 'card' | 'cash';
  shipping_address: string;
  phone: string;
  comment: string;
}

export interface DeliveryOptions {
  courier_price: string;
  free_from: string;
  pickup_address: string;
}

/** The car the user picked in the Year / Make / Model selector ("My garage"). */
export interface GarageCar {
  carId: number;
  make: string;
  model: string;
  year: number;
}
