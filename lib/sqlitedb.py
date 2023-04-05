import os
import sqlite3
from pathlib import Path
from datetime import datetime, time as dt_time, timedelta
from control_emulator.util import read_csv


class SQLiteDB:
    def __init__(self, db_path):
        def get_root_folder():
            cd = os.getcwd()
            cnt = 0
            while not os.path.isdir(str(cd) + '\\image'):
                cd = Path(cd).parent
                cnt += 1
                if 100 < cnt:
                    breakpoint()
            return str(cd)

        os.chdir(get_root_folder())

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        sqlite3.dbapi2.converters['DATETIME'] = sqlite3.dbapi2.converters['TIMESTAMP']

        self.cursor = self.conn.cursor()

    def __del__(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def exclusive_transaction(self):
        self.conn.execute('BEGIN EXCLUSIVE TRANSACTION')

    def commit(self):
        self.conn.commit()

    def execute(self, query, params=None):
        self.cursor.execute(query, params or ())
        return self.cursor

    def execute_one(self, query, params=None):
        self.execute(query, params)
        return self.cursor.fetchone()

    def execute_all(self, query, params=None):
        self.execute(query, params)
        return self.cursor.fetchall()

    def login_data_move(self):
        login_accounts = read_csv('csv/login.csv')
        logins_date = [(account_id, datetime.now().replace(microsecond=0)) for account_id in login_accounts]
        self.execute('DELETE FROM logins')
        self.conn.executemany('INSERT INTO logins (save_id, updated_at) VALUES (?, ?)', logins_date)
        self.conn.commit()

    def get_now_dt(self):
        return datetime.now().replace(microsecond=0)


if __name__ == '__main__':
    self = SQLiteDB('blue_archive.db')
    breakpoint()

    import sqlite3
    from datetime import datetime

    # SQLiteデータベースに接続
    conn = sqlite3.connect('blue_archive.db')

    # テーブル作成
    conn.execute(
        '''CREATE TABLE IF NOT EXISTS logins (save_id INTEGER PRIMARY KEY, updated_at TEXT)''')

    # datetimeオブジェクトの作成
    save_id = 2
    now = datetime.now().replace(microsecond=0)

    # SQL文の実行
    conn.execute("INSERT INTO logins (save_id, updated_at) VALUES (?, ?)", (save_id, now))

    # コミット
    conn.commit()

    # データの取得
    cursor = conn.execute("SELECT * FROM logins")
    for row in cursor:
        print(row)

    # SQLiteデータベースから切断
    conn.close()