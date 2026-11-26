"""
Demo catalog for `python manage.py seed`.
Prices are in tenge (KZT). OEM numbers and specs are DEMO data for the course project.
To add a product: append a row to PRODUCTS (keys of CARS in the last column) and run `seed` again.
"""

# slug, name EN, name RU, icon (frontend icon name)
CATEGORIES = [
    ("brakes", "Brakes", "Тормозная система", "disc"),
    ("engine-oil", "Engine oil & fluids", "Масла и жидкости", "droplet"),
    ("filters", "Filters", "Фильтры", "filter"),
    ("lighting", "Lighting", "Освещение", "bulb"),
    ("suspension", "Suspension", "Подвеска", "spring"),
    ("ignition", "Ignition", "Зажигание", "spark"),
    ("electrics", "Batteries & electrics", "Аккумуляторы и электрика", "battery"),
    ("cooling", "Cooling system", "Система охлаждения", "thermo"),
    ("tires", "Tires & wheels", "Шины и диски", "wheel"),
    ("body", "Body & mirrors", "Кузов и зеркала", "car"),
    ("care", "Car care", "Автохимия и уход", "spray"),
    ("accessories", "Accessories", "Аксессуары", "star"),
]

BRANDS = [
    ("Bosch", "Germany"), ("Brembo", "Italy"), ("Castrol", "United Kingdom"), ("Mann-Filter", "Germany"),
    ("Philips", "Netherlands"), ("KYB", "Japan"), ("Michelin", "France"), ("Toyota Genuine", "Japan"),
    ("NGK", "Japan"), ("Denso", "Japan"), ("Varta", "Germany"), ("Liqui Moly", "Germany"), ("Motul", "France"),
    ("Valeo", "France"), ("Sachs", "Germany"), ("Gates", "USA"), ("Osram", "Germany"), ("Hella", "Germany"),
    ("Continental", "Germany"), ("Nokian", "Finland"), ("Hyundai/Kia Genuine", "South Korea"), ("TRW", "Germany"),
    ("AIRLINE", "Russia"), ("Baseus", "China"),
]

# key: make, model, year from, year to   (the first 8 keep their order from earlier versions)
CARS = {
    "camry": ("Toyota", "Camry", 2018, 2024),
    "prado": ("Toyota", "Land Cruiser Prado", 2010, 2023),
    "elantra": ("Hyundai", "Elantra", 2016, 2023),
    "tucson": ("Hyundai", "Tucson", 2015, 2024),
    "rio": ("Kia", "Rio", 2017, 2023),
    "cobalt": ("Chevrolet", "Cobalt", 2013, 2023),
    "granta": ("Lada", "Granta", 2011, 2024),
    "polo": ("Volkswagen", "Polo", 2015, 2022),
    "corolla": ("Toyota", "Corolla", 2013, 2024),
    "rav4": ("Toyota", "RAV4", 2013, 2024),
    "lc200": ("Toyota", "Land Cruiser 200", 2008, 2021),
    "accent": ("Hyundai", "Accent", 2011, 2020),
    "sonata": ("Hyundai", "Sonata", 2015, 2023),
    "creta": ("Hyundai", "Creta", 2016, 2024),
    "sportage": ("Kia", "Sportage", 2016, 2024),
    "k5": ("Kia", "K5", 2020, 2024),
    "cerato": ("Kia", "Cerato", 2013, 2024),
    "nexia": ("Chevrolet", "Nexia", 2016, 2023),
    "vesta": ("Lada", "Vesta", 2015, 2024),
    "niva": ("Lada", "Niva Legend", 2010, 2024),
    "octavia": ("Skoda", "Octavia", 2013, 2024),
    "qashqai": ("Nissan", "Qashqai", 2014, 2022),
}

TOYOTA = ["camry", "prado", "corolla", "rav4", "lc200"]
KOREAN = ["elantra", "tucson", "rio", "accent", "sonata", "creta", "sportage", "k5", "cerato"]
BUDGET = ["cobalt", "nexia", "granta", "vesta", "niva"]
EURO = ["polo", "octavia", "qashqai"]
ALL = list(CARS)

