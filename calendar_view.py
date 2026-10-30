import tkinter as tk
from tkinter import ttk
from calendar import monthcalendar,month_name
from datetime import date
class CalendarView:
    def __init__(self,parent,db):
        self.db=db;self.win=tk.Toplevel(parent);self.win.title("Monthly Calendar");self.win.geometry("700x520")
        d=date.today();self.year=d.year;self.month=d.month
        self.heading=ttk.Label(self.win,font=("Segoe UI",16,"bold"));self.heading.pack(pady=8)
        nav=ttk.Frame(self.win);nav.pack()
        ttk.Button(nav,text="◀ Previous",command=lambda:self.move(-1)).pack(side="left",padx=5)
        ttk.Button(nav,text="Next ▶",command=lambda:self.move(1)).pack(side="left",padx=5)
        self.grid=ttk.Frame(self.win,padding=10);self.grid.pack(fill="both",expand=True)
        self.details=tk.Text(self.win,height=7);self.details.pack(fill="x",padx=10,pady=8);self.render()
    def move(self,n):
        self.month+=n
        if self.month<1:self.month=12;self.year-=1
        if self.month>12:self.month=1;self.year+=1
        self.render()
    def day(self,d):
        if not d:return
        chosen=date(self.year,self.month,d).isoformat();rows=self.db.fetch("SELECT title,due_time,status FROM tasks WHERE due_date=? ORDER BY due_time",(chosen,))
        self.details.delete("1.0","end");self.details.insert("end",f"Tasks for {chosen}\n")
        for r in rows:self.details.insert("end",f'{r["due_time"]}  {r["title"]} [{r["status"]}]\n')
        if not rows:self.details.insert("end","No tasks scheduled.")
    def render(self):
        for w in self.grid.winfo_children():w.destroy()
        self.heading.config(text=f"{month_name[self.month]} {self.year}")
        for i,n in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):ttk.Label(self.grid,text=n).grid(row=0,column=i)
        for ri,week in enumerate(monthcalendar(self.year,self.month),1):
            for ci,d in enumerate(week):ttk.Button(self.grid,text=str(d) if d else "",command=lambda x=d:self.day(x)).grid(row=ri,column=ci,sticky="nsew",padx=2,pady=2,ipady=7)
        for i in range(7):self.grid.columnconfigure(i,weight=1)
