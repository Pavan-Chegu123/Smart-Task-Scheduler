import csv
from pathlib import Path
from datetime import datetime,timedelta
from tkinter import filedialog,messagebox
from database import DATE_FORMAT,TIME_FORMAT
class Integrations:
    def __init__(self,db,refresh):self.db=db;self.refresh=refresh
    def export_csv(self):
        p=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")])
        if not p:return
        rows=self.db.fetch("SELECT t.title,t.description,t.due_date,t.due_time,t.priority,t.status,p.name project,m.name assigned_to,t.recurrence,t.repeat_until FROM tasks t LEFT JOIN projects p ON p.id=t.project_id LEFT JOIN members m ON m.id=t.assigned_to")
        with open(p,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f);w.writerow(["title","description","due_date","due_time","priority","status","project","assigned_to","recurrence","repeat_until"])
            for r in rows:w.writerow([r[k] or "" for k in r.keys()])
        messagebox.showinfo("CSV export",f"Exported {len(rows)} tasks.")
    def import_csv(self):
        p=filedialog.askopenfilename(filetypes=[("CSV","*.csv")])
        if not p:return
        count=0
        try:
            with open(p,newline="",encoding="utf-8-sig") as f:
                for r in csv.DictReader(f):
                    title=(r.get("title") or "").strip()
                    if not title:continue
                    dd=r.get("due_date") or datetime.now().strftime(DATE_FORMAT);tt=r.get("due_time") or "18:00";datetime.strptime(dd,DATE_FORMAT);datetime.strptime(tt,TIME_FORMAT)
                    project=(r.get("project") or "General").strip() or "General";self.db.execute("INSERT OR IGNORE INTO projects(name) VALUES(?)",(project,));pid=self.db.fetch("SELECT id FROM projects WHERE name=?",(project,))[0]["id"]
                    member=(r.get("assigned_to") or "").strip();mid=None
                    if member:
                        self.db.execute("INSERT OR IGNORE INTO members(name) VALUES(?)",(member,));mid=self.db.fetch("SELECT id FROM members WHERE name=?",(member,))[0]["id"]
                    self.db.add_task({"title":title,"description":r.get("description") or "","due_date":dd,"due_time":tt,"priority":r.get("priority") or "Medium","project_id":pid,"assigned_to":mid,"recurrence":r.get("recurrence") or "None","repeat_until":r.get("repeat_until") or ""});count+=1
            self.refresh();messagebox.showinfo("CSV import",f"Imported {count} tasks.")
        except Exception as e:messagebox.showerror("CSV import failed",str(e))
    def export_ics(self):
        p=filedialog.asksaveasfilename(defaultextension=".ics",filetypes=[("iCalendar","*.ics")])
        if not p:return
        rows=self.db.fetch("SELECT * FROM tasks ORDER BY due_date,due_time");lines=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Smart Task Scheduler//EN","CALSCALE:GREGORIAN"]
        def esc(s):return (s or "").replace("\\","\\\\").replace(",","\\,").replace(";","\\;").replace("\n","\\n")
        for r in rows:
            try:dt=datetime.strptime(r["due_date"]+" "+r["due_time"],DATE_FORMAT+" "+TIME_FORMAT)
            except ValueError:continue
            lines += ["BEGIN:VEVENT",f"UID:task-{r['id']}@smarttasks.local",f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",f"DTSTART:{dt.strftime('%Y%m%dT%H%M%S')}",f"DTEND:{(dt+timedelta(minutes=30)).strftime('%Y%m%dT%H%M%S')}",f"SUMMARY:{esc(r['title'])}",f"DESCRIPTION:{esc(r['description'])}","END:VEVENT"]
        lines.append("END:VCALENDAR");Path(p).write_text("\r\n".join(lines)+"\r\n",encoding="utf-8");messagebox.showinfo("Calendar export","Calendar file exported.")
    def import_ics(self):
        p=filedialog.askopenfilename(filetypes=[("iCalendar","*.ics")])
        if not p:return
        try:
            content=Path(p).read_text(encoding="utf-8",errors="replace").replace("\r\n ","").replace("\n ","");count=0
            for event in content.split("BEGIN:VEVENT")[1:]:
                title=start=desc=""
                for line in event.splitlines():
                    if line.startswith("SUMMARY:"):title=line[8:].replace("\\,",",").replace("\\n"," ")
                    elif line.startswith("DTSTART"):start=line.split(":",1)[1].strip()
                    elif line.startswith("DESCRIPTION:"):desc=line[12:].replace("\\n","\n")
                if not title or not start:continue
                raw=start.rstrip("Z")
                if "T" in raw:dt=datetime.strptime(raw[:15] if len(raw)>=15 else raw[:13],"%Y%m%dT%H%M%S" if len(raw)>=15 else "%Y%m%dT%H%M")
                else:dt=datetime.strptime(raw[:8],"%Y%m%d")
                pid=self.db.fetch("SELECT id FROM projects WHERE name='General'")[0]["id"]
                self.db.add_task({"title":title,"description":desc,"due_date":dt.strftime(DATE_FORMAT),"due_time":dt.strftime(TIME_FORMAT),"priority":"Medium","project_id":pid,"assigned_to":None,"recurrence":"None","repeat_until":""});count+=1
            self.refresh();messagebox.showinfo("Calendar import",f"Imported {count} events.")
        except Exception as e:messagebox.showerror("Calendar import failed",str(e))
