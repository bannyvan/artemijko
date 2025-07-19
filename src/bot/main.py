from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

try:
    from . import config
except ImportError:
    from . import config as config

from . import db


def main_menu():
    return ReplyKeyboardMarkup([
        ['\U0001F4C5 Начать смену', '\U0001F6D1 Закончить смену'],
        ['\U0001F4CA Моя статистика', '\u2699\ufe0f Профиль']
    ], resize_keyboard=True)


def start(update: Update, context: CallbackContext):
    conn = db.get_connection(config.DB)
    tg_id = update.effective_user.id
    employee = db.get_employee(conn, tg_id)
    registration = db.get_registration(conn, tg_id)
    if employee:
        update.message.reply_text('Вы уже зарегистрированы.', reply_markup=main_menu())
    else:
        if not registration:
            db.start_registration(conn, tg_id)
        update.message.reply_text('Добро пожаловать! Введите ваше ФИО:')
    conn.close()


def cancel(update: Update, context: CallbackContext):
    conn = db.get_connection(config.DB)
    tg_id = update.effective_user.id
    if db.get_registration(conn, tg_id):
        db.cancel_registration(conn, tg_id)
        update.message.reply_text('Регистрация отменена.', reply_markup=main_menu())
    else:
        update.message.reply_text('Нечего отменять.', reply_markup=main_menu())
    conn.close()


