# models/baseObject.py
import yaml
from pathlib import Path
import pymysql
from pymysql.cursors import DictCursor

class baseObject:
    def __init__(self, config_path='config.yml'):
        self.data = []
        self.pk = None
        self.errors = []
        self.setup(config_path)  # ← automatically call setup on creation

    def setup(self, config_path='config.yml'):
        config_text = Path(config_path).read_text()
        self.config = yaml.safe_load(config_text)

        self.tn = self.config['tables'][type(self).__name__.lower()]

        self.conn = pymysql.connect(
            host=self.config['db']['host'],
            port=3306,
            user=self.config['db']['user'],
            password=self.config['db']['pw'],
            database=self.config['db']['db'],
            cursorclass=DictCursor,
            autocommit=True
        )
        self.cur = self.conn.cursor()

        self.getFields()

    def getFields(self):
        self.fields = []
        self.cur.execute(f"DESCRIBE `{self.tn}`")
        for row in self.cur:
            if 'auto_increment' in row.get('Extra', ''):
                self.pk = row['Field']
            else:
                self.fields.append(row['Field'])

    def set(self, d):
        self.data = [d]

    def insert(self, n=0):
        if not self.data or len(self.data) <= n:
            self.errors.append("No data to insert")
            return False

        record = self.data[n]
        keys = [k for k in record if k in self.fields]
        cols = ', '.join(f'`{k}`' for k in keys)
        ph = ', '.join(['%s'] * len(keys))
        sql = f"INSERT INTO `{self.tn}` ({cols}) VALUES ({ph})"
        vals = [record[k] for k in keys]

        self.cur.execute(sql, vals)
        if self.pk:
            self.data[n][self.pk] = self.cur.lastrowid

    def getAll(self, order=''):
        self.data = []
        sql = f"SELECT * FROM `{self.tn}`"
        if order:
            sql += f" ORDER BY {order}"
        self.cur.execute(sql)
        self.data = self.cur.fetchall()

    def getById(self, id_val):
        self.data = []
        sql = f"SELECT * FROM `{self.tn}` WHERE `{self.pk}` = %s"
        self.cur.execute(sql, (id_val,))
        row = self.cur.fetchone()
        if row:
            self.data.append(row)

    def getByField(self, field, value):
        self.data = []
        sql = f"SELECT * FROM `{self.tn}` WHERE `{field}` = %s"
        self.cur.execute(sql, (value,))
        self.data = self.cur.fetchall()

    def delete(self, id_val):
        if not self.pk:
            return False
        sql = f"DELETE FROM `{self.tn}` WHERE `{self.pk}` = %s"
        self.cur.execute(sql, (id_val,))
        return self.cur.rowcount > 0

    def truncate(self):
        sql = f"TRUNCATE TABLE `{self.tn}`"
        self.cur.execute(sql)

    def debug_print(self):
        print(f"Table: {self.tn}")
        print(f"Primary key: {self.pk}")
        print(f"Fields: {self.fields}")
        print(f"Data: {self.data}")
        print(f"Errors: {self.errors}")

if __name__ == '__main__':
    test = baseObject()
    test.debug_print()



    