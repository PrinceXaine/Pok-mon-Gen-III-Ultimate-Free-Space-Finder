import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, Menu, ttk, Toplevel, BooleanVar
import os
import pyperclip
import ctypes
import shutil
import threading
import configparser

if os.name == 'nt':
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

rom_data = b''
rom_path = ''
species_dict = {}
item_dict = {}
flag_dict = {}

for file, target_dict in [("species.dat", species_dict), ("items.dat", item_dict), ("flags.dat", flag_dict)]:
    if os.path.exists(file):
        with open(file, "r") as f:
            for index, line in enumerate(f):
                name = line.strip()
                if name:
                    target_dict[name] = index + 1

class ToolTip:
    def __init__(self, widget, text, delay=1000):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self.after_id = None
        widget.bind("<Enter>", self.schedule)
        widget.bind("<Leave>", self.cancel)

    def schedule(self, event=None):
        self.cancel()
        self.after_id = self.widget.after(self.delay, self.show_tip)

    def cancel(self, event=None):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        self.hide_tip()

    def show_tip(self):
        if self.tip_window or not self.text:
            return
        x, y, _cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 20
        y = y + cy + self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffff", relief='solid', borderwidth=1,
                         font=("tahoma", "10", "bold"))
        label.pack(ipadx=1)

    def hide_tip(self):
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None



# ---------- Utility Functions ----------
def hex_viewer(data):
    lines = []
    for i in range(0, len(data), 16):
        hex_bytes = ' '.join(f'{b:02X}' for b in rom_data[i:i+16])
        ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in rom_data[i:i+16])
        lines.append(f"{i:08X}\t{hex_bytes:<47}    {ascii_repr}")


    return '\n'.join(lines)

def browse_file():
    global rom_data, rom_path
    path = filedialog.askopenfilename(title="Select a GBA ROM", filetypes=[("GBA ROM", "*.gba")])
    if path:
        rom_path = path
        load_rom_threaded(path)

def load_last_rom():
    try:
        with open("last_rom_path.txt", "r") as f:
            last_path = f.read().strip()
        if os.path.exists(last_path):
            load_rom_threaded(last_path)
        else:
            messagebox.showerror("Error", f"Last ROM not found:\n{last_path}")
    except Exception:
        messagebox.showerror("Error", "No previous ROM found.")


import queue

def load_rom_threaded(path):
    loading_popup = Toplevel(root)
    loading_popup.title("Loading ROM")
    loading_popup.geometry("400x160")
    loading_label = tk.Label(loading_popup, text="Loading ROM, please wait...")
    loading_label.pack(pady=(10, 5))

    load_progress = ttk.Progressbar(loading_popup, orient="horizontal", length=350, mode="determinate")
    load_progress.pack(pady=(0, 10))
    load_progress["value"] = 0

    hex_label = tk.Label(loading_popup, text="")
    hex_label.pack()
    hex_progress = ttk.Progressbar(loading_popup, orient="horizontal", length=350, mode="determinate")
    hex_progress.pack(pady=(0, 10))
    hex_progress["value"] = 0

    progress_queue = queue.Queue()

    def update_progress_ui():
        try:
            while not progress_queue.empty():
                which, value, message = progress_queue.get_nowait()
                if which == "load":
                    load_progress["value"] = value
                    if message:
                        loading_label.config(text=message)
                elif which == "hex":
                    hex_progress["value"] = value
                    if message:
                        hex_label.config(text=message)
        except Exception as e:
            print(f"UI update error: {e}")
        finally:
            if loading_popup.winfo_exists():
                loading_popup.after(50, update_progress_ui)

    def load_and_update():
        import time
        global rom_data

        load_start_time = time.time()

        try:
            file_size = os.path.getsize(path)
            rom_bytes = bytearray()
            read_total = 0
            last_percent = -1

            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    rom_bytes.extend(chunk)
                    read_total += len(chunk)
                    percent = int((read_total / file_size) * 100)
                    if percent > last_percent:
                        progress_queue.put(("load", percent, None))
                        last_percent = percent

            rom_data = bytes(rom_bytes)
            progress_queue.put(("load", 100, "ROM loaded successfully.\nPreparing Hex Viewer..."))
            time.sleep(0.5)
            progress_queue.put(("hex", 0, "Rendering Hex Viewer..."))

            hex_display.delete("1.0", tk.END)
            lines = []
            for i in range(0, len(rom_data), 16):
                hex_bytes = ' '.join(f'{b:02X}' for b in rom_data[i:i+16])
                ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in rom_data[i:i+16])
                lines.append(f"{hex_bytes:<47}    {ascii_repr}")


            chunk_size = 256
            total_chunks = (len(lines) + chunk_size - 1) // chunk_size

            for i in range(total_chunks):
                hex_display.insert(tk.END, "\n".join(lines[i * chunk_size:(i + 1) * chunk_size]) + "\n")
                progress_queue.put(("hex", ((i + 1) / total_chunks) * 100, None))

            time.sleep(0.2)
            hex_display.see("1.0")
            update_hex_line_numbers()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while loading the ROM:\n{e}")
        finally:
            if loading_popup.winfo_exists():
                loading_popup.destroy()
            rom_status_label.config(fg="blue")
            enable_rom_controls()
            load_end_time = time.time()
            duration = load_end_time - load_start_time
            rom_status_var.set(f"ROM loaded: {os.path.basename(path)} ({len(rom_data)} bytes) in {duration:.2f} sec")
            with open("last_rom_path.txt", "w") as f:
                f.write(path)

    update_progress_ui()
    threading.Thread(target=load_and_update, daemon=True).start()