# Description templates per category: {name} and {brand} are filled in
DESCRIPTIONS = {
    "brakes": ("{name} by {brand}. Strong, stable braking with low dust and quiet operation. Replace in pairs on the same axle.",
               "{name} от {brand}. Уверенное торможение, мало пыли и без скрипа. Меняйте парой на одной оси."),
    "engine-oil": ("{name} by {brand}. Protects the engine from wear and deposits; check your owner's manual for the right spec.",
                   "{name} от {brand}. Защищает двигатель от износа и отложений; допуск смотрите в руководстве к авто."),
    "filters": ("{name} by {brand}. High filtration efficiency for clean air and oil. Recommended at every service.",
                "{name} от {brand}. Высокая степень фильтрации. Рекомендуется менять при каждом ТО."),
    "lighting": ("{name} by {brand}. Brighter, whiter light for safer night driving.",
                 "{name} от {brand}. Более яркий и белый свет для безопасной езды ночью."),
    "suspension": ("{name} by {brand}. Restores handling and comfort on Kazakhstan roads.",
                   "{name} от {brand}. Возвращает управляемость и комфорт на наших дорогах."),
    "ignition": ("{name} by {brand}. Reliable cold starts and smooth engine running.",
                 "{name} от {brand}. Надёжный холодный пуск и ровная работа двигателя."),
    "electrics": ("{name} by {brand}. Dependable power even at −30 °C.",
                  "{name} от {brand}. Надёжная работа даже при −30 °C."),
    "cooling": ("{name} by {brand}. Keeps the engine at the right temperature in summer and winter.",
                "{name} от {brand}. Поддерживает нужную температуру двигателя летом и зимой."),
    "tires": ("{name} by {brand}. Grip, comfort and long tread life.",
              "{name} от {brand}. Сцепление, комфорт и долгий срок службы протектора."),
    "body": ("{name} by {brand}. Exact fit, ready to install.",
             "{name} от {brand}. Точная посадка, готово к установке."),
    "care": ("{name} by {brand}. Keeps your car clean and protected.",
             "{name} от {brand}. Чистота и защита вашего автомобиля."),
    "accessories": ("{name} by {brand}. Practical addition for everyday driving.",
                    "{name} от {brand}. Полезное дополнение для каждой поездки."),
}


def spec(en, ru, value):
    return {"en": en, "ru": ru, "value": value}


