import threading
from datetime import datetime
from database import DATE_FORMAT,TIME_FORMAT
class ReminderScheduler(threading.Thread):
    def __init__(self,db,event_queue,stop_event):
        super().__init__(daemon=True);self.db=db;self.events=event_queue;self.stop_event=stop_event
    def run(self):
        while not self.stop_event.is_set():
            now=datetime.now()
            with self.db.lock,self.db.connect() as c:
                rows=c.execute("SELECT id,title,due_date,due_time FROM tasks WHERE status='Pending' AND notified=0").fetchall()
                for t in rows:
                    try:due=datetime.strptime(t["due_date"]+" "+t["due_time"],DATE_FORMAT+" "+TIME_FORMAT)
                    except ValueError:continue
                    if due<=now:
                        c.execute("UPDATE tasks SET notified=1 WHERE id=?",(t["id"],));self.events.put((t["title"],t["due_date"],t["due_time"]))
                c.commit()
            self.stop_event.wait(5)
