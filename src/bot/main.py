from datetime import datetime
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

try:
    from . import config
except ImportError:
    import config as config

from . import db


def main_menu() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton("\U0001F4C5 Начать смену"),
             types.KeyboardButton("\U0001F6D1 Закончить смену")],
            [types.KeyboardButton("\U0001F4CA Моя статистика"),
             types.KeyboardButton("\u2699\ufe0f Профиль")],
        ],
        resize_keyboard=True
    )


async def cmd_start(message: types.Message):
    conn = db.get_connection(config.DB)
    tg_id = message.from_user.id
    employee = db.get_employee(conn, tg_id)
    registration = db.get_registration(conn, tg_id)
    if employee:
        await message.answer("Вы уже зарегистрированы.", reply_markup=main_menu())
    else:
        if not registration:
            db.start_registration(conn, tg_id)
        await message.answer("Добро пожаловать! Введите ваше ФИО:")
    conn.close()


async def cmd_cancel(message: types.Message):
    conn = db.get_connection(config.DB)
    tg_id = message.from_user.id
    if db.get_registration(conn, tg_id):
        db.cancel_registration(conn, tg_id)
        await message.answer("Регистрация отменена.", reply_markup=main_menu())
    else:
        await message.answer("Нечего отменять.", reply_markup=main_menu())
    conn.close()