def wrap_text():
    content = text_input.get("1.0", tk.END)
    lines = content.splitlines()
    result = []
    for ln in lines:
        if "= " in ln:
            pre, sep, msg = ln.partition("= ")
            raw = msg.strip()

            if "\\n" in raw or "\\p" in raw:
                result.append(ln)
                continue
            parts = [raw[i:i+36] for i in range(0, len(raw), 36)]
            wrapped = ""
            for idx, part in enumerate(parts):
                wrapped += part
                if idx < len(parts)-1:
                    wrapped += "\\p" if (idx+1)%2==0 else "\\n"
            result.append(f"{pre}{sep}{wrapped}")
        else:
            result.append(ln)
    text_input.delete("1.0", tk.END)
    text_input.insert("1.0", "\n".join(result))
    update_line_numbers()

def save_rom():
    global rom_data, rom_path
    if not rom_data:
        messagebox.showerror("Error", "No ROM loaded.")
        return
    backup_path = rom_path + ".bak"
    shutil.copyfile(rom_path, backup_path)
    with open(rom_path, 'wb') as f:
        f.write(rom_data)
    messagebox.showinfo("ROM Saved", f"ROM saved and backup created at:\n{backup_path}")

def update_hex_editor():
    if rom_data:
        hex_display.delete("1.0", tk.END)
        lines = []

        for i in range(0, len(rom_data), 16):
            hex_bytes = ' '.join(f'{b:02X}' for b in rom_data[i:i+16])
            ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in rom_data[i:i+16])
            lines.append(f"{hex_bytes:<47}    {ascii_repr}")


        chunk_size = 256
        for i in range(0, len(lines), chunk_size):
            hex_display.insert(tk.END, "\n".join(lines[i:i+chunk_size]) + "\n")
            hex_display.update_idletasks()

        hex_display.see("1.0")
        update_hex_line_numbers()


def update_hex_line_numbers():
    if not rom_data:
        return
    line_count = (len(rom_data) + 15) // 16
    offsets = "\n".join(f"{i*16:08X}" for i in range(line_count))
    hex_line_numbers.config(state='normal')
    hex_line_numbers.delete("1.0", "end")
    hex_line_numbers.insert("1.0", offsets)
    hex_line_numbers.config(state='disabled')


def on_hex_cursor_move(event):
    try:
        index = hex_display.index(tk.CURRENT)
        line = int(index.split('.')[0]) - 1
        col = int(index.split('.')[1])

        byte_pos = col // 3
        byte_pos = max(0, min(byte_pos, 15))

        offset = (line * 16) + byte_pos

        fmt = offset_format_var.get()
        if fmt == "0x":
            start_offset_var.set(f"0x{offset:X}")
        elif fmt == "$":
            start_offset_var.set(f"${offset:X}")
        else:
            start_offset_var.set(str(offset))

    except Exception as e:
        print(f"DEBUG: Error in on_hex_cursor_move - {e}")




def is_range_free(start, size, check_byte):
    global rom_data
    block = bytes([check_byte] * size)
    return rom_data[start:start+size] == block

