import tkinter as tk
from time import strftime
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from canvasapi import Canvas
from PIL import Image, ImageTk

# --- CONFIGURATION ---
API_KEY_WEATHER = "3fe3056870ae031f30eba1ff3b616660" 
CANVAS_TOKEN = "24690~WvrE6QhxVfZVRxPkhCX324HhrVE7wuUGQf6uc34MxXF3fQ27LyMxewFnmTAe8RWF"
CANVAS_URL = "https://texastech.instructure.com"
CITY = "Lubbock"
TARGET_DATE = datetime(2026, 3, 30)
START_DATE = datetime(2026, 1, 12) 
# ---------------------

class TechDashboard:
    def __init__(self, root):
        self.root = root
        
        # --- TRUE BORDERLESS SETUP ---
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # overrideredirect(True) removes ALL window decorations (borders, title bar)
        self.root.overrideredirect(True)
        # Manually set geometry to fill the screen
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        
        self.root.configure(bg='black')
        self.root.config(cursor="none") 
        
        # --- EXIT BINDING ---
        self.root.bind('<Escape>', lambda e: self.root.destroy())

        # 1. Setup UI elements
        self.setup_ui()
        
        # 2. Apply theme FIRST
        self.apply_theme()
        
        # 3. Start data loops
        self.get_tech_alerts()
        self.get_canvas_data()
        self.get_weather()
        self.update_display()

    def setup_ui(self):
        # TechAlert (Top Left)
        self.alert_label = tk.Label(self.root, font=('DejaVu Sans Mono', 18, 'bold'), 
                                    bg='black', fg='red', justify='left', wraplength=500)
        self.alert_label.place(relx=0.02, rely=0.02, anchor='nw')

        # Clock/Weather (Center)
        self.center_frame = tk.Frame(self.root, bg='black')
        self.center_frame.place(relx=0.5, rely=0.45, anchor='center')
        
        self.time_label = tk.Label(self.center_frame, font=('DejaVu Sans Mono', 140, 'bold'), bg='black', fg='white')
        self.time_label.pack()
        
        self.weather_label = tk.Label(self.center_frame, font=('DejaVu Sans Mono', 45), bg='black', fg='white') 
        self.weather_label.pack(pady=10)

        # Canvas Assignments (Bottom Right)
        self.canvas_container = tk.Frame(self.root, bg='black', padx=40, pady=40)
        self.canvas_container.place(relx=1.0, rely=0.9, anchor='se')

        # Countdown & Progress Bar (Bottom Left)
        self.countdown_label = tk.Label(self.root, font=('DejaVu Sans Mono', 24, 'italic'), 
                                        bg='black', fg='gray', padx=30)
        self.countdown_label.place(relx=0.02, rely=0.88, anchor='sw')
        
        self.prog_width = 400
        self.progress_canvas = tk.Canvas(self.root, width=self.prog_width, height=15, 
                                         bg='#222222', highlightthickness=0)
        self.progress_canvas.place(relx=0.02, rely=0.94, anchor='sw')

    def apply_theme(self):
        hour = datetime.now().hour
        is_night = hour >= 22 or hour < 6
        
        self.colors = {
            'bg': 'black',
            'primary': '#FF3333' if is_night else 'white',
            'secondary': '#8B0000' if is_night else '#FFB81C',
            'dim': '#440000' if is_night else 'gray'
        }

        self.time_label.config(fg=self.colors['primary'])
        self.weather_label.config(fg=self.colors['primary'])
        self.countdown_label.config(fg=self.colors['dim'])
        
        for widget in self.canvas_container.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(fg=self.colors['secondary'])
        
        self.root.after(60000, self.apply_theme)

    def update_display(self):
        self.time_label.config(text=strftime('%I:%M:%S %p'))
        remaining = TARGET_DATE - datetime.now()
        if remaining.days >= 0:
            self.countdown_label.config(text=f"{remaining.days} Days Until Mar 30")
            total_dur = (TARGET_DATE - START_DATE).total_seconds()
            elapsed = (datetime.now() - START_DATE).total_seconds()
            percent = max(0, min(1, elapsed / total_dur))
            
            self.progress_canvas.delete("bar")
            self.progress_canvas.create_rectangle(0, 0, self.prog_width * percent, 15, 
                                                  fill=self.colors['secondary'], outline='', tags="bar")
        else:
            self.countdown_label.config(text="Target Date Reached!")
            
        self.root.after(1000, self.update_display)

    def get_tech_alerts(self):
        try:
            response = requests.get("https://www.ttu.edu/techalert/", timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            alert_box = soup.find(lambda tag: tag.name in ['div', 'p', 'strong'] and 'TechAlert!' in tag.text)
            
            if alert_box and "no active" not in alert_box.get_text().lower():
                full_text = alert_box.get_text(strip=True)
                main_msg = full_text.split('TechAlert!')[-1].split('.')[0].strip()
                self.alert_label.config(text=f"⚠️ {main_msg.upper()}") 
            else:
                self.alert_label.config(text="")
        except:
            pass
        self.root.after(300000, self.get_tech_alerts)

    def get_canvas_data(self):
        try:
            canvas = Canvas(CANVAS_URL, CANVAS_TOKEN)
            user = canvas.get_current_user()
            courses = user.get_favorite_courses(include=['total_scores', 'enrollments'])
            
            for widget in self.canvas_container.winfo_children(): 
                widget.destroy()

            has_any = False
            for course in courses:
                if not hasattr(course, 'name'): continue
                assignments = list(course.get_assignments(bucket='upcoming'))
                
                if assignments:
                    has_any = True
                    grade = "N/A"
                    if hasattr(course, 'enrollments') and len(course.enrollments) > 0:
                        score = course.enrollments[0].get('computed_current_score')
                        grade = f"{score}%" if score else "N/A"
                    
                    a = assignments[0]
                    if hasattr(a, 'due_at') and a.due_at:
                        dt = datetime.strptime(a.due_at, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
                        due_str = dt.astimezone().strftime('%b %d')
                    else:
                        due_str = "No Date"
                    
                    lbl = tk.Label(self.canvas_container, text=f"{course.course_code} ({grade})\n{a.name} - {due_str}", 
                                   font=('DejaVu Sans Mono', 22), bg='black', fg=self.colors['secondary'], justify='right', pady=12)
                    lbl.pack(anchor='se')

            if not has_any:
                tk.Label(self.canvas_container, text="NO ASSIGNMENTS YIPPEEEE", 
                         font=('DejaVu Sans Mono', 22, 'bold'), bg='black', fg='#00FF00').pack(anchor='se')
        except Exception as e:
            print(f"Canvas Error: {e}")
        self.root.after(1200000, self.get_canvas_data)

    def get_weather(self):
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY_WEATHER}&units=imperial"
            data = requests.get(url, timeout=5).json()
            temp = round(data['main']['temp'])
            self.weather_label.config(text=f"{CITY}: {temp}°F")
        except: 
            self.weather_label.config(text="Weather Offline")
        self.root.after(1200000, self.get_weather)

if __name__ == "__main__":
    root = tk.Tk()
    app = TechDashboard(root)
    root.mainloop()