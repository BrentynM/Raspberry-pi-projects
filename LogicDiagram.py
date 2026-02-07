import tkinter as tk

class LogicGateSim:
    def __init__(self, root):
        self.root = root
        self.root.title("Full Logic Sim - Deletion Supported")
        self.root.geometry("1100x800")
        
        self.bg_color = "#2c3e50"
        self.gate_color = "#34495e"
        self.wire_color = "#f1c40f"
        self.active_color = "#2ecc71" 
        self.delete_mode_color = "#c0392b"
        
        self.setup_ui()
        
        self.gate_count = 0
        self.gates = {} 
        self.drag_data = {"x": 0, "y": 0, "tag": None}
        self.wire_source = None
        self.is_wiring = False
        self.is_deleting = False

    def setup_ui(self):
        self.sidebar = tk.Frame(self.root, width=180, bg="#1a252f", padx=10, pady=10)
        self.sidebar.pack(side="left", fill="y")
        
        tk.Label(self.sidebar, text="ANSI Symbols", fg="white", bg="#1a252f", font=("Arial", 12, "bold")).pack(pady=10)
        
        gate_types = ["INPUT", "AND", "OR", "NOT", "NAND", "NOR", "XOR"]
        for g_type in gate_types:
            tk.Button(self.sidebar, text=f"Add {g_type}", 
                      command=lambda t=g_type: self.spawn_gate(t),
                      bg="#34495e", fg="white", relief="flat", pady=5).pack(pady=2, fill="x")
        
        self.wire_btn = tk.Button(self.sidebar, text="Wiring Mode: OFF", 
                                  command=self.toggle_wiring, bg="#e67e22", fg="white")
        self.wire_btn.pack(pady=10, fill="x")

        # --- NEW DELETE BUTTON ---
        self.delete_btn = tk.Button(self.sidebar, text="Delete Gate: OFF", 
                                    command=self.toggle_deleting, bg="#7f8c8d", fg="white")
        self.delete_btn.pack(pady=5, fill="x")

        self.canvas = tk.Canvas(self.root, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(side="right", expand=True, fill="both")
        
        self.canvas.tag_bind("gate_group", "<Button-1>", self.on_gate_click)
        self.canvas.tag_bind("gate_group", "<B1-Motion>", self.on_gate_drag)
        self.canvas.tag_bind("wire", "<Button-3>", self.remove_wire)

    def toggle_wiring(self):
        self.is_wiring = not self.is_wiring
        self.is_deleting = False # Mutually exclusive modes
        self.update_mode_buttons()
        self.wire_source = None

    def toggle_deleting(self):
        self.is_deleting = not self.is_deleting
        self.is_wiring = False
        self.update_mode_buttons()

    def update_mode_buttons(self):
        self.wire_btn.config(text=f"Wiring Mode: {'ON' if self.is_wiring else 'OFF'}", 
                             bg="#2ecc71" if self.is_wiring else "#e67e22")
        self.delete_btn.config(text=f"Delete Gate: {'ON' if self.is_deleting else 'OFF'}", 
                               bg=self.delete_mode_color if self.is_deleting else "#7f8c8d")

    def spawn_gate(self, gate_type):
        self.gate_count += 1
        tag = f"gate_{self.gate_count}"
        self.gates[tag] = {"type": gate_type, "val": 0, "outputs": []}
        x, y = 150, 150
        
        if gate_type == "AND":
            self.canvas.create_polygon(x, y, x+40, y, x+60, y+25, x+40, y+50, x, y+50, fill=self.gate_color, outline="white", width=2, smooth=True, tags=(tag, "gate_group", "body"))
        elif gate_type == "OR":
            self.canvas.create_polygon(x, y, x+30, y, x+60, y+25, x+30, y+50, x, y+50, x+15, y+25, fill=self.gate_color, outline="white", width=2, smooth=True, tags=(tag, "gate_group", "body"))
        elif gate_type == "NOT":
            self.canvas.create_polygon(x, y, x+40, y+20, x, y+40, fill=self.gate_color, outline="white", width=2, tags=(tag, "gate_group", "body"))
            self.canvas.create_oval(x+40, y+15, x+50, y+25, outline="white", width=2, tags=(tag, "gate_group"))
        elif gate_type == "NAND":
            self.canvas.create_polygon(x, y, x+40, y, x+60, y+25, x+40, y+50, x, y+50, fill=self.gate_color, outline="white", width=2, smooth=True, tags=(tag, "gate_group", "body"))
            self.canvas.create_oval(x+60, y+20, x+70, y+30, outline="white", width=2, tags=(tag, "gate_group"))
        elif gate_type == "NOR":
            self.canvas.create_polygon(x, y, x+30, y, x+60, y+25, x+30, y+50, x, y+50, x+15, y+25, fill=self.gate_color, outline="white", width=2, smooth=True, tags=(tag, "gate_group", "body"))
            self.canvas.create_oval(x+60, y+20, x+70, y+30, outline="white", width=2, tags=(tag, "gate_group"))
        elif gate_type == "XOR":
            self.canvas.create_line(x-5, y, x+10, y+25, x-5, y+50, fill="white", width=2, smooth=True, tags=(tag, "gate_group"))
            self.canvas.create_polygon(x, y, x+30, y, x+60, y+25, x+30, y+50, x, y+50, x+15, y+25, fill=self.gate_color, outline="white", width=2, smooth=True, tags=(tag, "gate_group", "body"))
        else: # INPUT
            self.canvas.create_rectangle(x, y, x+60, y+30, fill=self.gate_color, outline="white", width=2, tags=(tag, "gate_group", "body"))

        label = "IN: 0" if gate_type == "INPUT" else gate_type
        self.canvas.create_text(x+25, y+65, text=label, fill="white", font=("Arial", 8), tags=(tag, "gate_group", f"txt_{tag}"))

    def on_gate_click(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item)
        current_tag = next((t for t in tags if t.startswith("gate_") and t != "gate_group"), None)
        if not current_tag: return

        # --- NEW DELETE LOGIC ---
        if self.is_deleting:
            self.delete_gate(current_tag)
            return

        if self.is_wiring:
            if not self.wire_source: self.wire_source = current_tag
            else:
                self.add_connection(self.wire_source, current_tag)
                self.wire_source = None
            return

        if self.gates[current_tag]["type"] == "INPUT":
            self.gates[current_tag]["val"] = 1 if self.gates[current_tag]["val"] == 0 else 0
            self.evaluate_logic()

        self.drag_data.update({"tag": current_tag, "x": event.x, "y": event.y})

    def delete_gate(self, tag):
        """Removes the gate and all its associated wires and logic entries."""
        # 1. Remove from logical structure
        if tag in self.gates:
            del self.gates[tag]
        
        # 2. Cleanup wires that were pointing TO this gate
        for other_tag, data in self.gates.items():
            if tag in data["outputs"]:
                data["outputs"].remove(tag)
        
        # 3. Remove all canvas items associated with this tag
        self.canvas.delete(tag)
        self.redraw_all_wires()
        self.evaluate_logic()

    def add_connection(self, src, dest):
        if src != dest and dest not in self.gates[src]["outputs"]:
            self.gates[src]["outputs"].append(dest)
            self.redraw_all_wires()
            self.evaluate_logic()

    def remove_wire(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item)
        src = next((t.replace("from_", "") for t in tags if t.startswith("from_")), None)
        dest = next((t.replace("to_", "") for t in tags if t.startswith("to_")), None)
        if src and dest:
            if src in self.gates and dest in self.gates[src]["outputs"]:
                self.gates[src]["outputs"].remove(dest)
            self.redraw_all_wires()
            self.evaluate_logic()

    def on_gate_drag(self, event):
        if self.is_wiring or self.is_deleting: return
        tag = self.drag_data["tag"]
        dx, dy = event.x - self.drag_data["x"], event.y - self.drag_data["y"]
        self.canvas.move(tag, dx, dy)
        self.drag_data.update({"x": event.x, "y": event.y})
        self.redraw_all_wires()

    def redraw_all_wires(self):
        self.canvas.delete("wire")
        for src, data in self.gates.items():
            for dest in data["outputs"]:
                s, d = self.canvas.bbox(src), self.canvas.bbox(dest)
                if s and d:
                    # Logic to find the vertical center of the source and destination shapes
                    self.canvas.create_line(s[2], s[1]+(s[3]-s[1])/2, d[0], d[1]+(d[3]-d[1])/2, 
                                            fill=self.wire_color, width=3, tags=("wire", f"from_{src}", f"to_{dest}"))

    def evaluate_logic(self):
        # Multi-pass signal propagation
        for _ in range(len(self.gates) + 1): 
            for tag, data in self.gates.items():
                if data["type"] == "INPUT": continue
                # Filter out inputs from gates that might have been deleted but still in data (failsafe)
                inputs = [self.gates[s]["val"] for s in self.gates if tag in self.gates[s]["outputs"]]
                
                if not inputs:
                    # Special case for NOT/NOR/NAND which might have a default value with no inputs
                    if data["type"] in ["NOT", "NAND", "NOR"]: data["val"] = 1
                    else: data["val"] = 0
                    continue

                t = data["type"]
                if t == "AND":  data["val"] = 1 if all(inputs) and len(inputs) > 1 else 0
                elif t == "OR":   data["val"] = 1 if any(inputs) else 0
                elif t == "NOT":  data["val"] = 1 if inputs[0] == 0 else 0
                elif t == "NAND": data["val"] = 0 if all(inputs) and len(inputs) > 1 else 1
                elif t == "NOR":  data["val"] = 0 if any(inputs) else 1
                elif t == "XOR":  data["val"] = 1 if inputs.count(1) % 2 != 0 else 0
        self.update_visuals()

    def update_visuals(self):
        for tag, data in self.gates.items():
            color = self.active_color if data["val"] == 1 else self.gate_color
            for item in self.canvas.find_withtag(tag):
                if "body" in self.canvas.gettags(item):
                    self.canvas.itemconfig(item, fill=color)
            
            # Find and update text
            txt_items = [i for i in self.canvas.find_withtag(tag) if self.canvas.type(i) == "text"]
            if txt_items:
                label = f"IN: {data['val']}" if data["type"] == "INPUT" else data["type"]
                self.canvas.itemconfig(txt_items[0], text=label)

if __name__ == "__main__":
    root = tk.Tk()
    app = LogicGateSim(root)
    root.mainloop()