def calculate_offset():
    try:
        fmt = calc_format_var.get()
        start = entry_start.get().strip()
        start_int = parse_offset(start, fmt)

        size_raw = entry_size.get().strip()
        if not size_raw.isdigit():
            raise ValueError("Byte count must be a plain number.")
        size = int(size_raw)

        end = start_int + size - 1

        if start_int < 0 or end >= len(rom_data):
            raise ValueError("Offset out of bounds.")

        result = f"0x{end:X}"
        pyperclip.copy(result)

        ff_free = is_range_free(start_int, size, 0xFF)
        zero_free = is_range_free(start_int, size, 0x00)

        if ff_free or zero_free:
            calc_output.config(fg="blue")
            msg = f"End Offset: {result}\nDesignated range is free."
        else:
            calc_output.config(fg="red")
            msg = f"End Offset: {result}\nWARNING: Range includes offsets used by the ROM!"

        calc_output.config(state='normal')
        calc_output.delete("1.0", tk.END)
        calc_output.insert(tk.END, msg)
        calc_output.config(state='disabled')

    except ValueError:
        messagebox.showerror("Error", "Enter valid hex offset and size.")

def parse_offset(raw, fmt):
    raw = raw.strip()
    if fmt == "0x":
        if not raw.lower().startswith("0x"):
            raise ValueError("Expected offset to start with '0x'")
        return int(raw, 16)
    elif fmt == "$":
        if not raw.startswith("$"):
            raise ValueError("Expected offset to start with '$'")
        return int(raw[1:], 16)
    elif fmt == "plain":
        try:
            return int(raw, 16)
        except ValueError:
            return int(raw)
    else:
        raise ValueError("Invalid format type.")    


def search_free_space():
    global rom_data
    if not rom_data:
        messagebox.showerror("Error", "Please load a ROM first.")
        return

    try:
        fmt = offset_format_var.get()
        start_offset = parse_offset(start_offset_var.get(), fmt)
        needed_size = int(size_var.get())
        selected_type = search_type.get()
        check_val = 0xFF if selected_type == "FF" else 0x00
    except ValueError as e:
        messagebox.showerror("Error", f"Offset error: {e}")
        return

    block = bytes([check_val] * needed_size)
    for i in range(start_offset, len(rom_data) - needed_size + 1):
        if rom_data[i:i + needed_size] == block:
            result = (
                f"Free space found (0x{check_val:02X}):\n"
                f"Start: 0x{i:06X}\n"
                f"End: 0x{i + needed_size - 1:06X}"
            )
            fs_output.delete("1.0", tk.END)
            fs_output.insert(tk.END, result)
            fmt = offset_format_var.get()
            if fmt == "0x":
                search_offset_var.set(f"0x{i:06X}")
            elif fmt == "$":
                search_offset_var.set(f"${i:06X}")
            else:
                search_offset_var.set(str(i))

            scroll_to_offset()
            return

    fs_output.delete("1.0", tk.END)
    fs_output.insert(tk.END, f"No free space found (0x{check_val:02X}).")



def scroll_to_offset():
    raw = search_offset_var.get().strip()
    fmt = offset_format_var.get()

    try:
        if fmt == "0x":
            if not raw.lower().startswith("0x"):
                raise ValueError("Expected offset to start with '0x'")
            offset = int(raw, 16)

        elif fmt == "$":
            if not raw.startswith("$"):
                raise ValueError("Expected offset to start with '$'")
            offset = int(raw[1:], 16)

        elif fmt == "plain":
            if not raw.isdigit():
                raise ValueError("Expected a plain decimal number")
            offset = int(raw)

        else:
            raise ValueError("Invalid format selection.")

        if offset < 0 or offset >= len(rom_data):
            raise ValueError("Offset out of bounds.")

        hex_display.see(f"{offset // 16 + 1}.0")

    except ValueError as e:
        messagebox.showerror("Error", f"Invalid offset: {e}")
        


# ---------- GUI Setup ----------
root = tk.Tk()
root.title("Pokémon Gen III Ultimate Free Space Finder")
root.geometry("700x620")

# Function to toggle controls
rom_controls = []
def disable_rom_controls():
    for ctrl in rom_controls:
        ctrl.config(state='disabled')
def enable_rom_controls():
    for ctrl in rom_controls:
        ctrl.config(state='normal')

disable_rom_controls()

notebook = ttk.Notebook(root)
notebook.pack(expand=1, fill='both')

