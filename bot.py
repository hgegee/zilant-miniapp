"""
ZILANT RENTAL — Telegram-бот + Mini App
Прокат премиум-авто в Казани

Запуск: python bot.py
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    MenuButtonWebApp,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from dotenv import load_dotenv

from data import (
    ADVANTAGES,
    BODIES,
    BRANDS,
    CARS,
    CONDITIONS,
    FAQ,
    PHONE,
    PLANS,
    calc_days,
    calc_discount,
    car_name,
    format_price,
    get_car,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
# URL мини-приложения (HTTPS). Пример: https://your-domain.com/ или https://xxx.github.io/zilant/
WEBAPP_URL = os.getenv("WEBAPP_URL", "").rstrip("/") + "/" if os.getenv("WEBAPP_URL") else ""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


# ─────────────────────── FSM (чат-бронирование) ───────────────────────
class Booking(StatesGroup):
    car = State()
    from_date = State()
    to_date = State()
    name = State()
    phone = State()
    driver = State()
    confirm = State()


# ─────────────────────── Клавиатуры ───────────────────────
def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    if WEBAPP_URL:
        builder.row(
            KeyboardButton(
                text="📱 Открыть приложение",
                web_app=WebAppInfo(url=WEBAPP_URL),
            )
        )
    builder.row(KeyboardButton(text="🚗 Автопарк"))
    builder.row(KeyboardButton(text="📅 Забронировать"), KeyboardButton(text="💰 Тарифы"))
    builder.row(KeyboardButton(text="✅ Условия"), KeyboardButton(text="⭐ Преимущества"))
    builder.row(KeyboardButton(text="❓ FAQ"), KeyboardButton(text="📞 Контакты"))
    return builder.as_markup(resize_keyboard=True)


def brands_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Все", callback_data="brand:Все")
    for b in BRANDS:
        count = sum(1 for c in CARS if c["brand"] == b)
        builder.button(text=f"{b} ({count})", callback_data=f"brand:{b}")
    builder.adjust(2)
    return builder.as_markup()


def bodies_kb(brand: str = "Все") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for body in ["Все"] + BODIES:
        builder.button(text=body, callback_data=f"body:{brand}:{body}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="« Назад к маркам", callback_data="fleet_start"))
    return builder.as_markup()


def cars_list_kb(cars: list, page: int = 0, per_page: int = 6) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * per_page
    chunk = cars[start : start + per_page]
    for c in chunk:
        tag = f" [{c['tag']}]" if c.get("tag") else ""
        builder.button(
            text=f"{car_name(c)}{tag} — {format_price(c['price'])} ₽",
            callback_data=f"car:{c['id']}",
        )
    builder.adjust(1)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="‹ Назад", callback_data=f"page:{page - 1}"))
    if start + per_page < len(cars):
        nav.append(InlineKeyboardButton(text="Далее ›", callback_data=f"page:{page + 1}"))
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="« Фильтры", callback_data="fleet_start"))
    return builder.as_markup()


def car_detail_kb(car_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Забронировать", callback_data=f"book:{car_id}")
    builder.button(text="« К списку", callback_data="fleet_start")
    builder.adjust(1)
    return builder.as_markup()


def driver_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Да, нужен (+5 000 ₽/сут)", callback_data="driver:yes")
    builder.button(text="Нет, без водителя", callback_data="driver:no")
    builder.adjust(1)
    return builder.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить заявку", callback_data="confirm:yes")
    builder.button(text="❌ Отменить", callback_data="confirm:no")
    builder.adjust(1)
    return builder.as_markup()


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )


def filter_cars(brand: str = "Все", body: str = "Все") -> list:
    result = CARS
    if brand != "Все":
        result = [c for c in result if c["brand"] == brand]
    if body != "Все":
        result = [c for c in result if c["body"] == body]
    return result


async def send_admin_notification(bot: Bot, text: str):
    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, text, parse_mode="HTML")
        except Exception as e:
            logger.error("Admin notify failed: %s", e)


# ─────────────────────── Start / Cancel ───────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    text = (
        "<b>ZILANT RENTAL</b>\n"
        "Прокат премиум-авто в Казани\n\n"
        "BMW, Mercedes-Benz, Bentley, Audi и ещё 19 машин с подачей по городу.\n\n"
    )
    if WEBAPP_URL:
        text += "Откройте <b>мини-приложение</b> кнопкой ниже или пользуйтесь меню в чате."
    else:
        text += "Выберите раздел в меню 👇"
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")

    # Кнопка меню слева от поля ввода (Web App)
    if WEBAPP_URL:
        try:
            await bot.set_chat_menu_button(
                chat_id=message.chat.id,
                menu_button=MenuButtonWebApp(
                    text="Приложение",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                ),
            )
        except Exception as e:
            logger.warning("set_chat_menu_button: %s", e)


@router.message(Command("cancel"))
@router.message(F.text == "❌ Отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_menu_kb())


# ─────────────────────── Данные из Mini App (sendData) ───────────────────────
@router.message(F.web_app_data)
async def webapp_data(message: Message, bot: Bot):
    """Заявка, отправленная из мини-приложения через Telegram.WebApp.sendData()"""
    try:
        data = json.loads(message.web_app_data.data)
    except Exception:
        await message.answer("Не удалось прочитать данные заявки.", reply_markup=main_menu_kb())
        return

    if data.get("type") != "booking":
        await message.answer("Получены данные, но это не заявка на аренду.", reply_markup=main_menu_kb())
        return

    car_name_s = data.get("carName", "—")
    days = data.get("days", 0)
    total = data.get("total", 0)
    name = data.get("name", "—")
    phone = data.get("phone", "—")
    driver = "Да" if data.get("driver") else "Нет"
    from_d = data.get("from", "—")
    to_d = data.get("to", "—")

    user = message.from_user
    admin_text = (
        f"🆕 <b>Заявка из Mini App</b>\n\n"
        f"🚗 {car_name_s}\n"
        f"📅 {from_d} → {to_d} ({days} сут.)\n"
        f"👤 {name}\n"
        f"📞 {phone}\n"
        f"🧑‍✈️ Водитель: {driver}\n"
        f"💰 Итого: {format_price(total)} ₽\n\n"
        f"Telegram: @{user.username or '—'} (id: {user.id})"
    )
    await send_admin_notification(bot, admin_text)

    await message.answer(
        f"✅ <b>Заявка принята!</b>\n\n"
        f"{name}, мы перезвоним в течение 15 минут, "
        f"чтобы подтвердить {car_name_s} на {days} сут.\n\n"
        f"Если удобнее — звоните: {PHONE}",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )


# ─────────────────────── Контент-разделы ───────────────────────
@router.message(F.text == "📞 Контакты")
async def contacts(message: Message):
    await message.answer(
        f"<b>Контакты ZILANT RENTAL</b>\n\n"
        f"📞 Телефон: <a href='tel:+78430000000'>{PHONE}</a>\n"
        f"🕐 Режим: Ежедневно, 24/7\n"
        f"📍 Город: Казань, Республика Татарстан\n"
        f"💬 Мессенджеры: Telegram · WhatsApp",
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "💰 Тарифы")
async def tariffs(message: Message):
    text = "<b>Тарифы</b>\nЧем дольше — тем дешевле\n\n"
    for p in PLANS:
        text += f"• <b>{p['term']}</b> — {p['discount']}\n  <i>{p['note']}</i>\n\n"
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())


@router.message(F.text == "✅ Условия")
async def conditions(message: Message):
    text = "<b>Условия аренды</b>\n\n<b>Водителю</b>\n"
    for i in CONDITIONS["driver"]:
        text += f"• <b>{i['t']}</b> — {i['d']}\n"
    text += "\n<b>Оплата и залог</b>\n"
    for i in CONDITIONS["money"]:
        text += f"• <b>{i['t']}</b> — {i['d']}\n"
    text += "\n<b>Сервис</b>\n"
    for i in CONDITIONS["service"]:
        text += f"• <b>{i['t']}</b> — {i['d']}\n"
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())


@router.message(F.text == "⭐ Преимущества")
async def advantages(message: Message):
    text = (
        "<b>Почему выбирают ZILANT</b>\n\n"
        "🚗 23 автомобиля · 🏷 9 марок · ⏱ 15 мин · 🌙 24/7\n\n"
    )
    for a in ADVANTAGES:
        text += f"<b>{a['t']}</b>\n{a['d']}\n\n"
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())


@router.message(F.text == "❓ FAQ")
async def faq(message: Message):
    text = "<b>Вопросы и ответы</b>\n\n"
    for i, qa in enumerate(FAQ, 1):
        text += f"<b>{i}. {qa['q']}</b>\n{qa['a']}\n\n"
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb())


# ─────────────────────── Автопарк (чат) ───────────────────────
@router.message(F.text == "🚗 Автопарк")
@router.callback_query(F.data == "fleet_start")
async def fleet_start(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "<b>Автопарк — 23 автомобиля</b>\n"
        "От Camry до Bentayga.\n\nВыберите марку:"
    )
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=brands_kb(), parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=brands_kb(), parse_mode="HTML")


@router.callback_query(F.data.startswith("brand:"))
async def choose_brand(callback: CallbackQuery, state: FSMContext):
    brand = callback.data.split(":", 1)[1]
    await state.update_data(filter_brand=brand, filter_body="Все", page=0)
    cars = filter_cars(brand)
    text = f"<b>{brand}</b> — {len(cars)} авто\nВыберите тип кузова:"
    await callback.message.edit_text(text, reply_markup=bodies_kb(brand), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("body:"))
async def choose_body(callback: CallbackQuery, state: FSMContext):
    _, brand, body = callback.data.split(":", 2)
    await state.update_data(filter_brand=brand, filter_body=body, page=0)
    cars = filter_cars(brand, body)
    if not cars:
        await callback.answer("По фильтрам ничего не найдено", show_alert=True)
        return
    text = f"<b>{brand} · {body}</b>\nНайдено: {len(cars)}\nВыберите автомобиль:"
    await callback.message.edit_text(text, reply_markup=cars_list_kb(cars, 0), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("page:"))
async def cars_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    brand = data.get("filter_brand", "Все")
    body = data.get("filter_body", "Все")
    cars = filter_cars(brand, body)
    await state.update_data(page=page)
    text = f"<b>{brand} · {body}</b>\nНайдено: {len(cars)}\nВыберите автомобиль:"
    await callback.message.edit_text(text, reply_markup=cars_list_kb(cars, page), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("car:"))
async def car_detail(callback: CallbackQuery):
    car_id = callback.data.split(":", 1)[1]
    car = get_car(car_id)
    if not car:
        await callback.answer("Автомобиль не найден", show_alert=True)
        return
    tag = f"\n🏷 {car['tag']}" if car.get("tag") else ""
    text = (
        f"<b>{car_name(car)}</b>{tag}\n"
        f"Тип: {car['body']}\n{car['specs']}\n\n"
        f"💰 от <b>{format_price(car['price'])} ₽</b> / сутки"
    )
    await callback.message.edit_text(text, reply_markup=car_detail_kb(car_id), parse_mode="HTML")
    await callback.answer()


# ─────────────────────── Бронирование в чате ───────────────────────
@router.message(F.text == "📅 Забронировать")
async def book_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Booking.car)
    await message.answer(
        "Выберите автомобиль:",
        reply_markup=cars_list_kb(CARS, 0),
    )


@router.callback_query(F.data.startswith("book:"))
async def book_from_car(callback: CallbackQuery, state: FSMContext):
    car_id = callback.data.split(":", 1)[1]
    car = get_car(car_id)
    if not car:
        await callback.answer("Автомобиль не найден", show_alert=True)
        return
    await state.update_data(car_id=car_id)
    await state.set_state(Booking.from_date)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    await callback.message.answer(
        f"Вы выбрали: <b>{car_name(car)}</b>\n"
        f"от {format_price(car['price'])} ₽/сут\n\n"
        f"Введите дату получения <b>ГГГГ-ММ-ДД</b>\n(например {tomorrow}):",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.callback_query(Booking.car, F.data.startswith("car:"))
async def book_select_car(callback: CallbackQuery, state: FSMContext):
    car_id = callback.data.split(":", 1)[1]
    car = get_car(car_id)
    if not car:
        await callback.answer("Автомобиль не найден", show_alert=True)
        return
    await state.update_data(car_id=car_id)
    await state.set_state(Booking.from_date)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    await callback.message.answer(
        f"Вы выбрали: <b>{car_name(car)}</b>\n"
        f"от {format_price(car['price'])} ₽/сут\n\n"
        f"Введите дату получения <b>ГГГГ-ММ-ДД</b>\n(например {tomorrow}):",
        parse_mode="HTML",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(Booking.from_date)
async def book_from_date(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        d = datetime.strptime(text, "%Y-%m-%d")
        if d.date() < datetime.now().date():
            await message.answer("Дата не может быть в прошлом. Введите снова:")
            return
    except ValueError:
        await message.answer("Формат: ГГГГ-ММ-ДД (например 2026-10-05):")
        return
    await state.update_data(from_date=text)
    await state.set_state(Booking.to_date)
    await message.answer("Введите дату возврата <b>ГГГГ-ММ-ДД</b>:", parse_mode="HTML")


@router.message(Booking.to_date)
async def book_to_date(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    try:
        d = datetime.strptime(text, "%Y-%m-%d")
        from_d = datetime.strptime(data["from_date"], "%Y-%m-%d")
        if d <= from_d:
            await message.answer("Дата возврата должна быть позже получения:")
            return
    except ValueError:
        await message.answer("Формат: ГГГГ-ММ-ДД:")
        return
    await state.update_data(to_date=text)
    await state.set_state(Booking.name)
    await message.answer("Как к вам обращаться? Введите имя:")


@router.message(Booking.name)
async def book_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Имя слишком короткое:")
        return
    await state.update_data(name=name)
    await state.set_state(Booking.phone)
    await message.answer("Введите номер телефона:")


@router.message(Booking.phone)
async def book_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 10:
        await message.answer("Укажите полный номер:")
        return
    await state.update_data(phone=phone)
    await state.set_state(Booking.driver)
    await message.answer("Нужен ли водитель?\n(+5 000 ₽ за сутки)", reply_markup=driver_kb())


@router.callback_query(Booking.driver, F.data.startswith("driver:"))
async def book_driver(callback: CallbackQuery, state: FSMContext):
    need_driver = callback.data.split(":")[1] == "yes"
    await state.update_data(driver=need_driver)
    data = await state.get_data()
    car = get_car(data["car_id"])
    days = calc_days(data["from_date"], data["to_date"])
    discount = calc_discount(days)
    base = car["price"] * days
    disc_amount = int(base * discount)
    driver_cost = 5000 * days if need_driver else 0
    total = base - disc_amount + driver_cost

    text = (
        f"<b>Проверьте заявку</b>\n\n"
        f"🚗 <b>{car_name(car)}</b>\n"
        f"📅 {data['from_date']} → {data['to_date']} ({days} сут.)\n"
        f"👤 {data['name']}\n"
        f"📞 {data['phone']}\n"
        f"🧑‍✈️ Водитель: {'Да' if need_driver else 'Нет'}\n\n"
        f"База: {format_price(base)} ₽\n"
    )
    if discount:
        text += f"Скидка {int(discount * 100)}%: −{format_price(disc_amount)} ₽\n"
    if driver_cost:
        text += f"Водитель: +{format_price(driver_cost)} ₽\n"
    text += f"\n💰 <b>Итого: {format_price(total)} ₽</b>"

    await state.update_data(total=total, days=days)
    await state.set_state(Booking.confirm)
    await callback.message.answer(text, reply_markup=confirm_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(Booking.confirm, F.data == "confirm:yes")
async def book_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    car = get_car(data["car_id"])
    days = data.get("days", 0)
    total = data.get("total", 0)
    driver = "Да" if data.get("driver") else "Нет"
    user = callback.from_user

    admin_text = (
        f"🆕 <b>Новая заявка (чат)</b>\n\n"
        f"🚗 {car_name(car)}\n"
        f"📅 {data['from_date']} → {data['to_date']} ({days} сут.)\n"
        f"👤 {data['name']}\n"
        f"📞 {data['phone']}\n"
        f"🧑‍✈️ Водитель: {driver}\n"
        f"💰 Итого: {format_price(total)} ₽\n\n"
        f"Telegram: @{user.username or '—'} (id: {user.id})"
    )
    await send_admin_notification(bot, admin_text)

    await callback.message.answer(
        f"✅ <b>Заявка принята!</b>\n\n"
        f"{data['name']}, мы перезвоним в течение 15 минут.\n"
        f"Телефон: {PHONE}",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(Booking.confirm, F.data == "confirm:no")
async def book_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Заявка отменена.", reply_markup=main_menu_kb())
    await callback.answer()


# ─────────────────────── Запуск ───────────────────────
async def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        print("=" * 50)
        print("Укажите BOT_TOKEN в файле .env")
        print("1. @BotFather → /newbot")
        print("2. Токен в .env")
        print("=" * 50)
        return

    if not WEBAPP_URL:
        print("⚠ WEBAPP_URL не задан — кнопка Mini App будет скрыта.")
        print("  Залейте папку miniapp на HTTPS-хостинг и пропишите URL в .env")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # Глобальная кнопка меню (для всех чатов)
    if WEBAPP_URL:
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="Приложение",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            )
        except Exception as e:
            logger.warning("Global menu button: %s", e)

    logger.info("ZILANT RENTAL bot started | Mini App: %s", WEBAPP_URL or "off")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