def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    tg_id = update.effective_user.id
    conn = db.get_connection(config.DB)
    employee = db.get_employee(conn, tg_id)
    registration = db.get_registration(conn, tg_id)

    if registration and not employee:
        step = registration['step']
        if step == 1:
            db.update_registration(conn, tg_id, {'full_name': text, 'step': 2})
            update.message.reply_text('Введите дату рождения (ДД.ММ.ГГГГ):')
        elif step == 2:
            try:
                date = datetime.strptime(text, '%d.%m.%Y').date()
            except ValueError:
                update.message.reply_text('Неверный формат. Используйте ДД.ММ.ГГГГ:')
                conn.close()
                return
            db.update_registration(conn, tg_id, {'birth_date': date, 'step': 3})
            with conn.cursor() as cur:
                cur.execute('SELECT name FROM companies')
                comps = cur.fetchall()
            buttons = [[c['name']] for c in comps]
            markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
            update.message.reply_text('Выберите компанию:', reply_markup=markup)
        elif step == 3:
            with conn.cursor() as cur:
                cur.execute('SELECT id FROM companies WHERE name=%s', (text,))
                cid = cur.fetchone()
            if not cid:
                update.message.reply_text('Компания не найдена, попробуйте ещё раз:')
            else:
                db.update_registration(conn, tg_id, {'company_id': cid['id'], 'step': 4})
                update.message.reply_text('Введите город работы:')
        elif step == 4:
            db.update_registration(conn, tg_id, {'city': text})
            db.finish_registration(conn, tg_id)
            update.message.reply_text('Регистрация завершена!', reply_markup=main_menu())
        conn.close()
        return

    if text in ('\U0001F4C5 Начать смену', '/start_work'):
        if not employee:
            update.message.reply_text('Сначала зарегистрируйтесь командой /start')
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM work_sessions WHERE employee_id=%s AND status='active'", (employee['id'],))
                if cur.fetchone():
                    update.message.reply_text('Смена уже запущена')
                else:
                    cur.execute('INSERT INTO work_sessions (employee_id,start_time,date) VALUES (%s,NOW(),CURDATE())', (employee['id'],))
                    conn.commit()
                    update.message.reply_text('Смена начата', reply_markup=main_menu())
        conn.close()
        return

    if text in ('\U0001F6D1 Закончить смену', '/end_work'):
        if not employee:
            update.message.reply_text('Сначала зарегистрируйтесь командой /start')
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT id,start_time FROM work_sessions WHERE employee_id=%s AND status='active'", (employee['id'],))
                session = cur.fetchone()
                if not session:
                    update.message.reply_text('Активная смена не найдена')
                else:
                    end = datetime.now()
                    start = session['start_time']
                    hours = (end - start).total_seconds() / 3600 - 1
                    cur.execute("UPDATE work_sessions SET end_time=NOW(), total_hours=%s, status='completed' WHERE id=%s", (hours, session['id']))
                    conn.commit()
                    update.message.reply_text('Смена завершена', reply_markup=main_menu())
        conn.close()
        return

    if text in ('\U0001F4CA Моя статистика', '/my_stats'):
        if not employee:
            update.message.reply_text('Сначала зарегистрируйтесь командой /start')
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT SUM(total_hours) FROM work_sessions WHERE employee_id=%s AND MONTH(date)=MONTH(CURDATE())", (employee['id'],))
                hours = cur.fetchone()['SUM(total_hours)'] or 0
                cur.execute("SELECT COUNT(*) FROM work_sessions WHERE employee_id=%s AND status='active'", (employee['id'],))
                open_cnt = list(cur.fetchone().values())[0]
            avg = round(hours / datetime.now().day, 1) if hours else 0
            msg = f"Отработано в этом месяце: {hours} ч\nСреднее в день: {avg} ч\nНезавершенные смены: {open_cnt}"
            update.message.reply_text(msg, reply_markup=main_menu())
        conn.close()
        return

    if text in ('\u2699\ufe0f Профиль', '/profile'):
        if not employee:
            update.message.reply_text('Сначала зарегистрируйтесь командой /start')
        else:
            with conn.cursor() as cur:
                cur.execute('SELECT name FROM companies WHERE id=%s', (employee['company_id'],))
                comp = cur.fetchone()
            msg = (f"ФИО: {employee['full_name']}\n"
                   f"Дата рождения: {employee['birth_date'].strftime('%d.%m.%Y')}\n"
                   f"Компания: {comp['name']}\n"
                   f"Город: {employee['city']}")
            update.message.reply_text(msg, reply_markup=main_menu())
        conn.close()
        return

    if text == '/history':
        if not employee:
            update.message.reply_text('Сначала зарегистрируйтесь командой /start')
        else:
            with conn.cursor() as cur:
                cur.execute('SELECT start_time,end_time,total_hours FROM work_sessions WHERE employee_id=%s ORDER BY id DESC LIMIT 5', (employee['id'],))
                rows = cur.fetchall()
            if not rows:
                update.message.reply_text('Нет завершенных смен.', reply_markup=main_menu())
            else:
                lines = []
                for r in rows:
                    start = r['start_time'].strftime('%d.%m %H:%M')
                    end = r['end_time'].strftime('%d.%m %H:%M') if r['end_time'] else '-'
                    lines.append(f"{start} - {end} ({r['total_hours']} ч)")
                update.message.reply_text('\n'.join(lines), reply_markup=main_menu())
        conn.close()
        return

    if text == '/report week':
        if not employee:
            update.message.reply_text('Сначала зарегистрируйтесь командой /start')
        else:
            with conn.cursor() as cur:
                cur.execute('SELECT SUM(total_hours) AS h FROM work_sessions WHERE employee_id=%s AND date >= CURDATE() - INTERVAL 7 DAY', (employee['id'],))
                hours = cur.fetchone()['h'] or 0
            update.message.reply_text(f'Вы отработали за неделю: {hours} часов', reply_markup=main_menu())
        conn.close()
        return

    if text == '/report month':
        if not employee:
            update.message.reply_text('Сначала зарегистрируйтесь командой /start')
        else:
            with conn.cursor() as cur:
                cur.execute('SELECT SUM(total_hours) AS h FROM work_sessions WHERE employee_id=%s AND MONTH(date)=MONTH(CURDATE())', (employee['id'],))
                hours = cur.fetchone()['h'] or 0
            update.message.reply_text(f'Отработано за месяц: {hours} часов', reply_markup=main_menu())
        conn.close()
        return

    update.message.reply_text('Неизвестная команда', reply_markup=main_menu())
    conn.close()


def admin(update: Update, context: CallbackContext):
    tg_id = update.effective_user.id
    if tg_id not in config.ADMIN_IDS:
        update.message.reply_text('Команда недоступна.')
        return
    update.message.reply_text('Админские функции пока ограничены.')


def main():
    token = config.BOT_TOKEN
    updater = Updater(token)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('cancel', cancel))
    dp.add_handler(CommandHandler('admin', admin))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
