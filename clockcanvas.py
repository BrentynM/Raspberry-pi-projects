import tkinter as tk
from tkinter import font as tkfont
import requests, psutil, threading, socket, os, qrcode
from PIL import ImageTk, Image
from flask import Flask, request, redirect
from canvasapi import Canvas
from datetime import datetime

# --- CONFIGURATION ---
CANVAS_URL = "https://texastech.instructure.com/"
CANVAS_TOKEN = "24690~WvrE6QhxVfZVRxPkhCX324HhrVE7wuUGQf6uc34MxXF3fQ27LyMxewFnmTAe8RWF"
WEATHER_API_KEY = "fe3056870ae031f30eba1ff3b616660"
CITY = "Lubbock"

# Global task storage
phone_tasks = ["Mow the lawn", "Python Project"]

def get_actual_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception: IP = '127.0.0.1'
    finally: s.close()
    return IP

# --- FLASK SERVER ---
server = Flask(__name__)

@server.route('/')
def index():
    items = "".join([f"<li style='margin-bottom:15px;'>{t} <a href='/del/{i}' style='color:#f85149;'>[DEL]</a></li>" for i, t in enumerate(phone_tasks)])
    return f"""
    <html><body style='font-family:sans-serif;background:#0d1117;color:white;padding:40px;font-size:24px;'>
    <h1>Raider Hub</h1><ul>{items}</ul><hr>
    <form action='/add'><input name='t' style='font-size:20px;padding:10px;'> <button style='font-size:20px;'>Add</button></form>
    <br><br><a href='/exit' style='background:#cc0000; color:white; padding:20px; text-decoration:none; border-radius:10px; display:inline-block;'>⚠️ END DASHBOARD</a>
    </body></html>
    """

@server.route('/add')
def add():
    t = request.args.get('t'); 
    if t: phone_tasks.append(t)
    return redirect('/')

@server.route('/del/<int:idx>')
def delete(idx):
    if 0 <= idx < len(phone_tasks): phone_tasks.pop(idx)
    return redirect('/')

@server.route('/exit')
def exit_app():
    app.after(10, app.destroy_and_quit)
    return "Dashboard closed."

def run_server(): server.run(host='0.0.0.0', port=5000)

# --- GUI CLASS ---
class StealthRaider(tk.Tk):
    def __init__(self):
        super().__init__()
        self.attributes('-fullscreen', True)
        self.overrideredirect(True) # Borderless
        self.geometry("1024x600+0+0")
        self.configure(bg="#050505")
        self.bind("<Escape>", lambda e: self.destroy_and_quit())

        self.bg_main, self.bg_side = "#050505", "#0d1117"
        self.accent_red, self.accent_gold = "#cc0000", "#e3b341"

        try:
            self.canvas_api = Canvas(CANVAS_URL, CANVAS_TOKEN)
            self.user = self.canvas_api.get_current_user()
        except: self.canvas_api = None

        self.setup_ui()
        self.update_vitals()
        self.update_api_data()

    def setup_ui(self):
        # LEFT PANEL (Sidebar)
        self.left_panel = tk.Frame(self, bg=self.bg_side, width=280)
        self.left_panel.pack(side="left", fill="y")
        
        tk.Label(self.left_panel, text="SYSTEM", font=("Helvetica", 14, "bold"), bg=self.bg_side, fg=self.accent_red).pack(pady=(20, 5))
        self.vit_lbl = tk.Label(self.left_panel, text="", font=("Courier", 11), bg=self.bg_side, fg="#4ade80", justify="left")
        self.vit_lbl.pack()

        # QR Code Generation
        ip = get_actual_ip()
        qr = qrcode.make(f"http://{ip}:5000")
        qr = qr.resize((140, 140))
        self.qr_img = ImageTk.PhotoImage(qr)
        self.qr_label = tk.Label(self.left_panel, image=self.qr_img, bg=self.bg_side)
        self.qr_label.pack(pady=20)
        tk.Label(self.left_panel, text=f"Scan to Sync\n{ip}:5000", font=("Arial", 9), bg=self.bg_side, fg="#8b949e").pack()

        self.phone_box = tk.Listbox(self.left_panel, bg="#0d1117", fg="white", font=("Arial", 11), borderwidth=0, highlightthickness=0)
        self.phone_box.pack(fill="both", expand=True, padx=15, pady=10)

        # MAIN PANEL
        self.main_panel = tk.Frame(self, bg=self.bg_main)
        self.main_panel.pack(side="left", fill="both", expand=True)

        self.clock_lbl = tk.Label(self.main_panel, text="00:00", font=("Helvetica", 110, "bold"), bg=self.bg_main, fg="white")
        self.clock_lbl.pack(pady=(40, 0))

        self.weather_lbl = tk.Label(self.main_panel, text="Lubbock: --°F", font=("Arial", 22), bg=self.bg_main, fg="#8b949e")
        self.weather_lbl.pack()

        tk.Label(self.main_panel, text="CANVAS DEADLINES", font=("Helvetica", 14, "bold"), bg=self.bg_main, fg=self.accent_gold).pack(pady=(40, 10))
        self.todo_box = tk.Listbox(self.main_panel, bg=self.bg_main, fg="#d1d5db", font=("Arial", 14), borderwidth=0, highlightthickness=0, justify="center")
        self.todo_box.pack(fill="x", padx=40)

    def update_vitals(self):
        self.clock_lbl.config(text=datetime.now().strftime("%H:%M:%S"))
        try:
            temp = int(open("/sys/class/thermal/thermal_zone0/temp").read())/1000
            self.vit_lbl.config(text=f"TEMP: {temp:.1f}C\nCPU:  {psutil.cpu_percent()}%\nRAM:  {psutil.virtual_memory().percent}%")
        except: pass
        
        self.phone_box.delete(0, tk.END)
        for t in phone_tasks: self.phone_box.insert(tk.END, f" • {t}")
        self.after(1000, self.update_vitals)

    def update_api_data(self):
        try:
            r = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=imperial").json()
            self.weather_lbl.config(text=f"Lubbock: {round(r['main']['temp'])}°F | {r['weather'][0]['main']}")
        except: pass

        if self.canvas_api:
            try:
                self.todo_box.delete(0, tk.END)
                for item in list(self.user.get_todo_items())[:4]:
                    self.todo_box.insert(tk.END, f"• {item.assignment['name']}")
            except: pass
        self.after(900000, self.update_api_data)

    def destroy_and_quit(self):
        self.destroy()
        os._exit(0)

if __name__ == "__main__":
    app = StealthRaider()
    threading.Thread(target=run_server, daemon=True).start()
    app.mainloop()