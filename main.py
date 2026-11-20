import asyncio
import logging
from urllib.parse import quote

import aiohttp

from aiogram import types
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, KeyboardButton, Message,
                           ReplyKeyboardMarkup)

import db

# --- НАСТРОЙКИ ---
TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"
ADMIN_ID = 1447033355

# На PythonAnywhere — True (прокси обязателен). Локально поставь False.
USE_PROXY = True
PROXY = "http://proxy.server:3128"

session = AiohttpSession(proxy=PROXY if USE_PROXY else None)
bot = Bot(token=TOKEN, session=session,
          default=DefaultBotProperties(parse_mode="HTML"))

router = Router()

# --- Киберпанк-стиль ---
HEADER = ("🌌 <b>PS5 GAME STORE</b> 🌌\n"
          "⚡ <i>Игры будущего уже здесь</i> ⚡\n"
          "─────────────────────────\n")
DIVIDER = "\n─────────────────────────\n"

AGE_BADGES = {"3+": "🟢 3+", "12+": "🟡 12+", "16+": "🟠 16+", "18+": "🔞 18+"}

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"


def fmt(n):
    return f"{n:,}".replace(",", " ")


def age_badge(age):
    return AGE_BADGES.get(age, "❓ без рейтинга")


def price_line(price, old_price):
    if old_price and old_price > price:
        disc = round((1 - price / old_price) * 100)
        return f"<s>{fmt(old_price)} ₽</s> → <b>{fmt(price)} ₽</b> (−{disc}%)"
    return f"<b>{fmt(price)} ₽</b>"


def product_text(p):
    return (f"{HEADER}"
            f"<b>{p['name']}</b>\n"
            f"🎯 {age_badge(p['age_limit'])}"
            f"{DIVIDER}"
            f"{p['description'] or 'Описание скоро появится.'}"
            f"{DIVIDER}"
            f"💰 Цена: {price_line(p['price'], p['old_price'])}")


def product_kb(p, user_id):
    fav_label = "💔 Убрать из избранного" if db.is_fav(user_id, p["id"]) else "⭐ В избранное"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_{p['id']}")],
        [InlineKeyboardButton(text=fav_label, callback_data=f"fav_{p['id']}")],
    ])


# --- Живые постеры: обложка берётся с Википедии и кэшируется в базу ---
async def get_cover(p):
    if p["image_url"]:
        return p["image_url"]
    title = p["wiki_title"]
    if not title:
        return None
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                    WIKI_API + quote(title),
                    proxy=PROXY if USE_PROXY else None,
                    timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    img = ((data.get("originalimage") or {}).get("source")
                           or (data.get("thumbnail") or {}).get("source"))
                    if img:
                        db.set_image_url(p["id"], img)
                        return img
    except Exception as e:
        logging.warning(f"Обложка «{title}» не найдена: {e}")
    return None


async def send_product_card(message: Message, p):
    kb = product_kb(p, message.from_user.id)
    text = product_text(p)
    cover = await get_cover(p)
    if cover:
        try:
            await message.answer_photo(photo=cover, caption=text[:1024],
                                       reply_markup=kb)
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=kb)


def list_kb(items, back_cb="to_main", back_label="⬅️ В главное меню"):
    rows = [[InlineKeyboardButton(
        text=f"{AGE_BADGES.get(p['age_limit'], '❓')} {p['name']} — {fmt(p['price'])} ₽"
             + (f" 🏷" if p["old_price"] else ""),
        callback_data=f"prod_{p['id']}")] for p in items]
    rows.append([InlineKeyboardButton(text=back_label, callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# --- Клавиатуры ---
MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔥 Хиты продаж"), KeyboardButton(text="🆕 Новинки")],
        [KeyboardButton(text="💸 Скидки"), KeyboardButton(text="💰 До 1000 ₽")],
        [KeyboardButton(text="🎮 Каталог игр"), KeyboardButton(text="🌐 Все игры")],
        [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="⭐ Избранное")],
        [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="📦 Мои заказы"), KeyboardButton(text="⚙️ Админ-панель")],
    ],
    resize_keyboard=True,
)


class SearchStates(StatesGroup):
    waiting_query = State()


class CheckoutStates(StatesGroup):
    waiting_contact = State()


class AddCategory(StatesGroup):
    waiting_name = State()


