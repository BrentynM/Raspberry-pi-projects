import tkinter as tk
from tkinter import messagebox
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageTk
from escpos.printer import Network

class BarcodeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("2x3 Label Maker")
        self.root.geometry("400x550")

        # --- UI Setup ---
        tk.Label(root, text="Barcode ID:", font=("Arial", 12)).pack(pady=5)
        self.id_entry = tk.Entry(root, font=("Arial", 12))
        self.id_entry.insert(0, "ID12345") 
        self.id_entry.pack(pady=5)

        tk.Label(root, text="Printer IP Address:", font=("Arial", 10)).pack(pady=5)
        self.ip_entry = tk.Entry(root, font=("Arial", 10))
        self.ip_entry.insert(0, "192.168.1.100")
        self.ip_entry.pack(pady=5)

        self.gen_btn = tk.Button(root, text="Generate & Preview", command=self.preview_barcode)
        self.gen_btn.pack(pady=10)

        self.preview_label = tk.Label(root, text="[ Preview Area ]")
        self.preview_label.pack(pady=10)

        self.print_btn = tk.Button(root, text="PRINT 2x3 LABEL", bg="blue", fg="white", command=self.print_barcode)
        self.print_btn.pack(pady=10)

    def generate_fixed_size_barcode(self):
        barcode_id = self.id_entry.get().strip()
        
        # Ensure ID is valid for Code128
        if len(barcode_id) < 1:
            barcode_id = "0000"

        # 1. Generate the raw barcode image
        code128 = barcode.get_barcode_class('code128')
        options = {'write_text': False, 'module_height': 15.0}
        
        writer = ImageWriter()
        my_barcode = code128(barcode_id, writer=writer)
        raw_path = my_barcode.save("raw_barcode", options)

        # 2. Create a 2x3 inch canvas (assuming standard 203 DPI)
        # Width: 406 pixels | Height: 609 pixels
        canvas_width = 406
        canvas_height = 609
        # Inkjet printers often need '1' (binary) or 'L' (grayscale) images
        canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')

        # 3. Open and resize the generated barcode
        with Image.open(raw_path) as barcode_img:
            new_w = int(canvas_width * 0.9)
            w_percent = (new_w / float(barcode_img.size[0]))
            new_h = int((float(barcode_img.size[1]) * float(w_percent)))
            
            # Using NEAREST keeps the barcode lines crisp
            resized_barcode = barcode_img.resize((new_w, new_h), Image.Resampling.NEAREST)

            # 4. Paste barcode onto the center of the canvas
            offset = ((canvas_width - new_w) // 2, (canvas_height - new_h) // 2)
            canvas.paste(resized_barcode, offset)
            
            final_path = "final_2x3_label.png"
            canvas.save(final_path)
            return final_path

    def preview_barcode(self):
        try:
            path = self.generate_fixed_size_barcode()
            img = Image.open(path)
            img.thumbnail((200, 300)) 
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo
        except Exception as e:
            messagebox.showerror("Error", f"Generation failed: {e}")

    def print_barcode(self):
        printer_ip = self.ip_entry.get().strip()
        try:
            path = self.generate_fixed_size_barcode()
            
            # Connect to WiFi printer via Raw Socket (Port 9100)
            p = Network(printer_ip)
            
            # Use 'bitImageRaster' implementation. 
            # This is the most compatible mode for HP printers that support raw data.
            p.image(path, impl="bitImageRaster")
            
            # Cut command (Works on most, ignored by standard inkjets)
            p.cut()
            
            messagebox.showinfo("Success", f"Sent to {printer_ip}")
        except Exception as e:
            messagebox.showerror("Error", f"Printer error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BarcodeApp(root)
    root.mainloop()