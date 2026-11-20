import sqlite3
from datetime import datetime

DB_NAME = "shop.db"

CATEGORIES = [
    (1, "Экшены и RPG"),
    (2, "Гонки и спорт"),
    (3, "Файтинги"),
    (4, "Инди-хиты до 1000 ₽"),
    (5, "Подписки"),
]

# (категория, название, цена, старая цена, возраст, хит, новинка, топ-постер, вики-статья, описание)
GAMES = [
    (1, "Grand Theft Auto VI", 6999, 0, "18+", 1, 1, 1, "Grand Theft Auto VI",
     "Вайс-Сити и штат Леонида ждут. Самый громкий релиз года от Rockstar: Люсия и Джейсон, огромный открытый мир и безумие уровня культурного события."),
    (1, "Ghost of Yōtei: Complete Edition", 5499, 0, "18+", 1, 1, 2, "Ghost of Yōtei",
     "Самурайская сага от студии Sucker Punch. Месть, снег, кленовые рощи и свобода исследования феодальной Японии."),
    (1, "Marvel's Wolverine", 5999, 0, "18+", 1, 1, 0, "Marvel's Wolverine",
     "Росомаха от Insomniac Games. Жестокий экшен про Джеймса Хоулетта с фирменными когтями и мрачным сюжетом."),
    (1, "Cyberpunk 2077: Ultimate Edition", 4499, 5999, "18+", 1, 0, 0, "Cyberpunk 2077",
     "Найт-Сити во всей красе: Phantom Liberty, импланты, неон и сюжет, который меняется от твоих решений."),
    (1, "God of War: Ragnarök", 5499, 0, "18+", 1, 0, 0, "God of War Ragnarök",
     "Финал скандинавской саги Кратоса и Атрея. Грандиозные битвы, драма и эталонная графика PS5."),
    (1, "Marvel's Spider-Man 2", 5499, 5999, "16+", 1, 0, 0, "Marvel's Spider-Man 2",
     "Два Человека-Паука, Нью-Йорк и Веном. Мгновенные переключения между Питером и Майлзом прямо в полёте."),
    (1, "Elden Ring", 4499, 0, "16+", 1, 0, 0, "Elden Ring",
     "Мрачное фэнтези от создателей Dark Souls. Огромный открытый мир и коварные боссы."),
    (1, "The Last of Us Part II Remastered", 4499, 5499, "18+", 0, 0, 0, "The Last of Us Part II",
     "Жестокая история мести в мире после апокалипсиса. Ремастер с режимом No Return."),
    (1, "Horizon Forbidden West", 4999, 5999, "16+", 0, 0, 0, "Horizon Forbidden West",
     "Приключение Элой: механические звери, племена Запретного Запада и потрясающие пейзажи."),
    (1, "Ghost of Tsushima Director's Cut", 4499, 0, "18+", 0, 0, 0, "Ghost of Tsushima",
     "Защищай Цусиму от монгольского вторжения с катаной в руках. Стиль и дух самурайского кино."),
    (1, "Resident Evil Requiem", 4999, 0, "18+", 0, 1, 0, "Resident Evil Requiem",
     "Новая глава хоррор-серии Capcom. Туман, монстры и удушающая атмосфера от первого лица."),
    (1, "Control Resonant", 4999, 0, "16+", 0, 1, 0, "Control Resonant",
     "Сиквел cultового Control от Remedy: ролевой экшен, паранормальный Нью-Йорк и свобода выбора."),
    (1, "Onimusha: Way of the Sword", 4499, 0, "18+", 0, 1, 0, "Onimusha: Way of the Sword",
     "Самурай-слэшер в фэнтезийном Киото эпохи Эдо. Меч, парирования и демоны."),
    (1, "The Blood of Dawnwalker", 4499, 0, "18+", 0, 1, 0, "The Blood of Dawnwalker",
     "Тёмное фэнтези от ветеранов The Witcher 3: полувампир Коэн, день и ночь решают всё."),
    (1, "Helldivers 2", 3499, 0, "18+", 1, 0, 0, "Helldivers 2",
     "Кооперативный шутер за свободу галактики. Орбитальные удары и никакой поодиночке."),
    (1, "Hogwarts Legacy", 3999, 4999, "16+", 1, 0, 0, "Hogwarts Legacy",
     "Открытый мир Хогвартса XIX века: колдовство, замок, тайны и собственная история мага."),
    (2, "Gran Turismo 7", 5499, 0, "3+", 1, 0, 0, "Gran Turismo 7",
     "Эталонный автосимулятор: сотни машин, динамическая погода и фотореализм."),
    (2, "EA SPORTS FC 27", 5999, 0, "3+", 1, 1, 0, "EA Sports FC 27",
     "Новый футбольный симулятор EA: обновлённая анимация, динамические стандарты, карьера и Ultimate Team."),
    (2, "F1 25", 4499, 0, "3+", 0, 0, 0, "F1 25",
     "Официальная игра Формулы-1: реалистичная физика болидов и все трассы чемпионата."),
    (3, "Mortal Kombat 1", 4499, 5499, "18+", 1, 0, 0, "Mortal Kombat 1",
     "Перезапуск легенды: жестокие добивания, камео-бойцы и кинематографичный сюжет."),
    (3, "Tekken 8", 4499, 0, "16+", 1, 0, 0, "Tekken 8",
     "Файтинг на Unreal Engine 5. Классические персонажи и агрессивный агрессивный геймплей."),
    (3, "Street Fighter 6", 3999, 4499, "16+", 0, 0, 0, "Street Fighter 6",
     "Культовый файтинг Capcom: World Tour,.drive Gauge и огромная сцена онлайн-боёв."),
    (4, "Hades II", 990, 0, "12+", 1, 1, 0, "Hades II",
     "Сестра Загрея против титанов. Лучший рогалик года и идеальный таймкиллер."),
    (4, "Hollow Knight", 499, 0, "12+", 0, 0, 0, "Hollow Knight",
     "Шедевральный метроидвения про королевство насекомых. Красиво и сурово."),
    (4, "Celeste", 499, 0, "12+", 0, 0, 0, "Celeste (video game)",
     "Платформер о подъёме на гору и о себе. Тонкая история и отточенная механика."),
    (4, "Dead Cells", 599, 0, "12+", 0, 0, 0, "Dead Cells",
     "Рогалик-экшен с мечом и вышивальной энергией. Каждая смерть — новое начало."),
    (4, "Stray", 990, 0, "12+", 0, 0, 0, "Stray (video game)",
     "Игра за кота в кибер-городе роботов. Мило, атмосферно и очень по-кошачьи."),
    (4, "Sifu", 999, 1299, "16+", 0, 0, 0, "Sifu (video game)",
     "Хардкорный боевик о мести: стареешь с каждой смертью, а мастерство растёт."),
    (4, "Vampire Survivors", 299, 0, "12+", 0, 0, 0, "Vampire Survivors",
     "Затягивающий буллет-хелл. Ты просто нажимаешь стрелки, а часы исчезают."),
    (4, "Untitled Goose Game", 599, 0, "3+", 0, 0, 0, "Untitled Goose Game",
     "Ты — гадкий гусь. Твоя миссия — портить день всем вокруг. Комично и отлично."),
    (5, "PS Plus Essential — 1 мес", 660, 0, "3+", 1, 0, 0, "PlayStation Plus",
     "Онлайн-мультиплеер, ежемесячные игры, облачные сохранения и скидки в магазине."),
    (5, "PS Plus Essential — 3 мес", 1700, 0, "3+", 0, 0, 0, "PlayStation Plus",
     "То же, что и месячный, но выгоднее в пересчёте на месяц."),
    (5, "PS Plus Essential — 12 мес", 4800, 0, "3+", 0, 0, 0, "PlayStation Plus",
     "Годовой тариф Essential: максимум экономии для мультиплеера и раздач."),
    (5, "PS Plus Extra — 1 мес", 1000, 0, "3+", 1, 0, 0, "PlayStation Plus",
     "Каталог из 400+ игр PS4 и PS5, включая эксклюзивы Sony и Ubisoft+ Classics."),
    (5, "PS Plus Extra — 3 мес", 2750, 0, "3+", 0, 0, 0, "PlayStation Plus",
     "Три месяца каталога Extra — популярный выбор активных геймеров."),
    (5, "PS Plus Extra — 12 мес", 8000, 0, "3+", 0, 0, 0, "PlayStation Plus",
     "Год каталога Extra: доступ к сотням игр без отдельных покупок."),
    (5, "PS Plus Deluxe — 1 мес", 1180, 0, "3+", 1, 0, 0, "PlayStation Plus",
     "Каталог Extra + классика PS1/PS2/PSP и пробные версии новинок."),
    (5, "PS Plus Deluxe — 3 мес", 3250, 0, "3+", 0, 0, 0, "PlayStation Plus",
     "Три месяца максимального тарифа: каталог, ретро и демо новинок."),
    (5, "PS Plus Deluxe — 12 мес", 9250, 0, "3+", 0, 0, 0, "PlayStation Plus",
     "Год Deluxe: ретро-библиотека, пробники новинок и всё из Extra."),
    (5, "EA Play — 1 мес", 299, 0, "3+", 1, 0, 0, "EA Play",
     "Каталог The Play List: FC, Battlefield, Star Wars и часы игры за 299 ₽."),
    (5, "EA Play — 12 мес", 1799, 0, "3+", 0, 0, 0, "EA Play",
     "Год EA Play — почти в два раза выгоднее помесячной оплаты."),
    (5, "EA Play Pro — 1 мес", 999, 0, "3+", 0, 0, 0, "EA Play",
     "Pro-уровень: новинки EA с первого дня и полные deluxe-версии."),
    (5, "EA Play Pro — 12 мес", 5999, 0, "3+", 0, 0, 0, "EA Play",
     "Годовой EA Play Pro для тех, кто хочет всё и сразу."),
]