class AddGame(StatesGroup):
    waiting_name = State()
    waiting_price = State()
    waiting_age = State()
    waiting_desc = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    db.get_or_create_user(message.from_user.id, message.from_user.full_name)
    with open("banner_shop.png", "rb") as f:
        await message.answer_photo(
            types.BufferedInputFile(
                f.read(), filename="banner.png"))

    await message.answer(
        f"{HEADER}"
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Добро пожаловать в магазин игр для PS5.\n"
        "Хиты, новинки, скидки и подписки — всё в меню ниже 👇",
        reply_markup=MAIN_MENU)


# --- Хиты продаж: 2 постера + «Показать все» ---
@router.message(F.text == "🔥 Хиты продаж")
async def hits_menu(message: Message):
    await message.answer(f"{HEADER}🔥 <b>Хиты продаж</b>\nСамое покупаемое прямо сейчас:")
    for p in db.get_hit_posters():
        await send_product_card(message, p)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Показать все хиты", callback_data="hits_all")],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="to_main")],
    ])
    await message.answer("Каждый из этих хитов — топ продаж месяца. "
                         "Показать остальные?", reply_markup=kb)


@router.callback_query(F.data == "hits_all")
async def hits_all(call: CallbackQuery):
    hits = db.get_hits()
    kb = list_kb(hits, back_cb="to_main", back_label="⬅️ В главное меню")
    await call.message.answer(f"{HEADER}🔥 <b>Все хиты продаж</b>:", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data == "to_main")
async def to_main(call: CallbackQuery):
    await call.message.answer("Главное меню 👇", reply_markup=MAIN_MENU)
    await call.answer()


# --- Новинки ---
@router.message(F.text == "🆕 Новинки")
async def new_games(message: Message):
    items = db.get_new_products()
    if not items:
        await message.answer("Новинок пока нет 🤷")
        return
    await message.answer(f"{HEADER}🆕 <b>Новинки</b>\nСвежие релизы для PS5:",
                         reply_markup=list_kb(items))


# --- Скидки ---
@router.message(F.text == "💸 Скидки")
async def discounted(message: Message):
    items = db.get_discounted()
    if not items:
        await message.answer("Скидок сейчас нет 🤷")
        return
    await message.answer(f"{HEADER}💸 <b>Скидки</b>\nИгры по сниженным ценам:",
                         reply_markup=list_kb(items))


# --- До 1000 ₽ ---
@router.message(F.text == "💰 До 1000 ₽")
async def under_1000(message: Message):
    items = db.get_under(1000)
    if not items:
        await message.answer("Товаров до 1000 ₽ пока нет 🤷")
        return
    await message.answer(f"{HEADER}💰 <b>До 1000 ₽</b>\nНедорогой контент:",
                         reply_markup=list_kb(items))


# --- Каталог по категориям ---
@router.message(F.text == "🎮 Каталог игр")
async def show_catalog(message: Message):
    cats = db.get_categories()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📂 {c['name']}", callback_data=f"cat_{c['id']}")]
        for c in cats])
    await message.answer(f"{HEADER}Выбери категорию:", reply_markup=kb)


@router.callback_query(F.data.startswith("cat_"))
async def show_products(call: CallbackQuery):
    products = db.get_products(int(call.data.split("_")[1]))
    if not products:
        await call.message.edit_text("В этой категории пока пусто 🤷")
        await call.answer()
        return
    kb = list_kb(products, back_cb="back_cats", back_label="⬅️ Назад")
    await call.message.edit_text(f"{HEADER}Игры категории:", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data == "back_cats")
async def back_to_categories(call: CallbackQuery):
    cats = db.get_categories()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📂 {c['name']}", callback_data=f"cat_{c['id']}")]
        for c in cats])
    await call.message.edit_text(f"{HEADER}Выбери категорию:", reply_markup=kb)
    await call.answer()


# --- Все игры PlayStation (с листанием) ---
@router.message(F.text == "🌐 Все игры")
async def all_games(message: Message):
    await send_games_page(message, 0)


