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
  is_active: boolean;
  category: Category;
  brand: Brand;
  compatible_cars: CarModel[];
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
  role: 'customer' | 'manager' | 'admin';
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

export interface Order {
  id: number;
  status: 'new' | 'paid' | 'shipped' | 'delivered' | 'cancelled';
  shipping_address: string;
  phone: string;
  total: string;
  items: OrderItem[];
  created_at: string;
}

/** The car the user picked in the Year / Make / Model selector ("My garage"). */
export interface GarageCar {
  carId: number;
  make: string;
  model: string;
  year: number;
}
