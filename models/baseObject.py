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
        sql = f"DESC `{self.tn}`"
        self.cur.execute(sql)
        for row in self.cur:
            self.fields.append(row['Field'])
            if row['Key'] == 'PRI':
                self.pk = row['Field']

    def set(self, d):
        self.data = [d]

    def insert(self):
        if not self.data or len(self.data) == 0:
            return False
        d = self.data[0]
        fields = []
        values = []
        for field in self.fields:
            if field != self.pk and field in d:
                fields.append(f"`{field}`")
                values.append(d[field])
        sql = f"INSERT INTO `{self.tn}` ({', '.join(fields)}) VALUES ({'%s, ' * (len(values)-1)}%s)"
        self.cur.execute(sql, values)
        return self.cur.lastrowid

    def update(self):
        if not self.data or len(self.data) == 0:
            return False
        d = self.data[0]
        sets = []
        values = []
        for field in self.fields:
            if field != self.pk and field in d:
                sets.append(f"`{field}` = %s")
                values.append(d[field])
        if not d.get(self.pk):
            return False
        sql = f"UPDATE `{self.tn}` SET {', '.join(sets)} WHERE `{self.pk}` = %s"
        values.append(d[self.pk])
        self.cur.execute(sql, values)
        return True

    def getAll(self, order=''):
        self.data = []
        sql = f"SELECT * FROM `{self.tn}`"
        if order:
            sql += f" ORDER BY {order}"
        self.cur.execute(sql)
        self.data = self.cur.fetchall()

    def getById(self, id_val):
        self.data = []
        if not self.pk:
            return
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