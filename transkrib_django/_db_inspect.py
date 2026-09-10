import sqlite3, os
os.chdir('transkrib_django')
c = sqlite3.connect('data/db.sqlite3')
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print('TABLES:', tables)
for t in ('core_task',):
    if t not in tables:
        print(t, ':: NOT FOUND')
        continue
    cols = [r[1] for r in c.execute(f'PRAGMA table_info({t})')]
    print(t, 'COLUMNS:', cols)
    has_txt = 'transcript_text' in cols
    print(t, 'HAS transcript_text:', has_txt)