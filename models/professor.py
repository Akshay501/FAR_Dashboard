# models/professor.py
from .baseObject import baseObject
import bibtexparser  # For parsing BibTeX imports
import json  # For JSON handling

class professor(baseObject):
    def __init__(self):
        super().__init__()

    def getScholarlyOutputs(self, professor_key):
        self.getById(professor_key)
        if not self.data or not self.data[0].get('ScholarlyOutputs'):
            return []
        # Assuming stored as JSON string; parse to list
        return json.loads(self.data[0]['ScholarlyOutputs'])

    def addScholarlyOutput(self, professor_key, entry_dict):
        outputs = self.getScholarlyOutputs(professor_key)
        outputs.append(entry_dict)
        sql = "UPDATE `PROFESSOR` SET `ScholarlyOutputs` = %s WHERE `ProfessorKey` = %s"
        self.cur.execute(sql, (json.dumps(outputs), professor_key))

    def importFromBibTeX(self, professor_key, bibtex_str):
        library = bibtexparser.loads(bibtex_str)
        outputs = []
        for entry in library.entries:
            entry_type = entry.get('ENTRYTYPE', 'other')  # e.g., 'article' -> 'journal'
            if entry_type == 'article':
                entry_type = 'journal'
            elif entry_type in ['inproceedings', 'conference']:
                entry_type = 'refereed_conference' if 'proceedings' in entry_type else 'conference'
            # Map other types as needed (e.g., 'book', 'techreport', 'patent')
            outputs.append({
                'type': entry_type,
                'title': entry.get('title'),
                'authors': entry.get('author'),
                'venue': entry.get('journal') or entry.get('booktitle'),
                'year': int(entry.get('year', 0)),
                'doi': entry.get('doi'),
                'url': entry.get('url'),
                # Add more fields from entry dict
            })
        # Save to DB (overwrites; append if needed by loading existing first)
        sql = "UPDATE `PROFESSOR` SET `ScholarlyOutputs` = %s WHERE `ProfessorKey` = %s"
        self.cur.execute(sql, (json.dumps(outputs), professor_key))