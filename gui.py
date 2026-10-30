import tkinter as tk,queue,sqlite3
from tkinter import ttk,messagebox,simpledialog
from datetime import datetime,date
from calendar_view import CalendarView
from integrations import Integrations
from database import DATE_FORMAT,TIME_FORMAT
class SchedulerGUI:
    def __init__(self,root,db,manager,events):
        self.root=root;self.db=db;self.manager=manager;self.events=events;self.selected_id=None;self.io=Integrations(db,self.refresh);self.build();self.refresh();root.after(400,self.check_events)
    def build(self):
        top=ttk.Frame(self.root,padding=10);top.pack(fill="x")
        ttk.Label(top,text="SMART TASK SCHEDULER",font=("Segoe UI",18,"bold")).pack(side="left")
        ttk.Label(top,text="Projects • Recurring tasks • Team • Calendar • Reminders").pack(side="right")
        form=ttk.LabelFrame(self.root,text="Task details",padding=10);form.pack(fill="x",padx=10,pady=5)
        self.v={k:tk.StringVar() for k in ["title","due_date","due_time","priority","project","member","recurrence","repeat_until"]}
        self.v["due_date"].set(date.today().isoformat());self.v["due_time"].set("18:00");self.v["priority"].set("Medium");self.v["recurrence"].set("None")
        self.desc=tk.Text(form,height=2,width=28)
        def field(label,key,row,col,choices=None):
            ttk.Label(form,text=label).grid(row=row,column=col,sticky="w",padx=4)
            w=ttk.Combobox(form,textvariable=self.v[key],values=choices,width=16,state="readonly") if choices is not None else ttk.Entry(form,textvariable=self.v[key],width=18)
            w.grid(row=row+1,column=col,sticky="ew",padx=4,pady=3);return w
        field("Task title *","title",0,0);field("Due date YYYY-MM-DD","due_date",0,1);field("Due time HH:MM","due_time",0,2);field("Priority","priority",0,3,["Low","Medium","High"])
        self.project_box=field("Project","project",0,4,[]);self.member_box=field("Assign to","member",0,5,[""])
        field("Repeat","recurrence",2,0,["None","Daily","Weekly","Monthly"]);field("Repeat until (optional)","repeat_until",2,1)
        ttk.Label(form,text="Description").grid(row=2,column=2,sticky="w");self.desc.grid(row=3,column=2,columnspan=2,padx=4,pady=3)
        act=ttk.Frame(form);act.grid(row=3,column=4,columnspan=2)
        for text,cmd in [("Add task",self.add),("Update",self.update),("Clear",self.clear)]:ttk.Button(act,text=text,command=cmd).pack(side="left",padx=2)
        bar=ttk.Frame(self.root,padding=6);bar.pack(fill="x")
        for text,cmd in [("Delete",self.delete),("Mark completed",self.complete),("Projects",self.projects),("Team members",self.members),("Calendar",lambda:CalendarView(self.root,self.db)),("Import ICS",self.io.import_ics),("Export ICS",self.io.export_ics),("Import CSV",self.io.import_csv),("Export CSV",self.io.export_csv)]:ttk.Button(bar,text=text,command=cmd).pack(side="left",padx=2)
        filters=ttk.Frame(self.root,padding=6);filters.pack(fill="x")
        self.search=tk.StringVar();self.sf=tk.StringVar(value="All");self.pf=tk.StringVar(value="All");self.projf=tk.StringVar(value="All")
        ttk.Label(filters,text="Search").pack(side="left");e=ttk.Entry(filters,textvariable=self.search,width=22);e.pack(side="left",padx=4);e.bind("<KeyRelease>",lambda _:self.refresh())
        self.filterbox(filters,"Status",self.sf,["All","Pending","Completed"]);self.filterbox(filters,"Priority",self.pf,["All","High","Medium","Low"]);self.project_filter=self.filterbox(filters,"Project",self.projf,["All"])
        frame=ttk.Frame(self.root,padding=10);frame.pack(fill="both",expand=True)
        cols=("id","title","due","priority","status","project","member","repeat");self.table=ttk.Treeview(frame,columns=cols,show="headings",selectmode="browse")
        for c,h,w in zip(cols,["ID","Task","Due date / time","Priority","Status","Project","Assigned to","Repeat"],[45,220,145,85,95,120,120,90]):self.table.heading(c,text=h);self.table.column(c,width=w,anchor="w")
        sb=ttk.Scrollbar(frame,orient="vertical",command=self.table.yview);self.table.configure(yscrollcommand=sb.set);self.table.pack(side="left",fill="both",expand=True);sb.pack(side="right",fill="y");self.table.bind("<<TreeviewSelect>>",self.select)
        self.summary=ttk.Label(self.root,padding=10);self.summary.pack(fill="x")
    def filterbox(self,parent,label,var,choices):
        ttk.Label(parent,text=label).pack(side="left",padx=(8,2));b=ttk.Combobox(parent,textvariable=var,values=choices,width=12,state="readonly");b.pack(side="left");b.bind("<<ComboboxSelected>>",lambda _:self.refresh());return b
    def refresh_choices(self):
        ps=[r["name"] for r in self.db.fetch("SELECT name FROM projects ORDER BY name")];ms=[""]+[r["name"] for r in self.db.fetch("SELECT name FROM members ORDER BY name")]
        self.project_box.configure(values=ps);self.member_box.configure(values=ms);self.project_filter.configure(values=["All"]+ps)
        if self.v["project"].get() not in ps:self.v["project"].set("General" if "General" in ps else ps[0])
        if self.v["member"].get() not in ms:self.v["member"].set("")
        if self.projf.get() not in ["All"]+ps:self.projf.set("All")
    def refresh(self):
        self.refresh_choices()
        for x in self.table.get_children():self.table.delete(x)
        rows=self.db.list_tasks(self.search.get(),self.sf.get(),self.pf.get(),self.projf.get());pending=completed=overdue=0;now=datetime.now()
        for r in rows:
            due=datetime.strptime(r["due_date"]+" "+r["due_time"],DATE_FORMAT+" "+TIME_FORMAT)
            if r["status"]=="Pending":pending+=1;overdue+=int(due<now)
            else:completed+=1
            self.table.insert("","end",values=(r["id"],r["title"],r["due_date"]+" "+r["due_time"],r["priority"],r["status"],r["project_name"] or "General",r["member_name"] or "-",r["recurrence"]))
        self.summary.config(text=f"Tasks: {len(rows)} | Pending: {pending} | Completed: {completed} | Overdue: {overdue}")
    def values(self):
        return {"title":self.v["title"].get(),"due_date":self.v["due_date"].get().strip(),"due_time":self.v["due_time"].get().strip(),"priority":self.v["priority"].get(),"project":self.v["project"].get(),"member":self.v["member"].get(),"recurrence":self.v["recurrence"].get(),"repeat_until":self.v["repeat_until"].get().strip(),"description":self.desc.get("1.0","end").strip()}
    def add(self):
        try:self.manager.add(self.values());self.clear();self.refresh();messagebox.showinfo("Success","Task added.")
        except Exception as e:messagebox.showerror("Invalid task",str(e))
    def update(self):
        if self.selected_id is None:messagebox.showwarning("Select task","Select a task first.");return
        try:self.manager.update(self.selected_id,self.values());self.clear();self.refresh();messagebox.showinfo("Success","Task updated.")
        except Exception as e:messagebox.showerror("Invalid task",str(e))
    def selected(self):
        s=self.table.selection()
        if not s:return None
        rows=self.db.fetch("SELECT * FROM tasks WHERE id=?",(int(self.table.item(s[0],"values")[0]),));return rows[0] if rows else None
    def select(self,event=None):
        r=self.selected()
        if not r:return
        self.selected_id=r["id"]
        for k in ["title","due_date","due_time","priority","recurrence"]:self.v[k].set(r[k])
        p=self.db.fetch("SELECT name FROM projects WHERE id=?",(r["project_id"],));m=self.db.fetch("SELECT name FROM members WHERE id=?",(r["assigned_to"],))
        self.v["project"].set(p[0]["name"] if p else "General");self.v["member"].set(m[0]["name"] if m else "");self.v["repeat_until"].set(r["repeat_until"] or "")
        self.desc.delete("1.0","end");self.desc.insert("1.0",r["description"] or "")
    def clear(self):
        self.selected_id=None
        self.v["title"].set("");self.v["due_date"].set(date.today().isoformat());self.v["due_time"].set("18:00");self.v["priority"].set("Medium");self.v["recurrence"].set("None");self.v["repeat_until"].set("");self.desc.delete("1.0","end")
        if self.table.selection():self.table.selection_remove(self.table.selection())
    def delete(self):
        r=self.selected()
        if not r:messagebox.showwarning("Select task","Select a task first.");return
        if messagebox.askyesno("Confirm","Delete selected task?"):self.db.delete_task(r["id"]);self.clear();self.refresh()
    def complete(self):
        r=self.selected()
        if not r:messagebox.showwarning("Select task","Select a task first.");return
        self.manager.complete(r);self.clear();self.refresh();messagebox.showinfo("Completed","Task completed. Next occurrence added if recurring.")
    def projects(self):
        n=simpledialog.askstring("New project","Enter project name:")
        if n and n.strip():
            try:self.db.execute("INSERT INTO projects(name) VALUES(?)",(n.strip(),));self.refresh()
            except sqlite3.IntegrityError:messagebox.showerror("Exists","Project already exists.")
    def members(self):
        n=simpledialog.askstring("New team member","Enter team member name:")
        if n and n.strip():
            try:self.db.execute("INSERT INTO members(name) VALUES(?)",(n.strip(),));self.refresh()
            except sqlite3.IntegrityError:messagebox.showerror("Exists","Team member already exists.")
    def check_events(self):
        try:
            while True:
                title,dd,tt=self.events.get_nowait();messagebox.showwarning("Task reminder",f"Task is due:\n{title}\n{dd} at {tt}");self.refresh()
        except queue.Empty:pass
        if self.root.winfo_exists():self.root.after(400,self.check_events)
