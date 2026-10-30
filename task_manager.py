from datetime import datetime
from database import DATE_FORMAT,TIME_FORMAT
class TaskManager:
    def __init__(self,db):self.db=db
    def prepare(self,v):
        if not v["title"].strip():raise ValueError("Enter a task title.")
        datetime.strptime(v["due_date"],DATE_FORMAT);datetime.strptime(v["due_time"],TIME_FORMAT)
        until=v["repeat_until"].strip()
        if until:
            datetime.strptime(until,DATE_FORMAT)
            if until<v["due_date"]:raise ValueError("Repeat-until date cannot be before due date.")
        projects={r["name"]:r["id"] for r in self.db.fetch("SELECT id,name FROM projects")}
        members={r["name"]:r["id"] for r in self.db.fetch("SELECT id,name FROM members")}
        if v["project"] not in projects:raise ValueError("Select a valid project.")
        if v["member"] and v["member"] not in members:raise ValueError("Select a valid team member.")
        return {"title":v["title"].strip(),"description":v["description"],"due_date":v["due_date"],"due_time":v["due_time"],"priority":v["priority"],"project_id":projects[v["project"]],"assigned_to":members.get(v["member"]),"recurrence":v["recurrence"],"repeat_until":until}
    def add(self,v):self.db.add_task(self.prepare(v))
    def update(self,i,v):self.db.update_task(i,self.prepare(v))
    def complete(self,t):self.db.complete_task(t)
