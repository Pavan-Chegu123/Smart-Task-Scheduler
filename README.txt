SMART TASK SCHEDULER - RUN INSTRUCTIONS

1. Extract the ZIP file.
2. Open the extracted SmartTaskScheduler_Modular folder in VS Code.
3. Open Terminal in that folder.
4. Run: python main.py

No extra pip packages are required (Python 3.10+ recommended).

FEATURES
- Add, update, delete, search, and filter tasks.
- Due date/time, priority, status, and overdue count.
- Multithreaded due-task reminders while the app is running.
- Multiple projects and team-member assignment.
- Daily, weekly, monthly recurring tasks.
- Monthly calendar view.
- CSV import/export.
- iCalendar (.ics) import/export for moving events to/from calendar apps.
- SQLite database stored in tasks.db beside the Python files.

LIMITATIONS
- Reminders show only while this desktop app is running.
- Calendar support is file-based import/export, not live Google Calendar sync.
- Team collaboration is local task assignment, not real-time online collaboration.
- SMS/Twilio sending is not included because trial account templates restrict custom SMS.
- Keep tasks.db to preserve saved data.
