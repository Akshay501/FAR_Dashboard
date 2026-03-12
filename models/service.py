from .baseObject import baseObject

class service(baseObject):
    def __init__(self):
        super().__init__()

    def getByProfessor(self, professor_key):
        self.data = []
        sql = "SELECT * FROM `SERVICE` WHERE `ProfessorKey` = %s ORDER BY `Calendar Year` DESC, `Term` DESC"
        self.cur.execute(sql, (professor_key,))
        self.data = self.cur.fetchall()
        return self.data