import { Injectable, signal } from '@angular/core';

export type Lang = 'en' | 'ru';

/** UI text in two languages. Add a key here, then use it in templates as {{ 'key' | t }}. */
const DICT: Record<string, Record<Lang, string>> = {
  // header
  'nav.catalog': { en: 'Catalog', ru: 'Каталог' },
  'nav.search_placeholder': { en: 'Search by part name, SKU, brand or car…', ru: 'Поиск по названию, артикулу, бренду или авто…' },
  'nav.cart': { en: 'Cart', ru: 'Корзина' },
  'nav.orders': { en: 'My orders', ru: 'Мои заказы' },
  'nav.login': { en: 'Sign in', ru: 'Войти' },
  'nav.logout': { en: 'Sign out', ru: 'Выйти' },
  'nav.no_car': { en: 'Add your car', ru: 'Добавить авто' },
  'theme.to_light': { en: 'Switch to light theme', ru: 'Светлая тема' },
  'theme.to_dark': { en: 'Switch to dark theme', ru: 'Тёмная тема' },
  'api.online': { en: 'API connected', ru: 'API подключен' },
  'api.offline': { en: 'API offline', ru: 'API недоступен' },
  // hero / garage
  'hero.kicker': { en: 'Auto parts & accessories in Kazakhstan', ru: 'Автозапчасти и аксессуары в Казахстане' },
  'hero.title': { en: 'Parts that fit your car. First time.', ru: 'Детали, которые подходят вашему авто. С первого раза.' },
  'hero.sub': {
    en: 'Choose year, make and model — we show only compatible parts.',
    ru: 'Выберите год, марку и модель — покажем только совместимые детали.',
  },
  'ymm.title': { en: 'Find parts for your car', ru: 'Подбор по автомобилю' },
  'ymm.make': { en: 'Make', ru: 'Марка' },
  'ymm.model': { en: 'Model', ru: 'Модель' },
  'ymm.year': { en: 'Year', ru: 'Год' },
  'ymm.go': { en: 'Show parts', ru: 'Показать детали' },
  'ymm.saved': { en: 'My car', ru: 'Моё авто' },
  'ymm.change': { en: 'Change', ru: 'Сменить' },
  'ymm.clear': { en: 'Remove', ru: 'Убрать' },
  'perk.fit': { en: 'Fitment check for every part', ru: 'Проверка совместимости для каждой детали' },
  'perk.stock': { en: 'Real stock — no overselling', ru: 'Реальный остаток — без «нет в наличии» после оплаты' },
  'perk.delivery': { en: 'Delivery across Kazakhstan', ru: 'Доставка по всему Казахстану' },
  // filters
  'filter.categories': { en: 'Categories', ru: 'Категории' },
  'filter.all': { en: 'All parts', ru: 'Все детали' },
  'filter.brand': { en: 'Brand', ru: 'Бренд' },
  'filter.any_brand': { en: 'Any brand', ru: 'Любой бренд' },
  'filter.in_stock': { en: 'In stock only', ru: 'Только в наличии' },
  'filter.reset': { en: 'Reset filters', ru: 'Сбросить фильтры' },
  'filter.fits_only': { en: 'Only parts for', ru: 'Только для' },
  'sort.label': { en: 'Sort', ru: 'Сортировка' },
  'sort.new': { en: 'Newest', ru: 'Новинки' },
  'sort.price_asc': { en: 'Price: low to high', ru: 'Цена: по возрастанию' },
  'sort.price_desc': { en: 'Price: high to low', ru: 'Цена: по убыванию' },
  'catalog.found': { en: 'parts', ru: 'деталей' },
  'catalog.empty': { en: 'No parts match these filters.', ru: 'По этим фильтрам ничего не найдено.' },
  'catalog.loading': { en: 'Loading…', ru: 'Загрузка…' },
  'catalog.error': {
    en: 'Could not load data. Is the backend running on port 8000?',
    ru: 'Не удалось загрузить данные. Запущен ли бэкенд на порту 8000?',
  },
  'page.prev': { en: 'Previous', ru: 'Назад' },
  'page.next': { en: 'Next', ru: 'Далее' },
  // product
  'product.in_stock': { en: 'In stock', ru: 'В наличии' },
  'product.left': { en: 'left', ru: 'шт. осталось' },
  'product.out_of_stock': { en: 'Out of stock', ru: 'Нет в наличии' },
  'product.pcs': { en: 'pcs', ru: 'шт' },
  'product.fits': { en: 'Fits these cars', ru: 'Подходит к авто' },
  'product.fits_yours': { en: 'Fits your', ru: 'Подходит к вашему' },
  'product.not_fit': { en: 'Does not fit your', ru: 'Не подходит к вашему' },
  'product.brand': { en: 'Brand', ru: 'Бренд' },
  'product.category': { en: 'Category', ru: 'Категория' },
  'product.back': { en: 'Back to catalog', ru: 'Назад в каталог' },
  'product.add': { en: 'Add to cart', ru: 'В корзину' },
  'product.added': { en: 'Added to cart', ru: 'Добавлено в корзину' },
  'product.max_reached': { en: 'All available items are in your cart', ru: 'Весь остаток уже в корзине' },
  'product.qty': { en: 'Quantity', ru: 'Количество' },
  'product.max_hint': { en: 'max', ru: 'макс.' },
  // cart
  'cart.title': { en: 'Cart', ru: 'Корзина' },
  'cart.empty': { en: 'Your cart is empty.', ru: 'Ваша корзина пуста.' },
  'cart.to_catalog': { en: 'Go to catalog', ru: 'Перейти в каталог' },
  'cart.remove': { en: 'Remove', ru: 'Удалить' },
  'cart.total': { en: 'Total', ru: 'Итого' },
  'cart.items': { en: 'items', ru: 'шт.' },
  'cart.checkout': { en: 'Checkout', ru: 'Оформление заказа' },
  'cart.address': { en: 'Delivery address', ru: 'Адрес доставки' },
  'cart.phone': { en: 'Phone', ru: 'Телефон' },
  'cart.place_order': { en: 'Place order', ru: 'Оформить заказ' },
  'cart.placed': { en: 'Order placed!', ru: 'Заказ оформлен!' },
  'cart.placed_sub': { en: 'You can follow it in My orders.', ru: 'Его статус можно смотреть в «Мои заказы».' },
  'cart.need_login': { en: 'Sign in to use the cart.', ru: 'Войдите, чтобы пользоваться корзиной.' },
  'cart.stock_limit': { en: 'Only', ru: 'Доступно' },
  // orders
  'orders.title': { en: 'My orders', ru: 'Мои заказы' },
  'orders.empty': { en: 'No orders yet.', ru: 'Заказов пока нет.' },
  'orders.order': { en: 'Order', ru: 'Заказ' },
  'status.new': { en: 'New', ru: 'Новый' },
  'status.paid': { en: 'Paid', ru: 'Оплачен' },
  'status.shipped': { en: 'Shipped', ru: 'Отправлен' },
  'status.delivered': { en: 'Delivered', ru: 'Доставлен' },
  'status.cancelled': { en: 'Cancelled', ru: 'Отменён' },
  // login
  'login.title': { en: 'Sign in', ru: 'Вход' },
  'login.username': { en: 'Username', ru: 'Логин' },
  'login.password': { en: 'Password', ru: 'Пароль' },
  'login.submit': { en: 'Sign in', ru: 'Войти' },
  'login.error': { en: 'Wrong username or password.', ru: 'Неверный логин или пароль.' },
  'login.demo': { en: 'Demo account', ru: 'Демо-аккаунт' },
  // search
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
