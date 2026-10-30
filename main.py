import tkinter as tk,queue,threading
from database import Database
from task_manager import TaskManager
from scheduler import ReminderScheduler
from gui import SchedulerGUI
def main():
    root=tk.Tk();root.title("Smart Task Scheduler using Multithreading and Notifications");root.geometry("1280x800");root.minsize(1050,650)
    db=Database();manager=TaskManager(db);events=queue.Queue();stop=threading.Event();SchedulerGUI(root,db,manager,events)
    ReminderScheduler(db,events,stop).start()
    root.protocol("WM_DELETE_WINDOW",lambda:(stop.set(),root.destroy()))
    root.mainloop()
if __name__=="__main__":main()