async def send_games_page(message: Message, page):
    per_page = 10
    items = db.get_all_games(per_page, page * per_page)
    total = len(db.get_all_games(999, 0))
    if not items:
        await message.answer("Игры закончились 🤷")
        return
    rows = [[InlineKeyboardButton(
        text=f"{AGE_BADGES.get(p['age_limit'], '❓')} {p['name'][:30]} — {fmt(p['price'])} ₽",
        callback_data=f"prod_{p['id']}")] for p in items]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"allgames_{page - 1}"))
    if (page + 1) * per_page < total:
        nav.append(InlineKeyboardButton(text="Далее ➡️", callback_data=f"allgames_{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="⬅️ В главное меню", callback_data="to_main")])
    await message.answer(
        f"{HEADER}🌐 <b>Все игры PlayStation</b>\n"
        f"Страница {page + 1} из -{(total + per_page - 1) // per_page}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.startswith("allgames_"))
async def all_games_page(call: CallbackQuery):
    await send_games_page(call.message, int(call.data.split("_")[1]))
    await call.answer()


# --- Карточка товара ---
@router.callback_query(F.data.startswith("prod_"))
async def show_product(call: CallbackQuery):
    product = db.get_product(int(call.data.split("_")[1]))
    if not product:
        await call.answer("Товар не найден", show_alert=True)
        return
    await send_product_card(call.message, product)
    await call.answer()


@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(call: CallbackQuery):
    db.add_to_cart(call.from_user.id, int(call.data.split("_")[1]))
    await call.answer("Добавлено в корзину ✅", show_alert=True)


# --- Избранное ---
@router.callback_query(F.data.startswith("fav_"))
async def toggle_fav(call: CallbackQuery):
    is_now_fav = db.toggle_fav(call.from_user.id, int(call.data.split("_")[1]))
    await call.answer("Добавлено в избранное ⭐" if is_now_fav
                      else "Убрано из избранного 💔", show_alert=True)


@router.message(F.text == "⭐ Избранное")
async def favorites_list(message: Message):
    items = db.get_favorites(message.from_user.id)
    if not items:
        await message.answer("В избранном пусто 🤷\nЖми ⭐ на карточке игры, чтобы добавить.")
        return
    kb = list_kb(items)
    await message.answer(f"{HEADER}⭐ <b>Избранное</b> ({len(items)}):", reply_markup=kb)


# --- Поиск ---
@router.message(F.text == "🔍 Поиск")
async def search_start(message: Message, state: FSMContext):
    await state.set_state(SearchStates.waiting_query)
    await message.answer("🔍 Что ищем? Напиши название игры\n(например: Cyberpunk или GTA):")


@router.message(SearchStates.waiting_query, F.text)
async def search_do(message: Message, state: FSMContext):
    await state.clear()
    found = db.search_products(message.text.strip())
    if not found:
        await message.answer("Ничего не нашёл 🤷 Попробуй другое слово.")
        return
    await message.answer(f"{HEADER}Найдено: {len(found)}",
                         reply_markup=list_kb(found))


# --- Корзина ---
def build_cart(items):
    total = sum(r["price"] * r["qty"] for r in items)
    text = f"{HEADER}🛒 <b>Корзина:</b>\n\n"
    rows = []
    for r in items:
        text += f"• {r['name']} × {r['qty']} — {fmt(r['price'] * r['qty'])} ₽\n"
        rows.append([
            InlineKeyboardButton(text="➖", callback_data=f"qminus_{r['id']}"),
            InlineKeyboardButton(text=f"{r['name'][:18]} ×{r['qty']}", callback_data="noop"),
            InlineKeyboardButton(text="➕", callback_data=f"qplus_{r['id']}"),
        ])
    text += f"\n<b>Итого: {fmt(total)} ₽</b>"
    rows.append([
        InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout"),
        InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_cart"),
    ])
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    items = db.get_cart(message.from_user.id)
    if not items:
        await message.answer("Корзина пуста 🤷 Загляни в 🔥 Хиты продаж!")
        return
    text, kb = build_cart(items)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("qplus_") | F.data.startswith("qminus_"))
async def cart_qty(call: CallbackQuery):
    action, pid = call.data.split("_", 1)
    db.change_qty(call.from_user.id, int(pid), 1 if action == "qplus" else -1)
    items = db.get_cart(call.from_user.id)
    if not items:
        await call.message.edit_text("Корзина пуста 🤷")
    else:
        text, kb = build_cart(items)
        await call.message.edit_text(text, reply_markup=kb)
    await call.answer()


@router.callback_query(F.data == "noop")
async def noop(call: CallbackQuery):
    await call.answer()


@router.callback_query(F.data == "clear_cart")
async def clear_cart(call: CallbackQuery):
    db.clear_cart(call.from_user.id)
    await call.message.edit_text("Корзина очищена 🗑")
    await call.answer()


@router.callback_query(F.data == "checkout")
async def checkout(call: CallbackQuery, state: FSMContext):
    items = db.get_cart(call.from_user.id)
    if not items:
        await call.answer("Корзина пуста", show_alert=True)
        return
    await state.set_state(CheckoutStates.waiting_contact)
    await call.message.edit_text(
        "💳 <b>Оформление заказа</b>\n\n"
        "Напиши одним сообщением имя и телефон для связи.\n"
        "<i>Например: Иван, +7 900 123-45-67</i>")
    await call.answer()


@router.message(CheckoutStates.waiting_contact, F.text)
async def checkout_contact(message: Message, state: FSMContext):
    contact = message.text.strip()
    cart_items = db.get_cart(message.from_user.id)
    order_id, total = db.create_order(message.from_user.id, contact)
    await state.clear()
    if not order_id:
        await message.answer("Корзина пуста, заказ не оформлен 🤷", reply_markup=MAIN_MENU)
        return
    lines = "\n".join(f"• {i['name']} × {i['qty']} — {fmt(i['price'] * i['qty'])} ₽"
                      for i in cart_items)
    await message.answer(
        f"{HEADER}"
        f"✅ <b>Заказ №{order_id} оформлен!</b>\n\n"
        f"📦 Состав:\n{lines}\n\n"
        f"💰 Итого: <b>{fmt(total)} ₽</b>\n"
        f"👤 Контакт: {contact}"
        f"{DIVIDER}"
        "Менеджер свяжется с тобой в ближайшее время 📞",
        reply_markup=MAIN_MENU)
    admin_text = (
        f"🆕 <b>НОВЫЙ ЗАКАЗ №{order_id}</b>\n"
        f"👤 От: {message.from_user.full_name} (id {message.from_user.id})\n"
        f"📞 Контакт: {contact}"
        f"{DIVIDER}"
        f"📦 <b>Состав заказа:</b>\n{lines}\n\n"
        f"💰 Итого: <b>{fmt(total)} ₽</b>")
    for attempt in range(1, 4):
        try:
            await bot.send_message(ADMIN_ID, admin_text)
            break
        except Exception as e:
            logging.warning(f"Попытка {attempt}/3 уведомления о заказе №{order_id}: {e}")
            if attempt < 3:
                await asyncio.sleep(2 ** attempt)
            else:
                logging.error(f"Не удалось уведомить админа о заказе №{order_id}!")


# --- Мои заказы ---
@router.message(F.text == "📦 Мои заказы")
async def my_orders(message: Message):
    orders = db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("Заказов пока нет 🤷")
        return
    text = f"{HEADER}📦 <b>Твои заказы:</b>\n\n"
    for o in orders:
        text += f"№{o['id']} • {o['created']} • {fmt(o['total'])} ₽ • {o['status']}\n"
        for it in db.get_order_items(o["id"]):
            text += f"   — {it['name']} × {it['qty']}\n"
        text += "\n"
    await message.answer(text)


# --- Профиль ---
@router.message(F.text == "👤 Профиль")
async def profile(message: Message):
    stats = db.get_user_stats(message.from_user.id)
    await message.answer(
        f"{HEADER}👤 <b>Профиль</b>"
        f"{DIVIDER}"
        f"🎮 Ник: {message.from_user.full_name}\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"📅 В магазине с: {stats['reg_date']}\n"
        f"🧾 Заказов: {stats['orders']}\n"
        f"💰 Куплено на: {fmt(stats['spent'])} ₽")


# --- Админ-панель ---
def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats")],
        [InlineKeyboardButton(text="📋 Все заказы", callback_data="adm_orders")],
        [InlineKeyboardButton(text="📂 Добавить категорию", callback_data="adm_addcat")],
        [InlineKeyboardButton(text="🎮 Добавить игру", callback_data="adm_addgame")],
    ])


