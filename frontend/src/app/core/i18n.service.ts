import { Injectable, signal } from '@angular/core';

export type Lang = 'en' | 'ru';

/** UI text in two languages. Add a key here, then use it in templates as {{ 'key' | t }}. */
const DICT: Record<string, Record<Lang, string>> = {
  'nav.catalog': { en: 'Catalog', ru: 'Каталог' },
  'nav.search_placeholder': { en: 'Search parts, brands, cars…', ru: 'Поиск деталей, брендов, авто…' },
  'theme.to_light': { en: 'Switch to light theme', ru: 'Светлая тема' },
  'theme.to_dark': { en: 'Switch to dark theme', ru: 'Тёмная тема' },
  'api.online': { en: 'API connected', ru: 'API подключен' },
  'api.offline': { en: 'API offline', ru: 'API недоступен' },
  'hero.title': { en: 'Parts that fit. First time.', ru: 'Детали, которые подходят. С первого раза.' },
  'hero.sub': {
    en: 'Pick your car and see only compatible parts and accessories.',
    ru: 'Выберите своё авто и смотрите только совместимые детали и аксессуары.',
  },
  'filter.my_car': { en: 'Fits my car', ru: 'Подходит к моему авто' },
  'filter.any_car': { en: 'Any car', ru: 'Любое авто' },
  'filter.categories': { en: 'Categories', ru: 'Категории' },
  'filter.all': { en: 'All parts', ru: 'Все детали' },
  'filter.brand': { en: 'Brand', ru: 'Бренд' },
  'filter.any_brand': { en: 'Any brand', ru: 'Любой бренд' },
  'filter.in_stock': { en: 'In stock only', ru: 'Только в наличии' },
  'filter.reset': { en: 'Reset filters', ru: 'Сбросить фильтры' },
  'sort.label': { en: 'Sort', ru: 'Сортировка' },
  'sort.new': { en: 'Newest', ru: 'Новинки' },
  'sort.price_asc': { en: 'Price: low to high', ru: 'Цена: по возрастанию' },
  'sort.price_desc': { en: 'Price: high to low', ru: 'Цена: по убыванию' },
  'catalog.found': { en: 'parts found', ru: 'деталей найдено' },
  'catalog.empty': { en: 'No parts match these filters.', ru: 'По этим фильтрам ничего не найдено.' },
  'catalog.loading': { en: 'Loading…', ru: 'Загрузка…' },
  'catalog.error': {
    en: 'Could not load data. Is the backend running on port 8000?',
    ru: 'Не удалось загрузить данные. Запущен ли бэкенд на порту 8000?',
  },
  'page.prev': { en: 'Previous', ru: 'Назад' },
  'page.next': { en: 'Next', ru: 'Далее' },
  'product.in_stock': { en: 'In stock', ru: 'В наличии' },
  'product.out_of_stock': { en: 'Out of stock', ru: 'Нет в наличии' },
  'product.pcs': { en: 'pcs', ru: 'шт' },
  'product.fits': { en: 'Fits these cars', ru: 'Подходит к авто' },
  'product.brand': { en: 'Brand', ru: 'Бренд' },
  'product.category': { en: 'Category', ru: 'Категория' },
  'product.back': { en: 'Back to catalog', ru: 'Назад в каталог' },
  'product.add_to_cart': { en: 'Add to cart — next sprint', ru: 'В корзину — следующий спринт' },
  'search.title': { en: 'Search results for', ru: 'Результаты поиска:' },
  'search.products': { en: 'Parts', ru: 'Детали' },
  'search.categories': { en: 'Categories', ru: 'Категории' },
  'search.cars': { en: 'Car models', ru: 'Модели авто' },
  'search.nothing': { en: 'Nothing found.', ru: 'Ничего не найдено.' },
  'search.min': { en: 'Type at least 2 characters.', ru: 'Введите минимум 2 символа.' },
  'footer.text': {
    en: 'BIS AutoShop · KBTU · Basics of Information Systems project',
    ru: 'BIS AutoShop · КБТУ · Проект по Основам информационных систем',
  },
};

@Injectable({ providedIn: 'root' })
export class I18nService {
  readonly lang = signal<Lang>(this.loadLang());

  setLang(lang: Lang) {
    this.lang.set(lang);
    try {
      localStorage.setItem('lang', lang);
    } catch {}
    document.documentElement.lang = lang;
  }

  t(key: string): string {
    return DICT[key]?.[this.lang()] ?? key;
  }

  /** Picks name_en / name_ru (or description_en / description_ru) from an API object. */
  field(obj: any, base: string): string {
    return obj?.[`${base}_${this.lang()}`] || obj?.[`${base}_en`] || '';
  }

  private loadLang(): Lang {
    try {
      const saved = localStorage.getItem('lang');
      if (saved === 'en' || saved === 'ru') return saved;
    } catch {}
    return 'en';
  }
}