# ROM Load Status
rom_status_var = tk.StringVar(value="No ROM loaded.")
rom_status_label = tk.Label(root, textvariable=rom_status_var, anchor="w", fg="red")
rom_status_label.pack(fill='x', padx=10, pady=(5, 0))

# Page 1: Hex Editor with Free Space Finder
# === Frame for Hex Editor with Line Numbers ===
frame_hex = tk.Frame(notebook)
hex_frame = tk.Frame(frame_hex)
hex_frame.pack(fill='both', expand=True, padx=10, pady=10)

hex_line_numbers = tk.Text(hex_frame, width=8, padx=5, takefocus=0, border=0, background='lightgray', state='disabled')
hex_line_numbers.pack(side='left', fill='y')

hex_display = tk.Text(hex_frame, wrap=tk.NONE, width=70)
hex_display.pack(side='left', fill='both', expand=True)

hex_scroll = ttk.Scrollbar(hex_frame, orient='vertical', command=lambda *args: (hex_display.yview(*args), hex_line_numbers.yview(*args)))
hex_scroll.pack(side='right', fill='y')
hex_display['yscrollcommand'] = lambda *args: (hex_scroll.set(*args), hex_line_numbers.yview_moveto(args[0]))
hex_line_numbers['yscrollcommand'] = lambda *args: (hex_scroll.set(*args), hex_display.yview_moveto(args[0]))

hex_display.bind("<KeyRelease>", on_hex_cursor_move)
hex_display.bind("<ButtonRelease>", on_hex_cursor_move)
hex_display.config(cursor="xterm", takefocus=True)


fs_controls = tk.Frame(frame_hex)
fs_controls.pack(pady=5)

offset_format_var = tk.StringVar(value="0x")
start_offset_var = tk.StringVar(value="0")
search_offset_var = tk.StringVar(value="0")
size_var = tk.StringVar(value="32")

calc_format_var = tk.StringVar(value="0x")

tk.Label(fs_controls, text="Start Offset:").grid(row=0, column=1)
start_entry = tk.Entry(fs_controls, textvariable=start_offset_var, width=10)
start_entry.grid(row=0, column=2, padx=20)
rom_controls.append(start_entry)


offset_format_ddl = ttk.Combobox(fs_controls, textvariable=offset_format_var, values=["0x", "$", "plain"], width=7, state='readonly')
offset_format_ddl.grid(row=1, column=0, sticky='w', padx=10)

tk.Label(fs_controls, text="Free Space Size:").grid(row=1, column=1)
rom_controls.append(tk.Entry(fs_controls, textvariable=size_var, width=6))
tk.Entry(fs_controls, textvariable=size_var, width=10).grid(row=1, column=2, padx=20)

rom_controls.append(tk.Button(fs_controls, text="Find Free Space", command=search_free_space))
tk.Button(fs_controls, text="Find Free Space", command=search_free_space).grid(row=0, column=3, padx=0)

tk.Label(fs_controls, text="").grid(row=0, column=5, padx=50)

tk.Label(fs_controls, text="Offset:").grid(row=0, column=6, padx=30)
rom_controls.append(tk.Entry(fs_controls, textvariable=search_offset_var, width=10))
tk.Entry(fs_controls, textvariable=search_offset_var, width=10).grid(row=0, column=7, padx=0)

rom_controls.append(tk.Button(fs_controls, text="Scroll to Offset", command=scroll_to_offset))
tk.Button(fs_controls, text="Scroll to Offset", command=scroll_to_offset).grid(row=1, column=7, padx=0)

fs_output = scrolledtext.ScrolledText(frame_hex, height=4)
rom_controls.append(fs_output)
fs_output.pack(padx=10, pady=5, fill='x')

notebook.add(frame_hex, text="Hex Editor")



#======================================#
#============SCRIPT TOOL===============#
#======================================#
frame_script = tk.Frame(notebook)

# Text input with line numbers
text_frame = tk.Frame(frame_script)
text_frame.pack(fill='both', expand=True, padx=10, pady=(5, 0))

line_numbers = tk.Text(text_frame, width=4, padx=5, takefocus=0, border=0,
                    background='lightgray', state='disabled')
line_numbers.pack(side='left', fill='y')

def update_line_numbers():
    line_count = int(text_input.index('end-1c').split('.')[0])
    lines = "\n".join(str(i) for i in range(1, line_count + 1))
    line_numbers.config(state='normal')
    line_numbers.delete("1.0", "end")
    line_numbers.insert("1.0", lines)
    line_numbers.config(state='disabled')

