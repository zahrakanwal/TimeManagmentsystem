import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import smtplib  # For real email sending (commented out in the example)
from email.mime.text import MIMEText  # For real email usage (commented out in the example)

###############################################################################
# Database and Models
###############################################################################

DB_NAME = "tms_prototype.db"

def create_database():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Users table
    # Roles: 'executive', 'secretary', 'admin'
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL, 
            email TEXT
        );
    """)

    # Appointments table
    # participants will be stored as a comma-separated list of user_id for simplicity
    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            participants TEXT,
            venue TEXT,
            start_time TEXT,
            end_time TEXT,
            project_name TEXT,
            created_by INTEGER,
            FOREIGN KEY(created_by) REFERENCES users(user_id)
        );
    """)

    # Leaves / Unavailability
    cur.execute("""
        CREATE TABLE IF NOT EXISTS leaves (
            leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            start_date TEXT,
            end_date TEXT,
            reason TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        );
    """)

    conn.commit()
    conn.close()

def seed_demo_data():
    """Insert some demo users (if not present) for illustration."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Check if there's at least one user
    cur.execute("SELECT count(*) FROM users;")
    count = cur.fetchone()[0]
    
    if count == 0:
        users = [
            ("alice", "password", "executive", "alice@example.com"),
            ("bob", "password", "secretary", "bob@example.com"),
            ("charlie", "password", "admin", "charlie@example.com"),
            ("kanwal", "password", "executive", "kanwalzahra409@gmail.com")  # New user added
        ]
        for u in users:
            cur.execute("INSERT INTO users (username, password, role, email) VALUES (?,?,?,?)", u)
        conn.commit()

    conn.close()

###############################################################################
# Utility / Business Logic
###############################################################################

def check_login(username, password):
    """Validate user credentials against the database."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id, role, email FROM users WHERE username=? AND password=?", (username, password))
    result = cur.fetchone()
    conn.close()
    if result:
        user_id, role, email = result
        return (user_id, role, email)
    else:
        return None

def get_all_users():
    """Return a list of all users (for participant selection, etc.)."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, role FROM users")
    results = cur.fetchall()
    conn.close()
    return results

def get_username_by_id(user_id):
    """Return the username for a given user_id."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def create_appointment(title, participants, venue, start_time, end_time, project, created_by):
    """Create an appointment record in the database."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # Convert participant list of user_ids to a comma-separated string
    participants_str = ",".join(str(p) for p in participants)
    cur.execute("""
        INSERT INTO appointments (title, participants, venue, start_time, end_time, project_name, created_by)
        VALUES (?,?,?,?,?,?,?)
    """, (title, participants_str, venue, start_time, end_time, project, created_by))
    conn.commit()
    conn.close()

def get_appointments_for_user(user_id, date_str=None):
    """
    Return a list of appointments for a given user.
    Optionally filter by a specific date (YYYY-MM-DD).
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    query = """
    SELECT appointment_id, title, participants, venue, start_time, end_time, project_name, created_by 
    FROM appointments
    WHERE participants LIKE ?
    """
    params = [f"%{user_id}%"]

    if date_str:
        # Filter by date
        # We'll assume start_time and end_time are stored in ISO format (YYYY-MM-DD HH:MM)
        query += " AND date(start_time) = ?"
        params.append(date_str)

    cur.execute(query, tuple(params))
    results = cur.fetchall()
    conn.close()
    return results