# sku, name EN, name RU, category, brand, price KZT, opening stock, compatible cars (keys), OEM numbers, specs
PRODUCTS = [
    # --- brakes ---
    ("BR-001", "Front brake pads", "Передние тормозные колодки", "brakes", "Brembo", 24900, 15, ["camry", "elantra", "tucson"],
     "04465-33471, 58101-2SA70", [spec("Axle", "Ось", "Front / Передняя"), spec("Width", "Ширина", "137 mm"), spec("Wear indicator", "Датчик износа", "Yes / Да")]),
    ("BR-002", "Ventilated brake disc", "Вентилируемый тормозной диск", "brakes", "Brembo", 38500, 8, ["camry", "prado"],
     "43512-33150", [spec("Diameter", "Диаметр", "296 mm"), spec("Thickness", "Толщина", "28 mm"), spec("Type", "Тип", "Ventilated / Вентилируемый")]),
    ("BR-003", "Rear brake pads", "Задние тормозные колодки", "brakes", "Bosch", 17900, 20, ["elantra", "rio", "granta"],
     "58302-F2A30", [spec("Axle", "Ось", "Rear / Задняя"), spec("Width", "Ширина", "99 mm")]),
    ("BR-004", "Brake fluid DOT4 1L", "Тормозная жидкость DOT4 1л", "brakes", "Bosch", 4900, 40, ALL,
     "", [spec("Standard", "Стандарт", "DOT 4"), spec("Volume", "Объём", "1 L"), spec("Boiling point", "Темп. кипения", "265 °C")]),
    ("BR-005", "Front brake pads TRW", "Передние тормозные колодки TRW", "brakes", "TRW", 19900, 18, ["corolla", "rav4", "camry"],
     "04465-02220", [spec("Axle", "Ось", "Front / Передняя"), spec("Width", "Ширина", "131 mm")]),
    ("BR-006", "Front brake disc (pair)", "Передние тормозные диски (пара)", "brakes", "TRW", 46900, 6, ["creta", "rio", "accent", "cerato"],
     "51712-H5000", [spec("Diameter", "Диаметр", "256 mm"), spec("Quantity", "Количество", "2 pcs / шт")]),
    ("BR-007", "Rear brake drum", "Задний тормозной барабан", "brakes", "TRW", 21900, 4, ["granta", "vesta", "nexia", "cobalt"],
     "", [spec("Diameter", "Диаметр", "200 mm")]),
    ("BR-008", "Brake pads Land Cruiser", "Тормозные колодки Land Cruiser", "brakes", "Toyota Genuine", 42900, 9, ["lc200", "prado"],
     "04465-60320", [spec("Axle", "Ось", "Front / Передняя"), spec("Original part", "Оригинал", "Yes / Да")]),
    # --- oils & fluids ---
    ("OIL-001", "Castrol EDGE 5W-30 4L", "Моторное масло Castrol EDGE 5W-30 4л", "engine-oil", "Castrol", 21500, 30, ["camry", "elantra", "tucson", "polo"],
     "", [spec("Viscosity", "Вязкость", "5W-30"), spec("Volume", "Объём", "4 L"), spec("Type", "Тип", "Synthetic / Синтетика")]),
    ("OIL-002", "Castrol Magnatec 10W-40 4L", "Моторное масло Castrol Magnatec 10W-40 4л", "engine-oil", "Castrol", 14900, 25, ["rio", "cobalt", "granta", "nexia"],
     "", [spec("Viscosity", "Вязкость", "10W-40"), spec("Volume", "Объём", "4 L"), spec("Type", "Тип", "Semi-synthetic / Полусинтетика")]),
    ("OIL-003", "Antifreeze G12 5L", "Антифриз G12 5л", "cooling", "Castrol", 8900, 18, ALL,
     "", [spec("Standard", "Стандарт", "G12"), spec("Volume", "Объём", "5 L"), spec("Freezing point", "Замерзает при", "−40 °C")]),
    ("OIL-004", "Liqui Moly Top Tec 4200 5W-30 5L", "Liqui Moly Top Tec 4200 5W-30 5л", "engine-oil", "Liqui Moly", 32900, 14, EURO + ["camry"],
     "", [spec("Viscosity", "Вязкость", "5W-30"), spec("Volume", "Объём", "5 L"), spec("Approvals", "Допуски", "VW 504/507")]),
    ("OIL-005", "Motul 8100 X-clean 5W-40 4L", "Motul 8100 X-clean 5W-40 4л", "engine-oil", "Motul", 29900, 12, KOREAN + EURO,
     "", [spec("Viscosity", "Вязкость", "5W-40"), spec("Volume", "Объём", "4 L")]),
    ("OIL-006", "Toyota Genuine 0W-20 4L", "Оригинальное масло Toyota 0W-20 4л", "engine-oil", "Toyota Genuine", 24900, 20, ["camry", "corolla", "rav4"],
     "08880-83886", [spec("Viscosity", "Вязкость", "0W-20"), spec("Volume", "Объём", "4 L")]),
    ("OIL-007", "ATF automatic transmission fluid 1L", "Масло для АКПП ATF 1л", "engine-oil", "Liqui Moly", 6900, 35, ALL,
     "", [spec("Type", "Тип", "ATF Dexron VI"), spec("Volume", "Объём", "1 L")]),
    ("OIL-008", "Windscreen washer −30 °C 4L", "Омывающая жидкость −30 °C 4л", "care", "Liqui Moly", 3500, 60, ALL,
     "", [spec("Frost protection", "Не замерзает до", "−30 °C"), spec("Volume", "Объём", "4 L")]),
    # --- filters ---
    ("FL-001", "Oil filter W 712/95", "Масляный фильтр W 712/95", "filters", "Mann-Filter", 3900, 50, ["elantra", "tucson", "rio"],
     "26300-35505", [spec("Height", "Высота", "79 mm"), spec("Thread", "Резьба", "M20x1.5")]),
    ("FL-002", "Air filter C 26 017", "Воздушный фильтр C 26 017", "filters", "Mann-Filter", 6500, 35, ["camry", "prado"],
     "17801-0V020", [spec("Length", "Длина", "259 mm"), spec("Width", "Ширина", "193 mm")]),
    ("FL-003", "Cabin filter with carbon", "Салонный фильтр угольный", "filters", "Bosch", 5900, 0, ["camry", "elantra", "tucson", "rio"],
     "87139-33010", [spec("Type", "Тип", "Activated carbon / Угольный")]),
    ("FL-004", "Toyota genuine oil filter", "Оригинальный масляный фильтр Toyota", "filters", "Toyota Genuine", 4500, 22, ["camry", "prado", "corolla", "rav4"],
     "90915-YZZE1", [spec("Original part", "Оригинал", "Yes / Да")]),
    ("FL-005", "Fuel filter", "Топливный фильтр", "filters", "Bosch", 7900, 16, KOREAN,
     "31911-2E000", [spec("Fuel", "Топливо", "Petrol / Бензин")]),
    ("FL-006", "Air filter Lada", "Воздушный фильтр Lada", "filters", "Mann-Filter", 2900, 40, ["granta", "vesta", "niva"],
     "21120-1109080", [spec("Length", "Длина", "235 mm")]),
    ("FL-007", "Cabin filter Hyundai/Kia", "Салонный фильтр Hyundai/Kia", "filters", "Hyundai/Kia Genuine", 4900, 30, ["creta", "rio", "accent", "sportage", "cerato"],
     "97133-D3000", [spec("Original part", "Оригинал", "Yes / Да")]),
    # --- lighting ---
    ("LT-001", "H7 X-tremeVision bulbs (2 pcs)", "Лампы H7 X-tremeVision (2 шт)", "lighting", "Philips", 11900, 28, ["elantra", "rio", "cobalt", "polo"],
     "", [spec("Base", "Цоколь", "H7"), spec("Power", "Мощность", "55 W"), spec("Brighter", "Ярче", "+130%")]),
    ("LT-002", "LED H4 headlight kit", "Комплект LED ламп H4", "lighting", "Philips", 27900, 10, ["cobalt", "granta", "nexia", "niva"],
     "", [spec("Base", "Цоколь", "H4"), spec("Colour temperature", "Цвет. температура", "6000 K")]),
    ("LT-003", "Osram Night Breaker H11 (2 pcs)", "Osram Night Breaker H11 (2 шт)", "lighting", "Osram", 13900, 22, ["camry", "corolla", "rav4", "creta", "sportage"],
     "", [spec("Base", "Цоколь", "H11"), spec("Power", "Мощность", "55 W")]),
    ("LT-004", "Fog lamp Hella", "Противотуманная фара Hella", "lighting", "Hella", 18900, 7, ["polo", "octavia", "vesta"],
     "", [spec("Side", "Сторона", "Left/Right / Л/П")]),
    ("LT-005", "W5W LED parking bulbs (2 pcs)", "LED лампы габаритов W5W (2 шт)", "lighting", "Osram", 3900, 45, ALL,
     "", [spec("Base", "Цоколь", "W5W (T10)")]),
    # --- suspension ---
    ("SU-001", "Front shock absorber Excel-G", "Передний амортизатор Excel-G", "suspension", "KYB", 32900, 12, ["camry", "elantra", "tucson"],
     "48510-06G00", [spec("Axle", "Ось", "Front / Передняя"), spec("Type", "Тип", "Gas / Газовый")]),
    ("SU-002", "Rear shock absorber Excel-G", "Задний амортизатор Excel-G", "suspension", "KYB", 28900, 9, ["rio", "granta", "polo"],
     "55310-H8000", [spec("Axle", "Ось", "Rear / Задняя"), spec("Type", "Тип", "Gas / Газовый")]),
    ("SU-003", "Stabilizer link", "Стойка стабилизатора", "suspension", "Toyota Genuine", 9900, 16, ["camry", "prado"],
     "48820-06070", [spec("Original part", "Оригинал", "Yes / Да")]),
    ("SU-004", "Front shock absorber Sachs", "Передний амортизатор Sachs", "suspension", "Sachs", 35900, 5, EURO,
     "", [spec("Axle", "Ось", "Front / Передняя")]),
    ("SU-005", "Lower control arm", "Рычаг передней подвески нижний", "suspension", "TRW", 27900, 8, ["creta", "rio", "accent"],
     "54500-H5000", [spec("Side", "Сторона", "Left / Левый")]),
    ("SU-006", "Shock absorber Land Cruiser", "Амортизатор Land Cruiser", "suspension", "KYB", 49900, 3, ["lc200", "prado"],
     "48510-69675", [spec("Axle", "Ось", "Front / Передняя")]),
    # --- ignition ---
    ("IG-001", "NGK Iridium spark plug", "Свеча зажигания NGK Iridium", "ignition", "NGK", 5900, 80, ["camry", "corolla", "rav4", "elantra", "creta"],
     "90919-01253", [spec("Electrode", "Электрод", "Iridium / Иридий"), spec("Gap", "Зазор", "1.1 mm")]),
    ("IG-002", "Denso spark plug (4 pcs)", "Свечи зажигания Denso (4 шт)", "ignition", "Denso", 12900, 25, BUDGET + ["rio", "accent"],
     "", [spec("Quantity", "Количество", "4 pcs / шт")]),
    ("IG-003", "Ignition coil", "Катушка зажигания", "ignition", "Bosch", 24900, 10, KOREAN,
     "27301-2B010", [spec("Type", "Тип", "Pencil coil / Индивидуальная")]),
    ("IG-004", "Spark plug wire set", "Высоковольтные провода (комплект)", "ignition", "Bosch", 8900, 14, ["granta", "niva", "nexia"],
     "", [spec("Quantity", "Количество", "4 pcs / шт")]),
    # --- electrics ---  (AC-002 keeps its old SKU: seed finds products by SKU, a new SKU would create a duplicate)
    ("AC-002", "Car battery S4 60Ah", "Аккумулятор S4 60Ач", "electrics", "Bosch", 54900, 7, ["camry", "elantra", "tucson", "rio", "cobalt", "granta", "polo"],
     "", [spec("Capacity", "Ёмкость", "60 Ah"), spec("Cold cranking", "Пусковой ток", "540 A"), spec("Polarity", "Полярность", "R+")]),
    ("EL-001", "Varta Blue Dynamic 74Ah", "Аккумулятор Varta Blue Dynamic 74Ач", "electrics", "Varta", 69900, 6, ["prado", "rav4", "sportage", "octavia"],
     "", [spec("Capacity", "Ёмкость", "74 Ah"), spec("Cold cranking", "Пусковой ток", "680 A")]),
    ("EL-002", "Varta Silver Dynamic 100Ah", "Аккумулятор Varta Silver Dynamic 100Ач", "electrics", "Varta", 98900, 3, ["lc200", "prado"],
     "", [spec("Capacity", "Ёмкость", "100 Ah"), spec("Cold cranking", "Пусковой ток", "830 A")]),
    ("EL-003", "Alternator", "Генератор", "electrics", "Valeo", 129900, 2, ["camry", "corolla"],
     "27060-0V010", [spec("Output", "Мощность", "130 A")]),
    ("EL-004", "Starter motor", "Стартер", "electrics", "Denso", 89900, 2, ["camry", "rav4"],
     "28100-0V030", [spec("Power", "Мощность", "1.4 kW")]),
    ("EL-005", "Battery charger Bosch C3 6/12V", "Зарядное устройство Bosch C3 6/12В", "electrics", "Bosch", 29900, 8, ALL,
     "", [spec("Voltage", "Напряжение", "6 / 12 V"), spec("Charging current", "Ток заряда", "3.8 A")]),
    # --- cooling ---
    ("CO-001", "Radiator", "Радиатор охлаждения", "cooling", "Valeo", 64900, 4, ["elantra", "creta", "rio"],
     "25310-H8000", [spec("Material", "Материал", "Aluminium / Алюминий")]),
    ("CO-002", "Thermostat", "Термостат", "cooling", "Gates", 11900, 15, ["camry", "corolla", "rav4"],
     "90916-03129", [spec("Opening temperature", "Т открытия", "82 °C")]),
    ("CO-003", "Water pump", "Помпа (водяной насос)", "cooling", "Gates", 34900, 6, KOREAN,
     "25100-2B000", [spec("Drive", "Привод", "Belt / Ремень")]),
    ("CO-004", "Timing belt kit with water pump", "Комплект ремня ГРМ с помпой", "cooling", "Gates", 39900, 5, ["granta", "vesta", "nexia", "polo"],
     "", [spec("Includes", "Состав", "Belt + idler + water pump / Ремень + ролик + помпа")]),
    # --- tires ---
    ("TR-001", "Michelin X-Ice North 4 205/55 R16", "Шина Michelin X-Ice North 4 205/55 R16", "tires", "Michelin", 62900, 24, ["elantra", "polo", "cerato"],
     "", [spec("Season", "Сезон", "Winter, studded / Зима, шипы"), spec("Size", "Размер", "205/55 R16")]),
    ("TR-002", "Michelin Primacy 4 215/55 R17", "Шина Michelin Primacy 4 215/55 R17", "tires", "Michelin", 58900, 16, ["camry", "tucson", "k5"],
     "", [spec("Season", "Сезон", "Summer / Лето"), spec("Size", "Размер", "215/55 R17")]),
    ("TR-003", "Nokian Hakkapeliitta 10 225/65 R17", "Шина Nokian Hakkapeliitta 10 225/65 R17", "tires", "Nokian", 79900, 12, ["rav4", "sportage", "tucson", "qashqai"],
     "", [spec("Season", "Сезон", "Winter, studded / Зима, шипы"), spec("Size", "Размер", "225/65 R17")]),
    ("TR-004", "Continental EcoContact 6 185/65 R15", "Шина Continental EcoContact 6 185/65 R15", "tires", "Continental", 39900, 20, ["accent", "rio", "cobalt", "nexia", "granta"],
     "", [spec("Season", "Сезон", "Summer / Лето"), spec("Size", "Размер", "185/65 R15")]),
    ("TR-005", "Continental Viking 265/65 R17", "Шина Continental Viking 265/65 R17", "tires", "Continental", 89900, 8, ["prado", "lc200"],
     "", [spec("Season", "Сезон", "Winter / Зима"), spec("Size", "Размер", "265/65 R17")]),
    # --- body ---
    ("BD-001", "Side mirror glass, heated", "Стекло зеркала с подогревом", "body", "Valeo", 9900, 12, ["camry", "corolla"],
     "", [spec("Side", "Сторона", "Left / Левое"), spec("Heated", "Подогрев", "Yes / Да")]),
    ("BD-002", "Wiper blades Aerotwin 600/475", "Щётки стеклоочистителя Aerotwin 600/475", "body", "Bosch", 12900, 30, ["camry", "elantra", "tucson"],
     "", [spec("Length", "Длина", "600 + 475 mm")]),
    ("BD-003", "Front bumper grille", "Решётка переднего бампера", "body", "Hyundai/Kia Genuine", 22900, 4, ["creta"],
     "86561-M0000", [spec("Original part", "Оригинал", "Yes / Да")]),
    ("BD-004", "Rear wiper blade", "Задняя щётка стеклоочистителя", "body", "Valeo", 4900, 25, ["tucson", "rav4", "sportage", "creta", "qashqai"],
     "", [spec("Length", "Длина", "300 mm")]),
    # --- car care ---
    ("CA-001", "Liqui Moly engine flush", "Промывка двигателя Liqui Moly", "care", "Liqui Moly", 4900, 40, ALL,
     "", [spec("Volume", "Объём", "300 ml")]),
    ("CA-002", "Injector cleaner", "Очиститель инжектора", "care", "Liqui Moly", 5900, 32, ALL,
     "", [spec("Volume", "Объём", "300 ml"), spec("Treats", "На бак", "70 L")]),
    ("CA-003", "Motul car wax", "Автомобильный воск Motul", "care", "Motul", 7900, 20, ALL,
     "", [spec("Volume", "Объём", "500 ml")]),
    # --- accessories ---
    ("AC-001", "Wiper blades Aerotwin 650/400", "Щётки стеклоочистителя Aerotwin 650/400", "body", "Bosch", 12900, 30, ["camry", "elantra", "tucson"],
     "", [spec("Length", "Длина", "650 + 400 mm")]),
    ("AC-003", "All-weather floor mats", "Всесезонные коврики", "accessories", "Toyota Genuine", 19900, 14, ["camry", "prado"],
     "", [spec("Material", "Материал", "Rubber / Резина"), spec("Quantity", "Количество", "4 pcs / шт")]),
    ("AC-004", "Phone holder for air vent", "Держатель телефона на дефлектор", "accessories", "Baseus", 5900, 40, ALL,
     "", [spec("Mount", "Крепление", "Air vent / Дефлектор")]),
    ("AC-005", "Emergency kit (triangle, first aid, extinguisher)", "Аварийный набор (знак, аптечка, огнетушитель)", "accessories", "AIRLINE", 14900, 18, ALL,
     "", [spec("Includes", "Состав", "3 items / 3 предмета")]),
    ("AC-006", "Trunk organizer", "Органайзер в багажник", "accessories", "AIRLINE", 9900, 15, ALL,
     "", [spec("Size", "Размер", "60 × 30 × 25 cm")]),
    ("AC-007", "Portable air compressor 35 L/min", "Автомобильный компрессор 35 л/мин", "accessories", "AIRLINE", 16900, 12, ALL,
     "", [spec("Flow", "Производительность", "35 L/min / л/мин"), spec("Power", "Питание", "12 V")]),
    ("AC-008", "Jumper cables 400 A, 3 m", "Провода прикуривания 400А, 3 м", "accessories", "AIRLINE", 7900, 20, ALL,
     "", [spec("Current", "Ток", "400 A"), spec("Length", "Длина", "3 m")]),
    ("AC-009", "Telescopic snow brush with ice scraper", "Щётка-скребок для снега телескопическая", "accessories", "AIRLINE", 4500, 35, ALL,
     "", [spec("Length", "Длина", "68–98 cm")]),
    ("AC-010", "Car charger USB-C + USB-A 30 W", "Автомобильное зарядное USB-C/USB-A 30 Вт", "accessories", "Baseus", 6900, 25, ALL,
     "", [spec("Ports", "Разъёмы", "USB-C + USB-A"), spec("Power", "Мощность", "30 W")]),
]