text_input = scrolledtext.ScrolledText(text_frame, height=20)
text_input.pack(side='right', fill='both', expand=True)
text_input.bind("<KeyRelease>", lambda e: update_line_numbers())
text_input.bind("<MouseWheel>", lambda e: update_line_numbers())

# Script utilities frame
script_util = tk.Frame(frame_script)
script_util.pack(fill='x', padx=10, pady=(5,5))

# Dropdowns and entries for script customization
script_config = tk.Frame(frame_script)
script_config.pack(fill='x', padx=10)
flag_label = tk.Label(script_config, text="Flag:")
flag_label.pack(side='left', padx=(10, 5))
flag_var = tk.StringVar(value="0x807")
flag_entry = tk.Entry(script_config, textvariable=flag_var, width=8)
flag_entry.pack(side='left', padx=5)

# Item Dropdown and Quantity
item_label = tk.Label(script_config, text="Item ID:")
item_label.pack(side='left', padx=(0, 5))
item_var = tk.StringVar(value="ITEM_ID")
item_dropdown = ttk.Combobox(script_config, textvariable=item_var, values=["POTION", "SUPER_POTION", "HYPER_POTION"], width=15)
item_dropdown.pack(side='left', padx=5)

qty_label = tk.Label(script_config, text="Qty:")
qty_label.pack(side='left')
qty_var = tk.StringVar(value="1")
qty_entry = tk.Entry(script_config, textvariable=qty_var, width=5)
qty_entry.pack(side='left', padx=5)

# Species Dropdown and Level
species_label = tk.Label(script_config, text="Species:")
species_label.pack(side='left', padx=(10, 5))
species_var = tk.StringVar(value="SPECIES")
species_dropdown = ttk.Combobox(script_config, textvariable=species_var, values=["BULBASAUR", "CHARMANDER", "SQUIRTLE"], width=15)
species_dropdown.pack(side='left', padx=5)

level_label = tk.Label(script_config, text="Level:")
level_label.pack(side='left')
level_var = tk.StringVar(value="5")
level_entry = tk.Entry(script_config, textvariable=level_var, width=5)
level_entry.pack(side='left', padx=5)

script_selector = ttk.Combobox(script_util, values=[
    "Give Item", "Encounter Pokémon", "Battle Trainer", "Find Item", "Give Pokémon",
    "Road-Closed", "Heal Pokémon", "Person Talking", "HM Move Block",
    "Need Item to Proceed", "Move Tutor"
], width=20)
script_selector.set("Select Script")
script_selector.pack(side='left', padx=(2, 0))

def handle_script_insert():
    sel = script_selector.get().lower().replace(" ", "_")
    insert_script(sel, item_var.get(), qty_var.get())

insert_btn = tk.Button(script_util, text="Insert", command=handle_script_insert)
insert_btn.pack(side='left', padx=(5, 10))
ToolTip(insert_btn, "Inserts the designated script below all text in the script above.")

notebook.add(frame_script, text="Script Editor")

# --- Script Tool Functions ---
def calc_text_size(widget):
    text = widget.get("1.0", tk.END).strip()
    byte_count = len(text.encode("utf-8"))
    messagebox.showinfo("Text Size", f"{byte_count} bytes required (UTF-8 encoding).")