def is_admin(user_id):
    return user_id == ADMIN_ID


@router.message(F.text == "⚙️ Админ-панель")
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ только для администратора.")
        return
    await message.answer(f"{HEADER}⚙️ <b>Панель администратора</b>", reply_markup=admin_kb())


@router.callback_query(F.data == "adm_stats")
async def adm_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    users, products, orders, revenue = db.get_stats()
    await call.message.edit_text(
        f"{HEADER}📊 <b>Статистика</b>\n\n"
        f"👥 Пользователей: {users}\n"
        f"🎮 Товаров: {products}\n"
        f"🧾 Заказов: {orders}\n"
        f"💰 Выручка: {fmt(revenue)} ₽")
    await call.answer()


@router.callback_query(F.data == "adm_orders")
async def adm_orders(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    orders = db.get_all_orders()
    if not orders:
        await call.message.edit_text("Заказов пока нет 🤷")
        await call.answer()
        return
    text = f"{HEADER}📋 <b>Последние заказы:</b>\n\n"
    for o in orders:
        text += (f"№{o['id']} • {o['created']} • {fmt(o['total'])} ₽ • {o['status']}\n"
                 f"   {o['uname'] or 'клиент'}, контакт: {o['contact']}\n\n")
    await call.message.edit_text(text)
    await call.answer()


@router.callback_query(F.data == "adm_addcat")
async def adm_addcat(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    await state.set_state(AddCategory.waiting_name)
    await call.message.edit_text("Введи название новой категории:")
    await call.answer()


@router.message(AddCategory.waiting_name, F.text)
async def addcat_name(message: Message, state: FSMContext):
    db.add_category(message.text.strip())
    await state.clear()
    await message.answer(f"Категория «{message.text.strip()}» добавлена ✅",
                         reply_markup=MAIN_MENU)


@router.callback_query(F.data == "adm_addgame")
async def adm_addgame(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    cats = db.get_categories()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=c["name"], callback_data=f"pickcat_{c['id']}")]
        for c in cats])
    await call.message.edit_text("В какую категорию добавить товар?", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("pickcat_"))
