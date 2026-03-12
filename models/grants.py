from .baseObject import baseObject

class grants(baseObject):
    def __init__(self):
        super().__init__()

    def getByProfessor(self, professor_key):
        self.data = []
        sql = "SELECT * FROM `GRANTS` WHERE `ProfessorKey` = %s ORDER BY `End Date` DESC"
        self.cur.execute(sql, (professor_key,))
        self.data = self.cur.fetchall()
        return self.data