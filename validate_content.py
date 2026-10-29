"""Validate the authored content without requiring Streamlit."""
import ast
import json
from pathlib import Path

root=Path(__file__).parent
ast.parse((root/'app.py').read_text(encoding='utf-8'))
course=json.loads((root/'course.json').read_text(encoding='utf-8'))
ids=set()
for c in course['chapters']:
    questions=[q for q in course['questions'] if q['chapter']==c['id']]
    assert len(questions)==15
    for q in questions:
        assert q['id'] not in ids
        ids.add(q['id'])
        assert len(q['options'])==len(set(q['options']))==4
        assert q['answer'] in q['options']
        assert q['source'] and q['explanation']
    for item in c['lessons']+questions:
        if item.get('figure'):
            assert (root/'assets'/f"{item['figure']}.png").is_file()
print('PASS: syntax, 2 chapters, 30 unique questions, answer keys, sources and figure paths')
