import sqlite3, threading, calendar
from pathlib import Path
from datetime import datetime, timedelta, date
DB_PATH = Path(__file__).resolve().parent / "tasks.db"
DATE_FORMAT="%Y-%m-%d"; TIME_FORMAT="%H:%M"
class Database:
    def __init__(self,path=DB_PATH):
        self.path=path; self.lock=threading.RLock()
        with self.connect() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL);
            CREATE TABLE IF NOT EXISTS members(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL);
            CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY,title TEXT NOT NULL,description TEXT DEFAULT '',
            due_date TEXT NOT NULL,due_time TEXT NOT NULL,priority TEXT DEFAULT 'Medium',status TEXT DEFAULT 'Pending',
            project_id INTEGER,assigned_to INTEGER,recurrence TEXT DEFAULT 'None',repeat_until TEXT DEFAULT '',
            notified INTEGER DEFAULT 0,created_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE SET NULL,
            FOREIGN KEY(assigned_to) REFERENCES members(id) ON DELETE SET NULL);
            INSERT OR IGNORE INTO projects(name) VALUES('General');
            """)
    def connect(self):
        c=sqlite3.connect(self.path,timeout=15); c.row_factory=sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON"); return c
    def fetch(self,sql,args=()):
        with self.lock,self.connect() as c:return c.execute(sql,args).fetchall()
    def execute(self,sql,args=()):
        with self.lock,self.connect() as c:return c.execute(sql,args).lastrowid
    def add_task(self,d):
        return self.execute("""INSERT INTO tasks(title,description,due_date,due_time,priority,status,project_id,assigned_to,recurrence,repeat_until,created_at)
        VALUES(?,?,?,?,?,'Pending',?,?,?,?,?)""",(d["title"],d["description"],d["due_date"],d["due_time"],d["priority"],d["project_id"],d["assigned_to"],d["recurrence"],d["repeat_until"],datetime.now().isoformat(timespec="seconds")))
    def update_task(self,i,d):
        self.execute("""UPDATE tasks SET title=?,description=?,due_date=?,due_time=?,priority=?,project_id=?,assigned_to=?,recurrence=?,repeat_until=?,notified=0 WHERE id=?""",
        (d["title"],d["description"],d["due_date"],d["due_time"],d["priority"],d["project_id"],d["assigned_to"],d["recurrence"],d["repeat_until"],i))
    def delete_task(self,i):self.execute("DELETE FROM tasks WHERE id=?",(i,))
    def complete_task(self,t):
        self.execute("UPDATE tasks SET status='Completed' WHERE id=?",(t["id"],))
        r=t["recurrence"]
        if r not in ("Daily","Weekly","Monthly"):return
        old=datetime.strptime(t["due_date"],DATE_FORMAT).date()
        if r=="Daily":nxt=old+timedelta(days=1)
        elif r=="Weekly":nxt=old+timedelta(days=7)
        else:
            y,m=old.year,old.month+1
            if m==13:y,m=y+1,1
            nxt=date(y,m,min(old.day,calendar.monthrange(y,m)[1]))
        until=t["repeat_until"] or ""
        if until and nxt>datetime.strptime(until,DATE_FORMAT).date():return
        self.add_task({"title":t["title"],"description":t["description"] or "","due_date":nxt.strftime(DATE_FORMAT),"due_time":t["due_time"],"priority":t["priority"],"project_id":t["project_id"],"assigned_to":t["assigned_to"],"recurrence":r,"repeat_until":until})
    def list_tasks(self,search="",status="All",priority="All",project="All"):
        q="SELECT t.*,p.name project_name,m.name member_name FROM tasks t LEFT JOIN projects p ON p.id=t.project_id LEFT JOIN members m ON m.id=t.assigned_to WHERE 1=1";a=[]
        if search:q+=" AND (t.title LIKE ? OR t.description LIKE ?)";a += [f"%{search}%",f"%{search}%"]
        if status!="All":q+=" AND t.status=?";a.append(status)
        if priority!="All":q+=" AND t.priority=?";a.append(priority)
        if project!="All":q+=" AND p.name=?";a.append(project)
        return self.fetch(q+" ORDER BY t.due_date,t.due_time",a)