def insert_script(script_type, arg1=None, arg2=None):
    if script_type == "give_item":
        item_name = arg1 or "ITEM_ID"
        item_id = item_dict.get(item_name, item_name)
        qty = arg2 or "1"
        snippet = (
            "#org @give\n"
            f"giveitem {item_id} {qty} MSG_NORMAL\n"
            "msgbox @msg MSG_KEEPOPEN\n"
            "callstd MSG_NORMAL\n"
            "release\n"
            "end\n\n"
            "#org @msg\n= Received an item!\n"
        )
    elif script_type == "encounter_pokémon":
        species_name = arg1 or species_var.get()
        species = species_dict.get(species_name, species_name)
        level = arg2 or level_var.get()
        item_name = item_var.get() or "ITEM"
        item = item_dict.get(item_name, item_name)
        flag = flag_var.get() or "0x807"
        snippet = (
            "#dyn 0x740000\n"
            "#org @start\n"
            "special 0x187\n"
            "compare LASTRESULT 2\n"
            "if == jump 0x81A7AE0\n"
            "special 0x188\n"
            "lock\n"
            "faceplayer\n"
            "checksound\n"
            f"cry {species} 2\n"
            "waitcry\n"
            "pause 0x14\n"
            "playsound 0x156 0x0\n"
            f"battle {species} 0x{level} {item}\n"
            f"setflag {flag}\n"
            "special 0x138\n"
            "waitspecial\n"
            f"clearflag {flag}\n"
            "special2 0x800D 0xB4\n"
            "compare LASTRESULT 1\n"
            "if == jump 0x8162558\n"
            "compare LASTRESULT 4\n"
            "if == jump 0x8162561\n"
            "compare LASTRESULT 5\n"
            "if == jump 0x8162561\n"
            "setflag 0x581\n"
            "release\n"
            "end\n"
        )

    elif script_type == "road-closed":
        snippet = (
            "#org @blocker\n"
            "lock\n"
            "faceplayer\n"
            "msgbox @msg MSG_NORMAL\n"
            "callstd MSG_NORMAL\n"
            "release\n"
            "end\n\n"
            "#org @msg\n= You can’t go this way yet.\n"
        )
    elif script_type == "battle_trainer":
        snippet = (
            "#org @trainer\n"
            "trainerbattle 0x0 TRAINER_ID 0x0 @msg_before @msg_after\n"
            "msgbox @msg_after MSG_KEEPOPEN\n"
            "end\n\n"
            "#org @msg_before\n= Prepare to battle!\n\n"
            "#org @msg_after\n= You fought well.\n"
        )
    elif script_type == "find_item":
        snippet = (
            "#org @find\n"
            "fanfare 0x13E\n"
            "msgbox @msg MSG_KEEPOPEN\n"
            "giveitem ITEM_ID QUANTITY MSG_FIND\n"
            "waitfanfare\n"
            "release\n"
            "end\n\n"
            "#org @msg\n= You found an item!\n"
        )
    elif script_type == "give_pokémon":
        snippet = (
            "#org @gift\n"
            "givepokemon SPECIES LEVEL ITEM 0x0 0x0 0x0\n"
            "msgbox @msg MSG_NORMAL\n"
            "release\n"
            "end\n\n"
            "#org @msg\n= You received a Pokémon!\n"
        )
    elif script_type == "heal_pokémon":
        snippet = (
            "#org @heal\n"
            "fanfare 0x13E\n"
            "special 0x0\n"
            "waitstate\n"
            "msgbox @msg MSG_NORMAL\n"
            "callstd MSG_NORMAL\n"
            "release\n"
            "end\n\n"
            "#org @msg\n= Your Pokémon have been fully healed.\n"
        )
    elif script_type == "person_talking":
        snippet = (
            "#org @talk\n"
            "lock\n"
            "faceplayer\n"
            "msgbox @msg MSG_NORMAL\n"
            "callstd MSG_NORMAL\n"
            "release\n"
            "end\n\n"
            "#org @msg\n= Hello there, trainer!\n"
        )
    elif script_type == "hm_move_block":
        snippet = (
            "#org @hmcheck\n"
            "checkitem ITEM_ID\n"
            "compare LASTRESULT 0x0\n"
            "if 0x1 goto @usehm\n"
            "msgbox @msgblock MSG_NORMAL\n"
            "end\n\n"
            "#org @msgblock\n= You need a special move to proceed.\n\n"
            "#org @usehm\n"
            "applymovement PLAYER @walkthrough\n"
            "waitmovement 0x0\n"
            "end\n"
        )
    elif script_type == "need_item_to_proceed":
        snippet = (
            "#org @needitem\n"
            "checkitem ITEM_ID\n"
            "compare LASTRESULT 0x0\n"
            "if 0x1 goto @gotpass\n"
            "msgbox @msgblock MSG_NORMAL\n"
            "end\n\n"
            "#org @msgblock\n= You need a special item to continue.\n\n"
            "#org @gotpass\n"
            "applymovement PLAYER @walkthrough\n"
            "waitmovement 0x0\n"
            "end\n"
        )
    elif script_type == "move_tutor":
        snippet = (
            "#org @tutor\n"
            "lock\n"
            "faceplayer\n"
            "msgbox @msg MSG_YESNO\n"
            "compare LASTRESULT 0x1\n"
            "if 0x1 goto @teach\n"
            "release\n"
            "end\n\n"
            "#org @msg\n= Want me to teach a move?\n\n"
            "#org @teach\n"
            "special 0x133\n"
            "release\n"
            "end\n"
        )
    else:
        snippet = f"#org @custom\n= Script type '{script_type}' not implemented yet.\n"

    text_input.insert(tk.INSERT, snippet + "\n")
    update_line_numbers()
    update_line_numbers()

