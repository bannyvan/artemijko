from aiogram import Bot
import asyncio
from datetime import datetime, timedelta
from src.bot import config, db


async def main():
    bot = Bot(config.BOT_TOKEN)
    conn = db.get_connection(config.DB)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT ws.id, e.telegram_id
            FROM work_sessions ws
            JOIN employees e ON ws.employee_id=e.id
            WHERE ws.status='active' AND ws.start_time < NOW() - INTERVAL 15 HOUR
        """)
        rows = cur.fetchall()
    for r in rows:
        await bot.send_message(r['telegram_id'], 'У вас есть незавершенная смена более 15 часов. Пожалуйста, завершите ее.')
    conn.close()


if __name__ == '__main__':
    asyncio.run(main())
