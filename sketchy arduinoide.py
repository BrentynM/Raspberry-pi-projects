import tkinter as tk
from tkinter import scrolledtext
import subprocess
import random
import os
import serial 
import time

class MatrixProgrammer328P:
    def __init__(self, root):
        self.root = root
        self.root.title("MATRIX_AVR_PRO_328P")
        self.root.geometry("850x750")
        self.root.configure(bg="#000000")

        self.mcu = "atmega328p" 
        self.programmer = "arduino" 
        self.port = "/dev/ttyACM0" 

        self.root.grid_rowconfigure(1, weight=3)
        self.root.grid_rowconfigure(3, weight=2)
        self.root.grid_columnconfigure(0, weight=1)

        # 1. Header
        self.header_canvas = tk.Canvas(root, bg="#000000", height=60, highlightthickness=0)
        self.header_canvas.grid(row=0, column=0, sticky="ew")
        self.header_text = self.header_canvas.create_text(425, 30, text=f"[ {self.mcu.upper()} PROTOCOL ]", 
                                                         fill="#00FF00", font=("Monospace", 20, "bold"))
        
        # 2. Source Code Area
        tk.Label(root, text="> SOURCE_C_CODE:", fg="#00FF00", bg="#000000", font=("Monospace", 10)).grid(row=1, column=0, sticky="w", padx=20)
        self.code_input = scrolledtext.ScrolledText(root, bg="#000500", fg="#00FF00", 
                                                    insertbackground="#00FF00", font=("Monospace", 12))
        self.code_input.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        self.code_input.insert(tk.INSERT, "#include <avr/io.h>\n#include <util/delay.h>\n\nint main(void) {\n    DDRB |= (1 << PB5);\n    while(1) {\n        PORTB ^= (1 << PB5);\n        _delay_ms(100);\n    }\n    return 0;\n}")

        # 3. Control Buttons (BURN and RESET)
        self.btn_frame = tk.Frame(root, bg="#000000")
        self.btn_frame.grid(row=2, column=0, pady=10)
        
        self.burn_btn = tk.Button(self.btn_frame, text=" [ BURN PROTOCOL ] ", 
                                  command=self.burn_protocol, 
                                  bg="#00FF00", fg="#000000", 
                                  font=("Monospace", 12, "bold"), padx=20, pady=10)
        self.burn_btn.pack(side=tk.LEFT, padx=5)

        self.reset_btn = tk.Button(self.btn_frame, text=" [ STOP / RESET ] ", 
                                  command=self.stop_reset_protocol, 
                                  bg="#FF0000", fg="#FFFFFF", 
                                  font=("Monospace", 12, "bold"), padx=20, pady=10)
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        # 4. Log Area
        tk.Label(root, text="> UPLOAD_STREAM_LOG:", fg="#00FF00", bg="#000000", font=("Monospace", 10)).grid(row=3, column=0, sticky="w", padx=20)
        self.output_console = scrolledtext.ScrolledText(root, bg="#000000", fg="#00FF00", height=10, font=("Monospace", 10))
        self.output_console.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.output_console.config(state=tk.DISABLED)

        self.digits = []
        self.animate_matrix()

    def animate_matrix(self):
        if random.random() < 0.1:
            x = random.randint(0, 850)
            tag = self.header_canvas.create_text(x, 0, text=random.choice(['0','1']), fill="#004400", font=("Monospace", 8))
            self.digits.append(tag)
        for d in self.digits[:]:
            self.header_canvas.move(d, 0, 5)
            if self.header_canvas.coords(d)[1] > 60:
                self.header_canvas.delete(d)
                self.digits.remove(d)
        self.root.after(50, self.animate_matrix)

    def log(self, text):
        self.output_console.config(state=tk.NORMAL)
        self.output_console.insert(tk.END, text + "\n")
        self.output_console.see(tk.END)
        self.output_console.config(state=tk.DISABLED)
        self.root.update()

    def stop_reset_protocol(self):
        """Toggles the DTR pin to reset the Arduino chip."""
        self.log(">>> ISSUING STOP/RESET COMMAND...")
        try:
            # We open the serial port and toggle DTR/RTS
            ser = serial.Serial(self.port, 115200)
            ser.dtr = True  # Pulls Reset Low
            time.sleep(0.5)
            ser.dtr = False # Releases Reset
            ser.close()
            self.log(">>> SYSTEM RESET SUCCESSFUL.")
        except Exception as e:
            self.log(f"!!! RESET ERROR: {e}")
            self.log("Try checking if the device is plugged in.")

    def burn_protocol(self):
        self.log(">>> INITIALIZING BURN SEQUENCE...")
        user_code = self.code_input.get(1.0, tk.END)
        with open("temp.c", "w") as f:
            f.write(user_code)

        commands = [
            f"avr-gcc -mmcu={self.mcu} -Os -DF_CPU=16000000UL temp.c -o temp.elf",
            "avr-objcopy -O ihex -R .eeprom temp.elf temp.hex",
            f"avrdude -F -V -c {self.programmer} -p {self.mcu} -P {self.port} -b 115200 -U flash:w:temp.hex:i"
        ]

        for cmd in commands:
            try:
                result = subprocess.run(cmd.split(), capture_output=True, text=True)
                if result.stderr: self.log(result.stderr)
                if result.returncode != 0: return
            except Exception as e:
                self.log(f"SYSTEM ERROR: {e}")
                return
        self.log(">>> SUCCESS: FLASHED.")

if __name__ == "__main__":
    root = tk.Tk()
    app = MatrixProgrammer328P(root)
    root.mainloop()
