import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime, timezone
from canvasapi import Canvas

# --- CONFIGURATION ---
API_URL = "https://texastech.instructure.com/" # Example for TTU
API_KEY = "24690~WvrE6QhxVfZVRxPkhCX324HhrVE7wuUGQf6uc34MxXF3fQ27LyMxewFnmTAe8RWF"

class CanvasDashboard(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("TTU Academic Performance Dashboard")
        self.geometry("850x500") # Widened to fit the grade column
        self.configure(bg="#f0f2f5")

        self.setup_styles()
        self.create_widgets()
        self.refresh_data()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), background="#f0f2f5")
        self.style.configure("Treeview", rowheight=30, font=("Segoe UI", 10))
        self.style.map("Treeview", background=[('selected', '#0078d7')])

    def create_widgets(self):
        header_frame = tk.Frame(self, bg="#f0f2f5", pady=20)
        header_frame.pack(fill="x", padx=20)

        self.title_label = ttk.Label(header_frame, text="Current Course Grades & Tasks", style="Header.TLabel")
        self.title_label.pack(side="left")

        self.refresh_btn = ttk.Button(header_frame, text="Refresh Dashboard", command=self.refresh_data)
        self.refresh_btn.pack(side="right")

        self.container = tk.Frame(self, bg="white", bd=1, relief="flat")
        self.container.pack(expand=True, fill="both", padx=20, pady=(0, 20))

        # Added "grade" to columns
        columns = ("course", "grade", "assignment", "due_date")
        self.tree = ttk.Treeview(self.container, columns=columns, show='headings', selectmode="browse")
        
        self.tree.heading("course", text="Course")
        self.tree.heading("grade", text="Current Grade")
        self.tree.heading("assignment", text="Upcoming Assignment")
        self.tree.heading("due_date", text="Due Date")

        self.tree.column("course", width=120, anchor="w")
        self.tree.column("grade", width=100, anchor="center")
        self.tree.column("assignment", width=280, anchor="w")
        self.tree.column("due_date", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self, textvariable=self.status_var, bd=1, relief="sunken", anchor="w").pack(side="bottom", fill="x")

    def refresh_data(self):
        self.refresh_btn.config(state="disabled")
        self.status_var.set("Fetching grades and assignments...")
        self.tree.delete(*self.tree.get_children())
        threading.Thread(target=self.fetch_canvas_data, daemon=True).start()

    def fetch_canvas_data(self):
        try:
            canvas = Canvas(API_URL, API_KEY)
            user = canvas.get_current_user()
            
            # CRITICAL: Added include=['total_scores'] to get grade data
            courses = user.get_favorite_courses(include=['total_scores'])
            
            display_data = []

            for course in courses:
                if not hasattr(course, 'name'): continue
                
                # 1. Extract Grade Information
                current_grade = "N/A"
                if hasattr(course, 'enrollments'):
                    enrollment = course.enrollments[0]
                    # Try to get percentage first, then letter grade
                    score = enrollment.get('computed_current_score')
                    letter = enrollment.get('computed_current_grade')
                    
                    if score:
                        current_grade = f"{score}%"
                    elif letter:
                        current_grade = letter

                # 2. Get upcoming assignments for this course
                upcoming = course.get_assignments(bucket='upcoming')
                
                # If no upcoming assignments, still show the course grade
                if not any(upcoming):
                    display_data.append((course.course_code, current_grade, "No upcoming tasks", "-"))
                
                for a in upcoming:
                    due_str = "No Date"
                    if hasattr(a, 'due_at') and a.due_at:
                        dt = datetime.strptime(a.due_at, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
                        due_str = dt.astimezone().strftime('%b %d, %I:%M %p')
                    
                    display_data.append((course.course_code, current_grade, a.name, due_str))

            self.after(0, lambda: self.update_table(display_data))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("API Error", f"Details: {str(e)}"))
            self.after(0, lambda: self.refresh_btn.config(state="normal"))

    def update_table(self, data):
        for item in data:
            self.tree.insert("", "end", values=item)
        self.refresh_btn.config(state="normal")
        self.status_var.set(f"Updated at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    app = CanvasDashboard()
    app.mainloop()