async def cmd_admin(message: types.Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("Команда недоступна.")
        return
    await message.answer("Админские функции пока ограничены.")


async def process_text(message: types.Message):
    if not message.text:
        return
    text = message.text.strip()
    tg_id = message.from_user.id
    conn = db.get_connection(config.DB)
    employee = db.get_employee(conn, tg_id)
    registration = db.get_registration(conn, tg_id)

    if registration and not employee:
        step = registration['step']
        if step == 1:
            db.update_registration(conn, tg_id, {'full_name': text, 'step': 2})
            await message.answer('Введите дату рождения (ДД.ММ.ГГГГ):')
        elif step == 2:
            try:
                date = datetime.strptime(text, '%d.%m.%Y').date()
            except ValueError:
                await message.answer('Неверный формат. Используйте ДД.ММ.ГГГГ:')
                conn.close()
                return
            db.update_registration(conn, tg_id, {'birth_date': date, 'step': 3})
            with conn.cursor() as cur:
                cur.execute('SELECT name FROM companies')
                comps = cur.fetchall()
            buttons = [[types.KeyboardButton(c['name'])] for c in comps]
            markup = types.ReplyKeyboardMarkup(keyboard=buttons, one_time_keyboard=True, resize_keyboard=True)
            await message.answer('Выберите компанию:', reply_markup=markup)
        elif step == 3:
            with conn.cursor() as cur:
                cur.execute('SELECT id FROM companies WHERE name=%s', (text,))
                cid = cur.fetchone()
            if not cid:
                await message.answer('Компания не найдена, попробуйте ещё раз:')
            else:
                db.update_registration(conn, tg_id, {'company_id': cid['id'], 'step': 4})
                await message.answer('Введите город работы:')
        elif step == 4:
            db.update_registration(conn, tg_id, {'city': text})
            db.finish_registration(conn, tg_id)
            await message.answer('Регистрация завершена!', reply_markup=main_menu())
        conn.close()
        return

    if text in ('\U0001F4C5 Начать смену', '/start_work'):
        if not employee:
            await message.answer('Сначала зарегистрируйтесь командой /start')
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM work_sessions WHERE employee_id=%s AND status='active'", (employee['id'],))
                if cur.fetchone():
                    await message.answer('Смена уже запущена')
                else:
                    cur.execute('INSERT INTO work_sessions (employee_id,start_time,date) VALUES (%s,NOW(),CURDATE())', (employee['id'],))
                    conn.commit()
                    await message.answer('Смена начата', reply_markup=main_menu())
        conn.close()
        return

    if text in ('\U0001F6D1 Закончить смену', '/end_work'):
        if not employee:
            await message.answer('Сначала зарегистрируйтесь командой /start')
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT id,start_time FROM work_sessions WHERE employee_id=%s AND status='active'", (employee['id'],))
                session = cur.fetchone()
                if not session:
                    await message.answer('Активная смена не найдена')
                else:
                    end = datetime.now()
                    start = session['start_time']
                    hours = (end - start).total_seconds() / 3600 - 1
                    cur.execute("UPDATE work_sessions SET end_time=NOW(), total_hours=%s, status='completed' WHERE id=%s", (hours, session['id']))
                    conn.commit()
                    await message.answer('Смена завершена', reply_markup=main_menu())
        conn.close()
        return

    if text in ('\U0001F4CA Моя статистика', '/my_stats'):
        if not employee:
            await message.answer('Сначала зарегистрируйтесь командой /start')
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT SUM(total_hours) FROM work_sessions WHERE employee_id=%s AND MONTH(date)=MONTH(CURDATE())", (employee['id'],))
                hours = cur.fetchone()['SUM(total_hours)'] or 0
                cur.execute("SELECT COUNT(*) FROM work_sessions WHERE employee_id=%s AND status='active'", (employee['id'],))
                open_cnt = list(cur.fetchone().values())[0]
            avg = round(hours / datetime.now().day, 1) if hours else 0
            msg = f"Отработано в этом месяце: {hours} ч\nСреднее в день: {avg} ч\nНезавершенные смены: {open_cnt}"
            await message.answer(msg, reply_markup=main_menu())
        conn.close()
        return

    if text in ('\u2699\ufe0f Профиль', '/profile'):
        if not employee:
            await message.answer('Сначала зарегистрируйтесь командой /start')
        else:
            with conn.cursor() as cur:
                cur.execute('SELECT name FROM companies WHERE id=%s', (employee['company_id'],))
                comp = cur.fetchone()
            msg = (f"ФИО: {employee['full_name']}\n"
                   f"Дата рождения: {employee['birth_date'].strftime('%d.%m.%Y')}\n"
                   f"Компания: {comp['name']}\n"
                   f"Город: {employee['city']}")
            await message.answer(msg, reply_markup=main_menu())
        conn.close()
        return

    if text == '/history':
        if not employee:
            await message.answer('Сначала зарегистрируйтесь командой /start')
        else:
            with conn.cursor() as cur:
                cur.execute('SELECT start_time,end_time,total_hours FROM work_sessions WHERE employee_id=%s ORDER BY id DESC LIMIT 5', (employee['id'],))
                rows = cur.fetchall()
            if not rows:
                await message.answer('Нет завершенных смен.', reply_markup=main_menu())
            else:
                lines = []
                for r in rows:
                    start = r['start_time'].strftime('%d.%m %H:%M')
                    end = r['end_time'].strftime('%d.%m %H:%M') if r['end_time'] else '-'
                    lines.append(f"{start} - {end} ({r['total_hours']} ч)")
                await message.answer('\n'.join(lines), reply_markup=main_menu())
        conn.close()
        return

    if text == '/report week':
        if not employee:
            await message.answer('Сначала зарегистрируйтесь командой /start')
        else:
            with conn.cursor() as cur:
                cur.execute('SELECT SUM(total_hours) AS h FROM work_sessions WHERE employee_id=%s AND date >= CURDATE() - INTERVAL 7 DAY', (employee['id'],))
                hours = cur.fetchone()['h'] or 0
            await message.answer(f'Вы отработали за неделю: {hours} часов', reply_markup=main_menu())
        conn.close()
        return

    if text == '/report month':
        if not employee:
            await message.answer('Сначала зарегистрируйтесь командой /start')
        else:
            with conn.cursor() as cur:
                cur.execute('SELECT SUM(total_hours) AS h FROM work_sessions WHERE employee_id=%s AND MONTH(date)=MONTH(CURDATE())', (employee['id'],))
                hours = cur.fetchone()['h'] or 0
            await message.answer(f'Отработано за месяц: {hours} часов', reply_markup=main_menu())
        conn.close()
        return

    if text.startswith('/'):
        await message.answer('Неизвестная команда', reply_markup=main_menu())
        conn.close()
        return

    await message.answer('Неизвестная команда', reply_markup=main_menu())
    conn.close()


def setup_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command('start'))
    dp.message.register(cmd_cancel, Command('cancel'))
    dp.message.register(cmd_admin, Command('admin'))
    dp.message.register(process_text, F.text)


aio_bot = Bot(config.BOT_TOKEN)
dp = Dispatcher()
setup_handlers(dp)


async def main():
    await dp.start_polling(aio_bot)


if __name__ == '__main__':
    asyncio.run(main())
