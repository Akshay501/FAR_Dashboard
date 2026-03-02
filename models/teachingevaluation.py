from .baseObject import baseObject

class teachingevaluation(baseObject):
    def __init__(self):
        self.setup()  # Loads 'TEACHINGEVALUATION'

    def getByProfessor(self, professor_key):
        self.data = []
        sql = "SELECT * FROM `TEACHINGEVALUATION` WHERE `ProfessorKey` = %s ORDER BY `EvaluationYear` DESC, `Term` DESC"
        self.cur.execute(sql, (professor_key,))
        for row in self.cur:
            self.data.append(row)
        return self.data