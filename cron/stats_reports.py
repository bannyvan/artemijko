from aiogram import Bot
import asyncio
from src.bot import config, db


async def main():
    bot = Bot(config.BOT_TOKEN)
    conn = db.get_connection(config.DB)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT employee_id, SUM(total_hours) AS hours FROM work_sessions "
            "WHERE date >= CURDATE() - INTERVAL 7 DAY GROUP BY employee_id"
        )
        stats = cur.fetchall()
    for row in stats:
        with conn.cursor() as c2:
            c2.execute('SELECT telegram_id FROM employees WHERE id=%s', (row['employee_id'],))
            user = c2.fetchone()
            if user:
                await bot.send_message(user['telegram_id'], f"Ваши отработанные часы за неделю: {row['hours']}")
    conn.close()


if __name__ == '__main__':
    asyncio.run(main())