def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        price INTEGER NOT NULL,
        old_price INTEGER DEFAULT 0,
        description TEXT,
        image_url TEXT DEFAULT '',
        age_limit TEXT DEFAULT '',
        is_hit INTEGER DEFAULT 0,
        is_new INTEGER DEFAULT 0,
        is_top INTEGER DEFAULT 0,
        wiki_title TEXT DEFAULT '')""")
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        reg_date TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS cart (
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        qty INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (user_id, product_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS favorites (
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        PRIMARY KEY (user_id, product_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total INTEGER NOT NULL,
        contact TEXT,
        status TEXT DEFAULT 'новый',
        created TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        name TEXT,
        price INTEGER,
        qty INTEGER)""")

       # Миграция старой базы: добавляем недостающие колонки
    pcols = {r[1] for r in cur.execute("PRAGMA table_info(products)")}
    for col, coltype, dflt in [
        ("old_price", "INTEGER", "0"),
        ("image_url", "TEXT", "''"),
        ("age_limit", "TEXT", "''"),
        ("is_hit", "INTEGER", "0"),
        ("is_new", "INTEGER", "0"),
        ("is_top", "INTEGER", "0"),
        ("wiki_title", "TEXT", "''"),
    ]:
        if col not in pcols:
            cur.execute(f"ALTER TABLE products ADD COLUMN {col} {coltype} DEFAULT {dflt}")

    tables = {r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if "favorites" not in tables:
        cur.execute("""CREATE TABLE favorites (
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, product_id))""")

    if cur.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        cur.executemany("INSERT INTO categories (id, name) VALUES (?, ?)", CATEGORIES)
        cur.executemany(
            "INSERT INTO products (category_id, name, price, old_price, age_limit, "
            "is_hit, is_new, is_top, wiki_title, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", GAMES)
    conn.commit()
    conn.close()


def get_or_create_user(user_id, name):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO users (user_id, name, reg_date) VALUES (?, ?, ?)",
                 (user_id, name, datetime.now().strftime("%d.%m.%Y")))
    conn.commit()
    conn.close()