# Permanent suppliers. Names, people and e-mails are FICTIONAL (course project); no phone numbers on purpose.
# key, name, contact person, e-mail, prefix of opening receipt numbers
SUPPLIERS = [
    ("dala", "ТОО «Дала Авто Трейд»", "Ерлан Сапаров", "sales@dala-autotrade.kz", "DAT"),
    ("volt", "ТОО «ВольтЛайн Казахстан»", "Айгерим Нурланова", "orders@voltline.kz", "VL"),
    ("style", "ТОО «АвтоСтиль Центр»", "Дмитрий Ким", "info@autostyle-center.kz", "ASC"),
]

# Which supplier brings the opening stock of each category (every slug of CATEGORIES must be here)
CATEGORY_SUPPLIER = {
    # consumables and brakes
    "brakes": "dala", "engine-oil": "dala", "filters": "dala", "cooling": "dala", "suspension": "dala",
    # electrics and lighting
    "electrics": "volt", "lighting": "volt", "ignition": "volt",
    # accessories (body parts, car care and tyres are placed here too)
    "accessories": "style", "care": "style", "body": "style", "tires": "style",
}

# Demo reviewers and reviews (sku, reviewer, stars, text)
DEMO_REVIEWERS = [("aliya", "Aliya", "N."), ("timur", "Timur", "S."), ("dana", "Dana", "K.")]
DEMO_REVIEWS = [
    ("BR-001", "aliya", 5, "Quiet and no dust. Fit my Camry 2020 perfectly."),
    ("BR-001", "timur", 4, "Good pads, a bit pricey."),
    ("BR-001", "dana", 5, "Отличные колодки, тормозят мягко."),
    ("OIL-001", "timur", 5, "Engine runs smoother, using it for 2 years."),
    ("OIL-001", "dana", 4, "Хорошее масло, но в другом магазине дешевле."),
    ("FL-004", "aliya", 5, "Original Toyota part, exact fit."),
    ("LT-001", "dana", 3, "Brighter than stock, but they burned out after a year."),
    ("LT-001", "timur", 4, "Noticeably brighter at night."),
    ("TR-003", "aliya", 5, "Best winter tires I have had. Great on ice in Astana."),
    ("IG-001", "timur", 5, "Cold start at −25 °C without problems."),
    ("AC-002", "dana", 4, "Started the car every morning this winter."),
    ("SU-001", "aliya", 4, "The car is much more stable on bumps now."),
]