def is_user_on_leave(user_id, date_str):
    """Check if a user is on leave for a given date (YYYY-MM-DD)."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    query = """
    SELECT leave_id FROM leaves
    WHERE user_id = ?
    AND date(?) BETWEEN date(start_date) AND date(end_date);
    """
    cur.execute(query, (user_id, date_str))
    row = cur.fetchone()
    conn.close()
    return row is not None

def add_leave(user_id, start_date, end_date, reason):
    """Mark a period of leave for a user."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO leaves (user_id, start_date, end_date, reason)
        VALUES (?,?,?,?)
    """, (user_id, start_date, end_date, reason))
    conn.commit()
    conn.close()

def send_email_notification(to_address, subject, body):
    """
    Mocked function to demonstrate email sending. 
    For real use, uncomment and configure smtplib settings.
    """
    print(f"[Mock Email] To: {to_address}\nSubject: {subject}\n{body}\n")
    
    # Example of how you'd send real email:
    # msg = MIMEText(body)
    # msg["Subject"] = subject
    # msg["From"] = "noreply@company.com"
    # msg["To"] = to_address
    #
    # with smtplib.SMTP("smtp.server.com", 587) as server:
    #     server.login("username", "password")
    #     server.sendmail("noreply@company.com", [to_address], msg.as_string())

def send_daily_summary(user_id):
    """
    Send a daily summary (mocked) of a user's appointments for the current date.
    """
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    appointments = get_appointments_for_user(user_id, today_str)
    
    username = get_username_by_id(user_id)
    subject = f"Daily Schedule for {today_str}"
    
    lines = []
    lines.append(f"Hello {username}, here are your appointments for {today_str}:")
    if not appointments:
        lines.append("No appointments scheduled for today.")
    else:
        for ap in appointments:
            ap_id, title, parts, venue, start, end, project, creator = ap
            lines.append(f"  - {title} from {start} to {end} at {venue} (Project: {project})")
    
    body = "\n".join(lines)

    # For demonstration, just print
    user_email = "unknown@example.com"
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT email FROM users WHERE user_id=?", (user_id,))
    res = cur.fetchone()
    if res:
        user_email = res[0]
    conn.close()

    send_email_notification(user_email, subject, body)

###############################################################################
# GUI Components
###############################################################################

class LoginWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("TMS Login")
        self.master.geometry("300x220")
        self.master.configure(bg="#cce6ff")  # light blue background
        
        # Username
        self.label_user = tk.Label(master, text="Username:", bg="#cce6ff", font=("Helvetica", 11))
        self.label_user.pack(pady=5)
        self.entry_user = tk.Entry(master, font=("Helvetica", 11))
        self.entry_user.pack()
        
        # Password
        self.label_pass = tk.Label(master, text="Password:", bg="#cce6ff", font=("Helvetica", 11))
        self.label_pass.pack(pady=5)
        self.entry_pass = tk.Entry(master, show="*", font=("Helvetica", 11))
        self.entry_pass.pack()
        
        # Login button
        self.button_login = tk.Button(master, text="Login", command=self.login, bg="#3399ff", fg="white", font=("Helvetica", 11, "bold"))
        self.button_login.pack(pady=15)
        
    def login(self):
        username = self.entry_user.get()
        password = self.entry_pass.get()
        
        result = check_login(username, password)
        if result:
            user_id, role, email = result
            messagebox.showinfo("Login Success", f"Welcome, {username} ({role})!")
            self.master.destroy()
            root = tk.Tk()
            TMSMainApp(root, user_id, role)
            root.mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

class TMSMainApp:
    def __init__(self, master, user_id, role):
        self.master = master
        self.master.title("Time Management Software - Main")
        self.master.geometry("800x600")
        self.master.configure(bg="#f0f8ff")  # Alice blue background
        
        self.user_id = user_id
        self.role = role
        
        # Create top menu with Logout option
        self.menu_bar = tk.Menu(self.master)
        self.master.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Logout", command=self.logout)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Title label
        self.label_title = tk.Label(master, text="TMS Dashboard", font=("Arial", 18, "bold"), bg="#f0f8ff", fg="#003366")
        self.label_title.pack(pady=15)
        
        # Frame for buttons with a colored background
        self.frame_buttons = tk.Frame(master, bg="#e6f2ff")
        self.frame_buttons.pack(pady=10, padx=10, fill="x")

        # Common operations for all roles
        btn_view_appts = tk.Button(self.frame_buttons, text="View Appointments", command=self.view_appointments, bg="#4da6ff", fg="white", font=("Helvetica", 11))
        btn_view_appts.grid(row=0, column=0, padx=10, pady=10)
        
        btn_add_appt = tk.Button(self.frame_buttons, text="Add Appointment", command=self.add_appointment, bg="#4da6ff", fg="white", font=("Helvetica", 11))
        btn_add_appt.grid(row=0, column=1, padx=10, pady=10)
        
        btn_add_leave = tk.Button(self.frame_buttons, text="Mark Leave", command=self.mark_leave, bg="#4da6ff", fg="white", font=("Helvetica", 11))
        btn_add_leave.grid(row=0, column=2, padx=10, pady=10)
        
        btn_daily_summary = tk.Button(self.frame_buttons, text="Send Daily Summary", command=self.send_daily_summary_now, bg="#4da6ff", fg="white", font=("Helvetica", 11))
        btn_daily_summary.grid(row=0, column=3, padx=10, pady=10)
        
        # Role-specific operations for secretary and admin
        if self.role == "secretary" or self.role == "admin":
            btn_schedule_multi = tk.Button(self.frame_buttons, text="Schedule Multi-User Meeting", command=self.schedule_multi_user_meeting, bg="#ffa64d", fg="white", font=("Helvetica", 11))
            btn_schedule_multi.grid(row=1, column=0, padx=10, pady=10)

        if self.role == "admin":
            btn_statistics = tk.Button(self.frame_buttons, text="View Statistics", command=self.view_statistics, bg="#ffa64d", fg="white", font=("Helvetica", 11))
            btn_statistics.grid(row=1, column=1, padx=10, pady=10)
            
            btn_user_mgmt = tk.Button(self.frame_buttons, text="User Management", command=self.user_management, bg="#ffa64d", fg="white", font=("Helvetica", 11))
            btn_user_mgmt.grid(row=1, column=2, padx=10, pady=10)
        
        # Optional Logout button at the bottom of the dashboard
        btn_logout = tk.Button(master, text="Logout", command=self.logout, bg="#cc0000", fg="white", font=("Helvetica", 11, "bold"))
        btn_logout.pack(side="bottom", pady=15)

    def logout(self):
        """Logs the user out and returns to the login window."""
        self.master.destroy()
        login_root = tk.Tk()
        LoginWindow(login_root)
        login_root.mainloop()
        
    ###########################################################################
    # Button Handlers
    ###########################################################################
    def view_appointments(self):
        """Show today's appointments or allow filtering by date."""
        top = tk.Toplevel(self.master)
        top.title("View Appointments")
        top.geometry("550x450")
        top.configure(bg="#e6f2ff")
        
        label_date = tk.Label(top, text="Enter date (YYYY-MM-DD) or leave blank for today:", bg="#e6f2ff", font=("Helvetica", 10))
        label_date.pack(pady=8)
        
        entry_date = tk.Entry(top, font=("Helvetica", 10))
        entry_date.pack(pady=5)
        
        text_area = tk.Text(top, width=65, height=18, font=("Helvetica", 10))
        text_area.pack(pady=8)
        
        def load_appointments():
            date_str = entry_date.get().strip()
            if not date_str:
                date_str = datetime.date.today().strftime("%Y-%m-%d")
            appts = get_appointments_for_user(self.user_id, date_str)
            
            text_area.delete("1.0", tk.END)
            if not appts:
                text_area.insert(tk.END, "No appointments.\n")
                return
            for ap in appts:
                ap_id, title, parts, venue, start, end, project, creator = ap
                text_area.insert(tk.END, f"Appointment ID: {ap_id}\n")
                text_area.insert(tk.END, f"Title: {title}\n")
                text_area.insert(tk.END, f"Venue: {venue}\n")
                text_area.insert(tk.END, f"Start: {start}\n")
                text_area.insert(tk.END, f"End: {end}\n")
                text_area.insert(tk.END, f"Project: {project}\n")
                creator_name = get_username_by_id(creator)
                text_area.insert(tk.END, f"Created By: {creator_name}\n")
                # List participants:
                p_ids = parts.split(",")
                p_names = [get_username_by_id(int(pid)) for pid in p_ids if pid]
                text_area.insert(tk.END, f"Participants: {', '.join(p_names)}\n")
                text_area.insert(tk.END, "------------------------------------\n")

        btn_load = tk.Button(top, text="Load Appointments", command=load_appointments, bg="#4da6ff", fg="white", font=("Helvetica", 10))
        btn_load.pack(pady=5)
        
        btn_close = tk.Button(top, text="Close", command=top.destroy, bg="#cc0000", fg="white", font=("Helvetica", 10))
        btn_close.pack(pady=5)

    def add_appointment(self):
        """Open a dialog to add a new appointment."""
        top = tk.Toplevel(self.master)
        top.title("Add Appointment")
        top.geometry("450x500")
        top.configure(bg="#e6f2ff")
        
        labels = ["Title", "Venue", "Start (YYYY-MM-DD HH:MM)", "End (YYYY-MM-DD HH:MM)", "Project Name"]
        entries = {}
        
        row = 0
        for lbl in labels:
            l = tk.Label(top, text=lbl + ":", bg="#e6f2ff", font=("Helvetica", 10))
            l.grid(row=row, column=0, pady=6, padx=6, sticky="e")
            e = tk.Entry(top, width=30, font=("Helvetica", 10))
            e.grid(row=row, column=1, pady=6, padx=6)
            entries[lbl] = e
            row += 1
        
        # Participant selection
        tk.Label(top, text="Select Participants:", bg="#e6f2ff", font=("Helvetica", 10)).grid(row=row, column=0, pady=6, padx=6, sticky="e")
        participants_var = tk.Variable(value=[])
        lb = tk.Listbox(top, listvariable=participants_var, selectmode=tk.MULTIPLE, width=30, height=6, font=("Helvetica", 10))
        lb.grid(row=row, column=1, pady=6, padx=6)
        row += 1
        
        user_list = get_all_users()
        for u in user_list:
            uid, uname, urole = u
            lb.insert(tk.END, f"{uid}:{uname} ({urole})")
        
        def save_appointment():
            title = entries["Title"].get().strip()
            venue = entries["Venue"].get().strip()
            start_str = entries["Start (YYYY-MM-DD HH:MM)"].get().strip()
            end_str = entries["End (YYYY-MM-DD HH:MM)"].get().strip()
            project_name = entries["Project Name"].get().strip()
            
            selected_indices = lb.curselection()
            selected_participants = []
            for idx in selected_indices:
                text_val = lb.get(idx)
                uid_str = text_val.split(":")[0]
                selected_participants.append(int(uid_str))
            
            if not title or not venue or not start_str or not end_str or not selected_participants:
                messagebox.showerror("Error", "Please fill all required fields and select participants.")
                return
            
            create_appointment(title, selected_participants, venue, start_str, end_str, project_name, self.user_id)
            
            # Notify participants by email (mock)
            for pid in selected_participants:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute("SELECT email, username FROM users WHERE user_id=?", (pid,))
                user_row = cur.fetchone()
                conn.close()
                if user_row:
                    email, uname = user_row
                    body = (f"Dear {uname},\n"
                            f"You have been invited to '{title}' at {venue} from {start_str} to {end_str}.\n"
                            f"Project: {project_name}\n\n"
                            "This is an automatic notification.")
                    send_email_notification(email, "New Meeting Invitation", body)
            
            messagebox.showinfo("Success", "Appointment created and participants notified!")
            top.destroy()
        
        btn_save = tk.Button(top, text="Save", command=save_appointment, bg="#4da6ff", fg="white", font=("Helvetica", 10))
        btn_save.grid(row=row, column=1, pady=10)
        
        btn_close = tk.Button(top, text="Close", command=top.destroy, bg="#cc0000", fg="white", font=("Helvetica", 10))
        btn_close.grid(row=row+1, column=1, pady=5)

    def schedule_multi_user_meeting(self):
        """
        A simplified demonstration of multi-user meeting scheduling.
        """
        top = tk.Toplevel(self.master)
        top.title("Schedule Multi-User Meeting")
        top.geometry("450x500")
        top.configure(bg="#e6f2ff")
        
        tk.Label(top, text="Title:", bg="#e6f2ff", font=("Helvetica", 10)).pack(pady=5)
        entry_title = tk.Entry(top, width=30, font=("Helvetica", 10))
        entry_title.pack()
        
        tk.Label(top, text="Venue:", bg="#e6f2ff", font=("Helvetica", 10)).pack(pady=5)
        entry_venue = tk.Entry(top, width=30, font=("Helvetica", 10))
        entry_venue.pack()

        tk.Label(top, text="Project Name (optional):", bg="#e6f2ff", font=("Helvetica", 10)).pack(pady=5)
        entry_project = tk.Entry(top, width=30, font=("Helvetica", 10))
        entry_project.pack()

        tk.Label(top, text="Desired Duration (hours):", bg="#e6f2ff", font=("Helvetica", 10)).pack(pady=5)
        entry_duration = tk.Entry(top, width=5, font=("Helvetica", 10))
        entry_duration.pack()

        tk.Label(top, text="Select Executives for Meeting:", bg="#e6f2ff", font=("Helvetica", 10)).pack(pady=5)
        lb_users = tk.Listbox(top, selectmode=tk.MULTIPLE, width=30, height=6, font=("Helvetica", 10))
        lb_users.pack(pady=5)
        user_list = get_all_users()
        for u in user_list:
            uid, uname, urole = u
            lb_users.insert(tk.END, f"{uid}:{uname} ({urole})")

        def find_common_slot():
            title = entry_title.get().strip()
            venue = entry_venue.get().strip()
            project_name = entry_project.get().strip()
            duration_hours = entry_duration.get().strip()
            
            if not title or not venue or not duration_hours:
                messagebox.showerror("Error", "Please fill out all required fields.")
                return
            
            try:
                dur_hrs = float(duration_hours)
            except ValueError:
                messagebox.showerror("Error", "Duration must be a number.")
                return
            
            selected_indices = lb_users.curselection()
            participants = []
            for idx in selected_indices:
                text_val = lb_users.get(idx)
                uid_str = text_val.split(":")[0]
                participants.append(int(uid_str))

            if not participants:
                messagebox.showerror("Error", "Please select at least one participant.")
                return

            start_dt = datetime.datetime.now() + datetime.timedelta(days=1)
            start_dt = start_dt.replace(hour=10, minute=0, second=0, microsecond=0)
            end_dt = start_dt + datetime.timedelta(hours=dur_hrs)
            
            start_str = start_dt.strftime("%Y-%m-%d %H:%M")
            end_str = end_dt.strftime("%Y-%m-%d %H:%M")
            
            create_appointment(title, participants, venue, start_str, end_str, project_name, self.user_id)
            
            # Notify participants
            for pid in participants:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute("SELECT email, username FROM users WHERE user_id=?", (pid,))
                user_row = cur.fetchone()
                conn.close()
                if user_row:
                    email, uname = user_row
                    body = (f"Dear {uname},\n"
                            f"A meeting '{title}' has been scheduled for you on {start_str} to {end_str} at {venue}.\n"
                            f"Project: {project_name}\n\n"
                            "This is an automatic notification.")
                    send_email_notification(email, "New Multi-User Meeting Scheduled", body)
            
            messagebox.showinfo("Success", f"Meeting scheduled on {start_str} to {end_str}.")
            top.destroy()

        btn_schedule = tk.Button(top, text="Find Common Slot & Schedule", command=find_common_slot, bg="#ffa64d", fg="white", font=("Helvetica", 10))
        btn_schedule.pack(pady=10)
        
        btn_close = tk.Button(top, text="Close", command=top.destroy, bg="#cc0000", fg="white", font=("Helvetica", 10))
        btn_close.pack(pady=5)

    def mark_leave(self):
        """Mark a leave period for the logged-in user."""
        top = tk.Toplevel(self.master)
        top.title("Mark Leave")
        top.geometry("320x240")
        top.configure(bg="#e6f2ff")
        
        tk.Label(top, text="Start Date (YYYY-MM-DD):", bg="#e6f2ff", font=("Helvetica", 10)).pack(pady=5)
        entry_start = tk.Entry(top, width=15, font=("Helvetica", 10))
        entry_start.pack()

        tk.Label(top, text="End Date (YYYY-MM-DD):", bg="#e6f2ff", font=("Helvetica", 10)).pack(pady=5)
        entry_end = tk.Entry(top, width=15, font=("Helvetica", 10))
        entry_end.pack()

        tk.Label(top, text="Reason:", bg="#e6f2ff", font=("Helvetica", 10)).pack(pady=5)
        entry_reason = tk.Entry(top, width=20, font=("Helvetica", 10))
        entry_reason.pack()

        def save_leave():
            s = entry_start.get().strip()
            e = entry_end.get().strip()
            r = entry_reason.get().strip()

            if not s or not e:
                messagebox.showerror("Error", "Please provide start and end dates.")
                return
            
            add_leave(self.user_id, s, e, r)
            messagebox.showinfo("Success", "Leave marked successfully!")
            top.destroy()

        btn_save = tk.Button(top, text="Save Leave", command=save_leave, bg="#4da6ff", fg="white", font=("Helvetica", 10))
        btn_save.pack(pady=10)
        
        btn_close = tk.Button(top, text="Close", command=top.destroy, bg="#cc0000", fg="white", font=("Helvetica", 10))
        btn_close.pack(pady=5)

    def send_daily_summary_now(self):
        """Send daily summary to the currently logged-in user."""
        send_daily_summary(self.user_id)
        messagebox.showinfo("Daily Summary", "A daily summary (mock) has been sent to your email.")

    def view_statistics(self):
        """Admins can view some basic usage stats."""
        top = tk.Toplevel(self.master)
        top.title("Statistics")
        top.geometry("550x350")
        top.configure(bg="#e6f2ff")

        text_area = tk.Text(top, width=65, height=18, font=("Helvetica", 10))
        text_area.pack(pady=10)

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT u.username, COUNT(a.appointment_id)
            FROM users u
            LEFT JOIN appointments a ON a.participants LIKE ('%' || u.user_id || '%')
            GROUP BY u.user_id
        """)
        rows = cur.fetchall()
        conn.close()

        text_area.insert(tk.END, "Appointments Count by User:\n")
        for r in rows:
            uname, count_ap = r
            text_area.insert(tk.END, f"- {uname}: {count_ap} appointments\n")
        
        btn_close = tk.Button(top, text="Close", command=top.destroy, bg="#cc0000", fg="white", font=("Helvetica", 10))
        btn_close.pack(pady=5)

    def user_management(self):
        """Admin can list users, add new users, etc."""
        top = tk.Toplevel(self.master)
        top.title("User Management")
        top.geometry("450x350")
        top.configure(bg="#e6f2ff")

        text_area = tk.Text(top, width=60, height=10, font=("Helvetica", 10))
        text_area.pack(pady=10)

        users = get_all_users()
        text_area.insert(tk.END, "Existing Users:\n")
        for u in users:
            uid, uname, urole = u
            text_area.insert(tk.END, f"ID: {uid}, Username: {uname}, Role: {urole}\n")

        tk.Label(top, text="Add New User", bg="#e6f2ff", font=("Helvetica", 10, "bold")).pack()

        frame_new = tk.Frame(top, bg="#e6f2ff")
        frame_new.pack(pady=5)
        
        tk.Label(frame_new, text="Username:", bg="#e6f2ff", font=("Helvetica", 10)).grid(row=0, column=0, padx=5)
        entry_uname = tk.Entry(frame_new, width=15, font=("Helvetica", 10))
        entry_uname.grid(row=0, column=1, padx=5)

        tk.Label(frame_new, text="Password:", bg="#e6f2ff", font=("Helvetica", 10)).grid(row=1, column=0, padx=5)
        entry_upass = tk.Entry(frame_new, show="*", width=15, font=("Helvetica", 10))
        entry_upass.grid(row=1, column=1, padx=5)

        tk.Label(frame_new, text="Role:", bg="#e6f2ff", font=("Helvetica", 10)).grid(row=2, column=0, padx=5)
        combo_role = ttk.Combobox(frame_new, values=["executive", "secretary", "admin"], width=13, font=("Helvetica", 10))
        combo_role.current(0)
        combo_role.grid(row=2, column=1, padx=5)

        tk.Label(frame_new, text="Email:", bg="#e6f2ff", font=("Helvetica", 10)).grid(row=3, column=0, padx=5)
        entry_email = tk.Entry(frame_new, width=15, font=("Helvetica", 10))
        entry_email.grid(row=3, column=1, padx=5)

        def add_user():
            uname = entry_uname.get().strip()
            upass = entry_upass.get().strip()
            urole = combo_role.get().strip()
            uemail = entry_email.get().strip()

            if not uname or not upass or not urole:
                messagebox.showerror("Error", "Fill all fields.")
                return

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO users (username, password, role, email) VALUES (?,?,?,?)", 
                            (uname, upass, urole, uemail))
                conn.commit()
                messagebox.showinfo("Success", "User created!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists.")
            conn.close()
            top.destroy()

        btn_add_user = tk.Button(top, text="Add User", command=add_user, bg="#ffa64d", fg="white", font=("Helvetica", 10))
        btn_add_user.pack(pady=10)
        
        btn_close = tk.Button(top, text="Close", command=top.destroy, bg="#cc0000", fg="white", font=("Helvetica", 10))
        btn_close.pack(pady=5)

###############################################################################
# Main Entry Point
###############################################################################

if __name__ == "__main__":
    create_database()
    seed_demo_data()
    
    main_root = tk.Tk()
    LoginWindow(main_root)
    main_root.mainloop()