# --- Каталог ---

def get_categories():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM categories ORDER BY id").fetchall()
    conn.close()
    return rows


def add_category(name):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def get_products(category_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM products WHERE category_id = ?",
                        (category_id,)).fetchall()
    conn.close()
    return rows


def get_product(product_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return row


def search_products(query):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM products WHERE name LIKE ? LIMIT 20",
                        (f"%{query}%",)).fetchall()
    conn.close()
    return rows


def get_hit_posters():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM products WHERE is_top > 0 ORDER BY is_top").fetchall()
    conn.close()
    return rows


def get_hits():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM products WHERE is_hit = 1 ORDER BY id").fetchall()
    conn.close()
    return rows


def get_new_products():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM products WHERE is_new = 1 ORDER BY id").fetchall()
    conn.close()
    return rows


def get_discounted():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM products WHERE old_price > price ORDER BY id").fetchall()
    conn.close()
    return rows


def get_under(max_price):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM products WHERE price <= ? ORDER BY price",
                        (max_price,)).fetchall()
    conn.close()
    return rows


def get_all_games(limit, offset):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM products WHERE category_id != 5 "
                        "ORDER BY name LIMIT ? OFFSET ?", (limit, offset)).fetchall()
    conn.close()
    return rows


def set_image_url(product_id, url):
    conn = get_conn()
    conn.execute("UPDATE products SET image_url = ? WHERE id = ?", (url, product_id))
    conn.commit()
    conn.close()


def add_product(category_id, name, price, age_limit, description):
    conn = get_conn()
    conn.execute(
        "INSERT INTO products (category_id, name, price, age_limit, description) "
        "VALUES (?, ?, ?, ?, ?)", (category_id, name, price, age_limit, description))
    conn.commit()
    conn.close()


