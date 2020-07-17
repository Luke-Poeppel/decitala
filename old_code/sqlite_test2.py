import sqlite3 as lite
import sys

con = lite.connect('user.db')

with con:
    cur = con.cursor()
    cur.execute("CREATE TABLE Users(Id INT, Name TEXT)") #create one table in the db
    cur.execute("INSERT INTO Users VALUES(1, 'Alex')") #insert entry into the Users table
    cur.execute("INSERT INTO Users VALUES(2, 'Andrew')")
    cur.execute("INSERT INTO Users VALUES(3, 'Luke')")




