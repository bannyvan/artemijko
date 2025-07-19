import pymysql


def get_connection(cfg):
    return pymysql.connect(
        host=cfg['host'],
        user=cfg['user'],
        password=cfg['password'],
        database=cfg['database'],
        charset=cfg.get('charset', 'utf8mb4'),
        cursorclass=pymysql.cursors.DictCursor
    )


def get_employee(conn, tg_id):
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM employees WHERE telegram_id=%s', (tg_id,))
        return cur.fetchone()


def get_registration(conn, tg_id):
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM registrations WHERE telegram_id=%s', (tg_id,))
        return cur.fetchone()


def start_registration(conn, tg_id):
    with conn.cursor() as cur:
        cur.execute(
            'INSERT INTO registrations (telegram_id) VALUES (%s) '
            'ON DUPLICATE KEY UPDATE step=step',
            (tg_id,)
        )
    conn.commit()


def update_registration(conn, tg_id, data):
    fields = ', '.join(f"{k}=%s" for k in data)
    params = list(data.values()) + [tg_id]
    with conn.cursor() as cur:
        cur.execute(f'UPDATE registrations SET {fields} WHERE telegram_id=%s', params)
    conn.commit()


def finish_registration(conn, tg_id):
    reg = get_registration(conn, tg_id)
    if not reg:
        return False
    with conn.cursor() as cur:
        cur.execute(
            'INSERT INTO employees (telegram_id, full_name, birth_date, company_id, city) '
            'VALUES (%s, %s, %s, %s, %s)',
            (tg_id, reg['full_name'], reg['birth_date'], reg['company_id'], reg['city'])
        )
        cur.execute('DELETE FROM registrations WHERE telegram_id=%s', (tg_id,))
    conn.commit()
    return True


def cancel_registration(conn, tg_id):
    with conn.cursor() as cur:
        cur.execute('DELETE FROM registrations WHERE telegram_id=%s', (tg_id,))
    conn.commit()
