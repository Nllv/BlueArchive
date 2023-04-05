from lib.sqlitedb import SQLiteDB


if __name__ == '__main__':
    self = SQLiteDB('blue_archive.db')
    self.record_login(3)