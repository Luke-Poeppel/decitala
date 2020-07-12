import sqlite3 as lite
import sys

con = None

try:
    con = lite.connect('test.db')
    cur = con.cursor()
    cur.execute('SELECT SQLITE_VERSION()')
    data = cur.fetchone()
    print('SQLite version: %s' % data)
except lite.Error as e:
    print('Error %s' % e.args[0])
    sys.exit(1)
finally:
    if con:
        con.close()