# --- Корзина ---

def add_to_cart(user_id, product_id):
    conn = get_conn()
    conn.execute("INSERT INTO cart (user_id, product_id, qty) VALUES (?, ?, 1) "
                 "ON CONFLICT(user_id, product_id) DO UPDATE SET qty = qty + 1",
                 (user_id, product_id))
    conn.commit()
    conn.close()


def change_qty(user_id, product_id, delta):
    conn = get_conn()
    row = conn.execute("SELECT qty FROM cart WHERE user_id = ? AND product_id = ?",
                       (user_id, product_id)).fetchone()
    if row:
        new_qty = row["qty"] + delta
        if new_qty <= 0:
            conn.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?",
                         (user_id, product_id))
        else:
            conn.execute("UPDATE cart SET qty = ? WHERE user_id = ? AND product_id = ?",
                         (new_qty, user_id, product_id))
        conn.commit()
    conn.close()


def get_cart(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.id, p.name, p.price, p.old_price, c.qty
        FROM cart c JOIN products p ON p.id = c.product_id
        WHERE c.user_id = ?""", (user_id,)).fetchall()
    conn.close()
    return rows


def clear_cart(user_id):
    conn = get_conn()
    conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# --- Избранное ---

def is_fav(user_id, product_id):
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM favorites WHERE user_id = ? AND product_id = ?",
                       (user_id, product_id)).fetchone()
    conn.close()
    return bool(row)


def toggle_fav(user_id, product_id):
    conn = get_conn()
    if is_fav(user_id, product_id):
        conn.execute("DELETE FROM favorites WHERE user_id = ? AND product_id = ?",
                     (user_id, product_id))
        conn.commit()
        conn.close()
        return False
    conn.execute("INSERT INTO favorites (user_id, product_id) VALUES (?, ?)",
                 (user_id, product_id))
    conn.commit()
    conn.close()
    return True


def get_favorites(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.* FROM favorites f JOIN products p ON p.id = f.product_id
        WHERE f.user_id = ? ORDER BY p.name""", (user_id,)).fetchall()
    conn.close()
    return rows


# --- Заказы ---

def create_order(user_id, contact):
    conn = get_conn()
    items = conn.execute("""
        SELECT p.name, p.price, c.qty
        FROM cart c JOIN products p ON p.id = c.product_id
        WHERE c.user_id = ?""", (user_id,)).fetchall()
    if not items:
        conn.close()
        return None, 0
    total = sum(i["price"] * i["qty"] for i in items)
    cur = conn.execute(
        "INSERT INTO orders (user_id, total, contact, status, created) VALUES (?, ?, ?, ?, ?)",
        (user_id, total, contact, "новый", datetime.now().strftime("%d.%m.%Y %H:%M")))
    order_id = cur.lastrowid
    for i in items:
        conn.execute("INSERT INTO order_items (order_id, name, price, qty) VALUES (?, ?, ?, ?)",
                     (order_id, i["name"], i["price"], i["qty"]))
    conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return order_id, total


def get_user_orders(user_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 10",
                        (user_id,)).fetchall()
    conn.close()
    return rows


def get_order_items(order_id):
    conn = get_conn()
    rows = conn.execute("SELECT name, price, qty FROM order_items WHERE order_id = ?",
                        (order_id,)).fetchall()
    conn.close()
    return rows


def get_all_orders():
    conn = get_conn()
    rows = conn.execute("""
        SELECT o.*, u.name AS uname
        FROM orders o LEFT JOIN users u ON u.user_id = o.user_id
        ORDER BY o.id DESC LIMIT 10""").fetchall()
    conn.close()
    return rows


def get_stats():
    conn = get_conn()
    users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    revenue = conn.execute("SELECT COALESCE(SUM(total), 0) FROM orders").fetchone()[0]
    conn.close()
    return users, products, orders, revenue


def get_user_stats(user_id):
    conn = get_conn()
    u = conn.execute("SELECT name, reg_date FROM users WHERE user_id = ?",
                     (user_id,)).fetchone()
    o = conn.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM orders WHERE user_id = ?",
                     (user_id,)).fetchone()
    conn.close()
    return {
        "name": u["name"] if u else None,
        "reg_date": u["reg_date"] if u else "—",
        "orders": o[0],
        "spent": o[1],
    }

def set_poster(name: str, file_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("UPDATE products SET image_url = ? WHERE name = ?",
                           (file_id, name))
        return cur.rowcount > 0