async def pick_cat(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Нет доступа", show_alert=True)
        return
    await state.update_data(cat_id=int(call.data.split("_")[1]))
    await state.set_state(AddGame.waiting_name)
    await call.message.edit_text("Введи название товара:")
    await call.answer()


@router.message(AddGame.waiting_name, F.text)
async def addgame_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddGame.waiting_price)
    await message.answer("Введи цену в рублях (только число):")


@router.message(AddGame.waiting_price, F.text)
async def addgame_price(message: Message, state: FSMContext):
    raw = message.text.strip().replace(" ", "")
    if not raw.isdigit():
        await message.answer("Цена должна быть числом. Попробуй ещё раз:")
        return
    await state.update_data(price=int(raw))
    await state.set_state(AddGame.waiting_age)
    await message.answer("Введи возрастной рейтинг (3+, 12+, 16+ или 18+):")


@router.message(AddGame.waiting_age, F.text)
async def addgame_age(message: Message, state: FSMContext):
    age = message.text.strip().replace(" ", "")
    if age not in AGE_BADGES:
        await message.answer("Рейтинг: 3+, 12+, 16+ или 18+. Попробуй ещё раз:")
        return
    await state.update_data(age=age)
    await state.set_state(AddGame.waiting_desc)
    await message.answer("Введи описание товара (или «-» чтобы без описания):")


@router.message(AddGame.waiting_desc, F.text)
async def addgame_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    desc = None if message.text.strip() == "-" else message.text.strip()
    db.add_product(data["cat_id"], data["name"], data["price"], data["age"], desc)
    await state.clear()
    await message.answer(f"«{data['name']}» ({fmt(data['price'])} ₽) добавлено ✅",
                         reply_markup=MAIN_MENU)


# --- Прочее ---
@router.message(F.text == "/cancel")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменил действие 👌", reply_markup=MAIN_MENU)


@router.message(F.text)
async def unknown(message: Message):
    await message.answer("Не понял 🙈 Используй кнопки меню ниже.", reply_markup=MAIN_MENU)


# --- Запуск с автоперезапуском ---
async def main():
    logging.basicConfig(level=logging.INFO)
    db.create_db()
    dp = Dispatcher()
    dp.include_router(router)
    while True:
        try:
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Сбой: {e}. Перезапуск через 10 секунд...")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())

@dp.message(F.photo)
async def save_poster(message: Message):
    if message.from_user.id != ADMIN_ID or not message.caption:
        return
    name = message.caption.strip()
    if db.set_poster(name, message.photo[-1].file_id):
        await message.answer(f"Постер для «{name}» сохранён ✅")
    else:
        await message.answer(f"Игра «{name}» не найдена. Название должно совпадать с каталогом точь-в-точь.")