if species_dict:
    species_dropdown["values"] = list(species_dict.keys())
if item_dict:
    item_dropdown["values"] = list(item_dict.keys())

search_type = tk.StringVar(value="FF")
search_option_menu = ttk.OptionMenu(fs_controls, search_type, "FF", "FF", "00")
search_option_menu.grid(row=0, column=0, padx=(10,0))

def wrap_text():
    content = text_input.get("1.0", tk.END)
    lines = content.splitlines()
    result = []

    for ln in lines:
        if "= " in ln:
            pre, sep, msg = ln.partition("= ")
            raw = msg.strip()
            if "\\n" in raw or "\\p" in raw:
                result.append(ln)
                continue

            words = raw.split()
            wrapped = ""
            line = ""
            count = 0
            for word in words:
                if len(line) + len(word) + 1 > 36:
                    wrapped += line.strip()
                    wrapped += "\\p" if (count % 2) else "\\n"
                    line = ""
                    count += 1
                line += word + " "
            wrapped += line.strip()
            result.append(f"{pre}{sep}{wrapped}")
        else:
            result.append(ln)

    text_input.delete("1.0", tk.END)
    text_input.insert("1.0", "\n".join(result))
    update_line_numbers()

    
#======================================#
#========END OF SCRIPT TOOL============#
#======================================#
offset_top = tk.Toplevel(root)
offset_top.title("Offset Calculator")
offset_top.geometry("400x400")
offset_top.withdraw()
offset_top.protocol("WM_DELETE_WINDOW", lambda: offset_top.withdraw())

calc_output = tk.Text(offset_top, height=5, width=50, state='disabled')
calc_output.pack(pady=(10, 0))


entry_start = tk.Entry(offset_top)
entry_size = tk.Entry(offset_top)
calc_type = tk.StringVar(value="FF")
calc_option_menu = ttk.OptionMenu(offset_top, calc_type, "FF", "FF", "00")
calc_option_menu.pack()

calc_format_menu = ttk.Combobox(offset_top, textvariable=calc_format_var, values=["0x", "$", "plain"], state='readonly', width=7)
calc_format_menu.pack(pady=(5, 0))

tk.Label(offset_top, text="Start Offset:").pack()
entry_start.pack()
tk.Label(offset_top, text="Byte Count:").pack()
entry_size.pack()
tk.Button(offset_top, text="Calculate", command=calculate_offset).pack(pady=10)

tk.Label(offset_top, text="Offset A:").pack()
entry_offset_a = tk.Entry(offset_top)
entry_offset_a.pack()

tk.Label(offset_top, text="Offset B:").pack()
entry_offset_b = tk.Entry(offset_top)
entry_offset_b.pack()

def calculate_difference():
    try:
        fmt = calc_format_var.get()
        a = parse_offset(entry_offset_a.get(), fmt)
        b = parse_offset(entry_offset_b.get(), fmt)
        result = abs(b - a)
        calc_output.config(state='normal')
        calc_output.delete("1.0", tk.END)
        calc_output.insert(tk.END, f"Byte Difference:\n{result} bytes")
        calc_output.config(state='disabled')
    except Exception as e:
        messagebox.showerror("Error", f"Invalid input: {e}")

tk.Button(offset_top, text="Calculate Bytes Between", command=calculate_difference).pack(pady=(5, 10))

# Tools Menu
menu_bar = Menu(root)
file_menu = Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Load Last ROM", command=load_last_rom)
file_menu.add_command(label="Open ROM", command=browse_file)
file_menu.add_command(label="Save ROM", command=save_rom)
menu_bar.add_cascade(label="File", menu=file_menu)
tools_menu = Menu(menu_bar, tearoff=0)
tools_menu.add_command(label="Offset Calculator", command=lambda: offset_top.deiconify())
menu_bar.add_cascade(label="Tools", menu=tools_menu)

wrap_btn = tk.Button(script_util, text="Wrap Messages", command=wrap_text)
wrap_btn.pack(side='left', padx=(0, 10))
ToolTip(wrap_btn, "Wraps all message boxes that begin with '=' at the proper intervals with \\n and \\p.")

root.config(menu=menu_bar)
root.mainloop()