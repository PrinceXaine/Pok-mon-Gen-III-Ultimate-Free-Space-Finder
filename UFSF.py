"""
Pokémon Gen III Ultimate Free Space Finder
A tool for ROM hacking that provides hex editing, free space finding, and script generation.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, Menu, ttk, Toplevel, BooleanVar
import os
import pyperclip
import ctypes
import shutil
import threading
import configparser
import queue

#----------------------------------------------------------------------
# GLOBAL VARIABLES AND INITIALIZATION
#----------------------------------------------------------------------

# Hide console window on Windows
if os.name == 'nt':
   ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Core data variables
rom_data = b''
rom_path = ''
species_dict = {}
item_dict = {}
flag_dict = {}

# Viewport Buffer
current_view_start = 0  # First line currently rendered
view_buffer_size = 500  # Number of lines to render above/below viewport
total_line_count = 0    # Total number of lines in the ROM

# Load dictionary data files
for file, target_dict in [("species.dat", species_dict), ("items.dat", item_dict), ("flags.dat", flag_dict)]:
    if os.path.exists(file):
        with open(file, "r") as f:
            for index, line in enumerate(f):
                name = line.strip()
                if name:
                    target_dict[name] = index + 1

#----------------------------------------------------------------------
# UTILITY CLASSES
#----------------------------------------------------------------------

class ToolTip:
    """Creates tooltip popup for UI elements"""
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

#----------------------------------------------------------------------
# HEX EDITOR UTILITY FUNCTIONS
#----------------------------------------------------------------------

def hex_viewer(data):
    """Generate formatted hex view of binary data"""
    lines = []
    for i in range(0, len(data), 16):
        hex_bytes = ' '.join(f'{b:02X}' for b in rom_data[i:i+16])
        ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in rom_data[i:i+16])
        lines.append(f"{i:08X}\t{hex_bytes:<47}    {ascii_repr}")
    return '\n'.join(lines)

def update_hex_line_numbers():
    """Update line numbers in hex editor"""
    if not rom_data:
        return
    line_count = (len(rom_data) + 15) // 16
    offsets = "\n".join(f"{i*16:08X}" for i in range(line_count))
    hex_line_numbers.config(state='normal')
    hex_line_numbers.delete("1.0", "end")
    hex_line_numbers.insert("1.0", offsets)
    hex_line_numbers.config(state='disabled')

# 3. Replace on_hex_cursor_move with this version
def on_hex_cursor_move(event):
    """Track cursor position in hex display and update offset"""
    try:
        index = hex_display.index(tk.CURRENT)
        line = int(index.split('.')[0]) - 1
        col = int(index.split('.')[1])

        # Ensure we're clicking on a hex byte, not ascii or spaces
        if col >= 48:  # ASCII section
            return
            
        byte_pos = col // 3
        if byte_pos > 15:  # Out of range
            return
            
        offset = (line * 16) + byte_pos

        # Update offset display
        fmt = offset_format_var.get()
        if fmt == "0x":
            start_offset_var.set(f"0x{offset:X}")
        elif fmt == "$":
            start_offset_var.set(f"${offset:X}")
        else:
            start_offset_var.set(str(offset))
        
        # Highlight the byte
        hex_display.tag_remove("highlight", "1.0", "end")
        col_start = byte_pos * 3
        hex_display.tag_add("highlight", f"{line+1}.{col_start}", f"{line+1}.{col_start+2}")

    except Exception as e:
        print(f"DEBUG: Error in on_hex_cursor_move - {e}")

def update_hex_editor():
    """Refresh hex editor display with current ROM data"""
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

def update_rom_data_from_hex_editor():
    """Sync changes from hex editor back to ROM data"""
    global rom_data
    try:
        lines = hex_display.get("1.0", tk.END).splitlines()
        new_data = bytearray()

        for line in lines:
            hex_part = line[:47].strip()
            if not hex_part:
                continue
            hex_bytes = hex_part.split()
            new_data.extend(int(b, 16) for b in hex_bytes)

        rom_data = bytes(new_data)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update ROM data from editor:\n{e}")

# Add this function for highlight management
def highlight_byte(offset):
    """Highlight the byte at the specified offset"""
    if not rom_data or offset >= len(rom_data):
        return
        
    # Calculate line and column for this offset
    line = offset // 16 + 1  # +1 because text widget lines start at 1
    col_offset = offset % 16
    col_start = col_offset * 3  # Each byte takes 3 characters (2 hex digits + 1 space)
    
    # Clear any existing highlights
    hex_display.tag_remove("highlight", "1.0", "end")
    
    # Create highlight tag if it doesn't exist
    if not "highlight" in hex_display.tag_names():
        hex_display.tag_configure("highlight", background="yellow", foreground="black")
        
    # Apply the highlight to the byte at the offset position
    hex_display.tag_add("highlight", f"{line}.{col_start}", f"{line}.{col_start+2}")

#----------------------------------------------------------------------
# ROM FILE OPERATIONS
#----------------------------------------------------------------------

def browse_file():
    """Open file dialog to select a ROM"""
    global rom_data, rom_path
    path = filedialog.askopenfilename(title="Select a GBA ROM", filetypes=[("GBA ROM", "*.gba")])
    if path:
        rom_path = path
        load_rom_threaded(path)

def load_last_rom():
    """Attempt to load the most recently opened ROM"""
    try:
        with open("last_rom_path.txt", "r") as f:
            last_path = f.read().strip()
        if os.path.exists(last_path):
            load_rom_threaded(last_path)
        else:
            messagebox.showerror("Error", f"Last ROM not found:\n{last_path}")
    except Exception:
        messagebox.showerror("Error", "No previous ROM found.")

def load_rom_threaded(path):
    """Load ROM file with virtual rendering for the hex editor"""
    global rom_path, total_line_count, current_view_start
    loading_popup = Toplevel(root)
    loading_popup.title("Loading ROM")
    loading_popup.geometry("400x160")
    loading_label = tk.Label(loading_popup, text="Loading ROM, please wait...")
    loading_label.pack(pady=(10, 5))

    load_progress = ttk.Progressbar(loading_popup, orient="horizontal", length=350, mode="determinate")
    load_progress.pack(pady=(0, 10))
    load_progress["value"] = 0

    progress_queue = queue.Queue()
    rom_path = path

    # Determine thread count immediately (outside the worker thread)
    cpu_count = os.cpu_count() or 4
    thread_count = max(2, min(cpu_count - 1, 32))

    def update_progress_ui():
        """Update UI from progress queue"""
        try:
            while not progress_queue.empty():
                which, value, message = progress_queue.get_nowait()
                if which == "load":
                    load_progress["value"] = value
                    if message:
                        loading_label.config(text=message)
        except Exception as e:
            print(f"UI update error: {e}")
        finally:
            if loading_popup.winfo_exists():
                loading_popup.after(50, update_progress_ui)

    def determine_optimal_threads():
        """Determine optimal thread count based on system and ROM size"""
        # Get CPU count (returns None if indeterminable)
        cpu_count = os.cpu_count() or 4  # Default to 4 if can't determine
        
        # Determine file size to scale appropriately
        try:
            file_size = os.path.getsize(path)
            # For very small ROMs (less than 1MB), fewer threads may be better
            if file_size < 1024 * 1024:
                return max(1, min(2, cpu_count))
            # For moderate ROMs, use about 75% of available cores
            elif file_size < 8 * 1024 * 1024:
                return max(2, int(cpu_count * 0.75))
            # For large ROMs, use nearly all cores, but leave 1-2 for system
            else:
                return max(4, cpu_count - 1)
        except:
            # If we can't determine, use a conservative approach
            return max(2, min(8, int(cpu_count * 0.5)))

    def format_hex_chunk(chunk_data, base_offset, result_queue):
        """Format a chunk of ROM data into hex display lines"""
        lines = []
        for i in range(0, len(chunk_data), 16):
            offset = base_offset + i
            end = min(i + 16, len(chunk_data))
            hex_bytes = ' '.join(f'{b:02X}' for b in chunk_data[i:end])
            hex_bytes = f"{hex_bytes:<47}"
            ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk_data[i:end])
            lines.append((offset // 16, f"{hex_bytes}    {ascii_repr}"))
        result_queue.put(lines)

    def load_and_update():
        """Worker thread for loading ROM"""
        import time
        global rom_data, total_line_count, current_view_start

        load_start_time = time.time()

        try:
            # Load the full ROM into memory
            file_size = os.path.getsize(path)
            progress_queue.put(("load", 0, f"Loading ROM ({file_size/1024/1024:.1f} MB)..."))
            
            rom_bytes = bytearray()
            read_total = 0
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(16384)
                    if not chunk:
                        break
                    rom_bytes.extend(chunk)
                    read_total += len(chunk)
                    percent = int((read_total / file_size) * 100)
                    progress_queue.put(("load", percent, None))

            rom_data = bytes(rom_bytes)
            progress_queue.put(("load", 100, "Preparing virtual hex view..."))
            
            # Reset view state
            current_view_start = 0
            total_line_count = (len(rom_data) + 15) // 16
            
            # Prepare the hex editor
            hex_display.config(state='normal')
            hex_display.delete("1.0", tk.END)
            
            # Set up scrollbar settings
            hex_scroll.config(command=on_virtual_scroll)
            
            # Render initial view
            render_visible_region()
            update_hex_line_numbers_virtual()
            
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

def on_virtual_scroll(*args):
    """Handle scrolling in virtual mode"""
    # Handle scrollbar commands
    hex_display.yview(*args)
    hex_line_numbers.yview(*args)
    
    # Get the new position
    start, end = hex_display.yview()
    
    # Calculate the first visible line
    visible_start = int(start * total_line_count)
    
    # Check if we need to update the view
    buffer_top = max(0, current_view_start)
    buffer_bottom = min(total_line_count, current_view_start + view_buffer_size * 2)
    
    # If scrolled outside the buffered area, re-render
    if visible_start < buffer_top + view_buffer_size//2 or visible_start > buffer_bottom - view_buffer_size//2:
        # Update rendering in a slight delay to avoid multiple renders during fast scrolling
        hex_display.after(10, render_visible_region)
    
def render_visible_region():
    """Render only the current visible region plus buffer"""
    global current_view_start
    
    if not rom_data:
        return
    
    # Get the current position in the view
    start, end = hex_display.yview()
    
    # Calculate the first visible line
    visible_start = int(start * total_line_count)
    
    # Calculate render range with buffer
    render_start = max(0, visible_start - view_buffer_size)
    render_end = min(total_line_count, visible_start + view_buffer_size)
    
    # Save scroll position
    current_position = hex_display.yview()
    
    # Clear and rebuild the display
    hex_display.config(state='normal')
    hex_display.delete("1.0", tk.END)
    
    # Format and insert only the lines in our render range
    lines = []
    for i in range(render_start, render_end):
        offset = i * 16
        chunk_end = min(offset + 16, len(rom_data))
        hex_bytes = ' '.join(f'{b:02X}' for b in rom_data[offset:chunk_end])
        hex_bytes = f"{hex_bytes:<47}"
        ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in rom_data[offset:chunk_end])
        lines.append(f"{hex_bytes}    {ascii_repr}")
    
    hex_display.insert("1.0", "\n".join(lines))
    
    # Track the new view boundaries
    current_view_start = render_start
    
    # Set internal yview so Tkinter knows total content size
    # This requires a bit of a trick with ROW_COUNT dummy lines
    total_height = total_line_count
    first_visible = render_start / total_height
    size_ratio = min(1.0, (render_end - render_start) / total_height)
    
    # Update scrolling
    hex_display.yview_moveto(first_visible)
    hex_scroll.set(start, end)  # Preserve scroll position
    
    # Update line numbers for the rendered region
    update_hex_line_numbers_virtual()

def update_hex_line_numbers_virtual():
    """Update line numbers for virtual rendering"""
    if not rom_data:
        return
    
    hex_line_numbers.config(state='normal')
    hex_line_numbers.delete("1.0", "end")
    
    # Only render line numbers for visible area
    offsets = "\n".join(f"{(current_view_start+i)*16:08X}" for i in range(view_buffer_size * 2))
    hex_line_numbers.insert("1.0", offsets)
    hex_line_numbers.config(state='disabled')

# Update the hex editor's scroll binding
   
def after_scroll():
    """Handle scroll events with slight delay to avoid multiple renders"""
    hex_display.after(10, render_visible_region)

def setup_virtual_hex_editor():
    # Update scrollbar command
    hex_scroll.config(command=on_virtual_scroll)
    
    # Bind additional scroll events
    hex_display.bind("<MouseWheel>", lambda e: after_scroll())
    hex_display.bind("<Up>", lambda e: after_scroll())
    hex_display.bind("<Down>", lambda e: after_scroll())
    hex_display.bind("<Prior>", lambda e: after_scroll())  # Page Up
    hex_display.bind("<Next>", lambda e: after_scroll())   # Page Down
    
    # Update initial state
    total_line_count = (len(rom_data) + 15) // 16 if rom_data else 0

def save_rom():
    """Save changes to ROM file with backup"""
    global rom_data, rom_path
    if not rom_data:
        messagebox.showerror("Error", "No ROM loaded.")
        return
    update_rom_data_from_hex_editor()  # Sync editor to memory
    backup_path = rom_path + ".bak"
    shutil.copyfile(rom_path, backup_path)
    with open(rom_path, 'wb') as f:
        f.write(rom_data)
    messagebox.showinfo("ROM Saved", f"ROM saved and backup created at:\n{backup_path}")

#----------------------------------------------------------------------
# FREE SPACE FINDER FUNCTIONS
#----------------------------------------------------------------------

def parse_offset(raw, fmt):
    """Parse offset string based on format (0x, $, plain)"""
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

def is_range_free(start, size, check_byte):
    """Check if a block of memory is filled with a specific byte value"""
    global rom_data
    block = bytes([check_byte] * size)
    return rom_data[start:start+size] == block

def search_free_space():
    """Find a block of free space in ROM"""
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

# 2. Replace scroll_to_offset function with this version
def scroll_to_offset():
    """Scroll the hex editor to a specific offset and highlight it"""
    global current_view_start, total_line_count
    raw = search_offset_var.get().strip()
    fmt = offset_format_var.get()

    try:
        # Parse the offset based on format
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

        # Calculate line number and position within line
        target_line = offset // 16
        byte_pos = offset % 16
        
        # Force a complete re-render centered on the target line
        view_start = max(0, target_line - (view_buffer_size // 2))
        view_end = min(total_line_count, view_start + view_buffer_size * 2)
        
        # Update the current view state
        current_view_start = view_start
        
        # Clear the display before rendering
        hex_display.config(state='normal')
        hex_display.delete("1.0", tk.END)
        
        # Format and insert only the lines in our render range
        lines = []
        for i in range(view_start, view_end):
            offset_i = i * 16
            chunk_end = min(offset_i + 16, len(rom_data))
            hex_bytes = ' '.join(f'{b:02X}' for b in rom_data[offset_i:chunk_end])
            hex_bytes = f"{hex_bytes:<47}"
            ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in rom_data[offset_i:chunk_end])
            lines.append(f"{hex_bytes}    {ascii_repr}")
        
        hex_display.insert("1.0", "\n".join(lines))
        
        # Update line numbers for the rendered region
        update_hex_line_numbers_virtual()
        
        # Calculate widget position (line in the visible area)
        widget_line = target_line - view_start + 1  # +1 because text widget lines start at 1
        col_start = byte_pos * 3  # Each byte is 2 hex digits + 1 space
        
        # Force the widget to update
        hex_display.update()
        
        # Clear existing highlights
        hex_display.tag_remove("highlight", "1.0", "end")
        
        # Apply new highlight
        hex_display.tag_add("highlight", f"{widget_line}.{col_start}", f"{widget_line}.{col_start+2}")
        
        # Scroll to position with extra space around
        hex_display.see(f"{widget_line}.0")
        hex_display.update()

    except ValueError as e:
        messagebox.showerror("Error", f"Invalid offset: {e}")

def calculate_offset():
    """Calculate end offset based on start offset and size"""
    if not rom_data:
        messagebox.showerror("Error", "No ROM loaded.")
        return
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

#----------------------------------------------------------------------
# SCRIPT EDITOR FUNCTIONS
#----------------------------------------------------------------------

def update_line_numbers():
    """Update line numbers in script editor"""
    line_count = int(text_input.index('end-1c').split('.')[0])
    lines = "\n".join(str(i) for i in range(1, line_count + 1))
    line_numbers.config(state='normal')
    line_numbers.delete("1.0", "end")
    line_numbers.insert("1.0", lines)
    line_numbers.config(state='disabled')

def wrap_text():
    """Wrap script messages for in-game display"""
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

def calc_text_size(widget):
    """Calculate byte size of text content"""
    text = widget.get("1.0", tk.END).strip()
    byte_count = len(text.encode("utf-8"))
    messagebox.showinfo("Text Size", f"{byte_count} bytes required (UTF-8 encoding).")

def insert_script(script_type, arg1=None, arg2=None):
    """Insert script template based on selected type"""
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
            "#org @msg\n= You can't go this way yet.\n"
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

def handle_script_insert():
    """Handle script insertion with selected options"""
    sel = script_selector.get().lower().replace(" ", "_")
    insert_script(sel, item_var.get(), qty_var.get())

#----------------------------------------------------------------------
# OFFSET CALCULATOR AND ERASE TOOLS
#----------------------------------------------------------------------

def calculate_difference():
    """Calculate byte difference between two offsets and check if range is free"""
    try:
        fmt = calc_format_var.get()
        a = parse_offset(entry_offset_a.get(), fmt)
        b = parse_offset(entry_offset_b.get(), fmt)
        
        # Ensure a is the smaller value
        start = min(a, b)
        end = max(a, b)
        size = end - start + 1
        
        # Calculate the byte difference
        result = size
        
        # Check if the range is free (all 0xFF or all 0x00)
        ff_free = is_range_free(start, size, 0xFF)
        zero_free = is_range_free(start, size, 0x00)
        
        # Format the result message
        if ff_free or zero_free:
            calc_output.config(fg="blue")
            msg = f"Byte Difference: {result} bytes\n"
            if ff_free:
                msg += "Range is free (0xFF)"
            else:
                msg += "Range is free (0x00)"
        else:
            calc_output.config(fg="red")
            msg = f"Byte Difference: {result} bytes\nWARNING: Range includes offsets used by the ROM!"
        
        # Update the output
        calc_output.config(state='normal')
        calc_output.delete("1.0", tk.END)
        calc_output.insert(tk.END, msg)
        calc_output.config(state='disabled')
        
        # Copy result to clipboard like the other function does
        pyperclip.copy(str(result))
        
    except Exception as e:
        messagebox.showerror("Error", f"Invalid input: {e}")

def erase_range():
    """Erase a range of bytes in the ROM"""
    global rom_data
    if not rom_data:
        messagebox.showerror("Error", "No ROM loaded.")
        return
    confirm = messagebox.askyesno(
        "Confirm Erase",
        "WARNING! You are about to erase data from the ROM!\n\nHave you verified this data is not needed?",
        icon='warning'
    )
    if not confirm:
        return
    try:
        start = parse_offset_str(er_start_range.get())
        end = parse_offset_str(er_end_range.get())
        value = 0xFF if byte_type_range.get() == "FF" else 0x00

        if start > end or end >= len(rom_data):
            raise ValueError("Invalid range")

        temp_data = bytearray(rom_data)
        for i in range(start, end + 1):
            temp_data[i] = value

        rom_data = bytes(temp_data)
        messagebox.showinfo("Success", f"Erased bytes from 0x{start:X} to 0x{end:X}")
        update_hex_editor()

    except Exception as e:
        messagebox.showerror("Error", str(e))

def erase_count():
    """Erase specific number of bytes from the ROM"""
    global rom_data
    if not rom_data:
        messagebox.showerror("Error", "No ROM loaded.")
        return
    confirm = messagebox.askyesno(
        "Confirm Erase",
        "WARNING! You are about to erase data from the ROM!\n\nHave you verified this data is not needed?",
        icon='warning'
    )
    if not confirm:
        return
    try:
        start = parse_offset_str(er_start_count.get())
        count = int(er_count.get())
        value = 0xFF if byte_type_count.get() == "FF" else 0x00
        end = start + count
        if end > len(rom_data):
            raise ValueError("Out of bounds")
        temp_data = bytearray(rom_data)
        temp_data[start:end] = bytes([value] * count)
        rom_data = bytes(temp_data)
        messagebox.showinfo("Success", f"Erased {count} bytes from 0x{start:X}")
        update_hex_editor()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def show_erase_tool():
    """Show dialog for erasing ROM data"""
    global er_start_range, er_end_range, byte_type_range
    global er_start_count, er_count, byte_type_count

    erase_top = tk.Toplevel(root)
    erase_top.title("Erase Offset Range")
    erase_top.geometry("480x300")

    frame_left = tk.LabelFrame(erase_top, text="By Offset Range")
    frame_left.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    tk.Label(frame_left, text="Start Offset:").pack()
    er_start_range = tk.Entry(frame_left)
    er_start_range.pack()

    tk.Label(frame_left, text="End Offset:").pack()
    er_end_range = tk.Entry(frame_left)
    er_end_range.pack()

    byte_type_range = tk.StringVar(value="FF")
    ttk.OptionMenu(frame_left, byte_type_range, "FF", "FF", "00").pack(pady=(5, 0))

    tk.Button(frame_left, text="ERASE", fg="red", command=erase_range).pack(pady=10)

    frame_right = tk.LabelFrame(erase_top, text="By Byte Count")
    frame_right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    tk.Label(frame_right, text="Start Offset:").pack()
    er_start_count = tk.Entry(frame_right)
    er_start_count.pack()

    tk.Label(frame_right, text="# of Bytes:").pack()
    er_count = tk.Entry(frame_right)
    er_count.pack()

    byte_type_count = tk.StringVar(value="FF")
    ttk.OptionMenu(frame_right, byte_type_count, "FF", "FF", "00").pack(pady=(5, 0))

    tk.Button(frame_right, text="ERASE", fg="red", command=erase_count).pack(pady=10)

def parse_offset_str(offset_str):
    """Parse offset string using current format setting"""
    fmt = offset_format_var.get()
    return parse_offset(offset_str, fmt)

def update_hex_from_dec(*args):
    """Update hex value when decimal value changes"""
    try:
        dec = int(dec_var.get())
        hex_var.set(f"{dec:X}")
    except ValueError:
        hex_var.set("")

def update_dec_from_hex(*args):
    """Update decimal value when hex value changes"""
    try:
        hex_str = hex_var.get().strip()
        if hex_str:
            dec_var.set(str(int(hex_str, 16)))
        else:
            dec_var.set("")
    except ValueError:
        dec_var.set("")

#----------------------------------------------------------------------
# GUI SETUP
#----------------------------------------------------------------------

# Create main window
root = tk.Tk()
root.title("Pokémon Gen III Ultimate Free Space Finder")
root.geometry("700x620")

# ROM control state management
rom_controls = []
def disable_rom_controls():
    """Disable all ROM-dependent controls"""
    for ctrl in rom_controls:
        ctrl.config(state='disabled')
def enable_rom_controls():
    """Enable all ROM-dependent controls"""
    for ctrl in rom_controls:
        ctrl.config(state='normal')

# Initially disable controls until ROM is loaded
disable_rom_controls()

# Create notebook for tabbed interface
notebook = ttk.Notebook(root)
notebook.pack(expand=1, fill='both')

# ROM status display
rom_status_var = tk.StringVar(value="No ROM loaded.")
rom_status_label = tk.Label(root, textvariable=rom_status_var, anchor="w", fg="red")
rom_status_label.pack(fill='x', padx=10, pady=(5, 0))

#----------------------------------------------------------------------
# HEX EDITOR TAB
#----------------------------------------------------------------------

# Main hex editor frame
frame_hex = tk.Frame(notebook)
hex_frame = tk.Frame(frame_hex)
hex_frame.pack(fill='both', expand=True, padx=10, pady=10)

# Hex editor with line numbers
hex_line_numbers = tk.Text(hex_frame, width=8, padx=5, takefocus=0, border=0, background='lightgray', state='disabled')
hex_line_numbers.pack(side='left', fill='y')

# 1. Add this right after creating hex_display (in the HEX EDITOR TAB section)
hex_display = tk.Text(hex_frame, wrap=tk.NONE, width=70)
hex_display.pack(side='left', fill='both', expand=True)
# Configure highlight tag during initialization
hex_display.tag_configure("highlight", background="#ffff00", foreground="#000000")

# Scrollbar setup for hex editor
hex_scroll = ttk.Scrollbar(hex_frame, orient='vertical', command=lambda *args: (hex_display.yview(*args), hex_line_numbers.yview(*args)))
hex_scroll.pack(side='right', fill='y')
hex_display['yscrollcommand'] = lambda *args: (hex_scroll.set(*args), hex_line_numbers.yview_moveto(args[0]))
hex_line_numbers['yscrollcommand'] = lambda *args: (hex_scroll.set(*args), hex_display.yview_moveto(args[0]))

# Event bindings for hex editor
hex_display.bind("<KeyRelease>", on_hex_cursor_move)
hex_display.bind("<ButtonRelease>", on_hex_cursor_move)
hex_display.config(cursor="xterm", takefocus=True)


# Free space finder controls
fs_controls = tk.Frame(frame_hex)
fs_controls.pack(pady=5)

# Format and offset variables
offset_format_var = tk.StringVar(value="0x")
start_offset_var = tk.StringVar(value="0")
search_offset_var = tk.StringVar(value="0")
size_var = tk.StringVar(value="32")
calc_format_var = tk.StringVar(value="0x")

# Search type selector (FF or 00)
search_type = tk.StringVar(value="FF")
search_option_menu = ttk.OptionMenu(fs_controls, search_type, "FF", "FF", "00")
search_option_menu.grid(row=0, column=0, padx=(10,0))

# Free space controls layout
tk.Label(fs_controls, text="Start Offset:").grid(row=0, column=1)
start_entry = tk.Entry(fs_controls, textvariable=start_offset_var, width=10)
start_entry.grid(row=0, column=2, padx=20)
rom_controls.append(start_entry)

offset_format_ddl = ttk.Combobox(fs_controls, textvariable=offset_format_var, 
                                values=["0x", "$", "plain"], width=7, state='readonly')
offset_format_ddl.grid(row=1, column=0, sticky='w', padx=10)

tk.Label(fs_controls, text="Free Space Size:").grid(row=1, column=1)
size_entry = tk.Entry(fs_controls, textvariable=size_var, width=10)
size_entry.grid(row=1, column=2, padx=20)
rom_controls.append(size_entry)

find_btn = tk.Button(fs_controls, text="Find Free Space", command=search_free_space)
find_btn.grid(row=0, column=3, padx=0)
rom_controls.append(find_btn)

# Spacer
tk.Label(fs_controls, text="").grid(row=0, column=5, padx=50)

# Offset navigation controls
tk.Label(fs_controls, text="Offset:").grid(row=0, column=6, padx=30)
offset_entry = tk.Entry(fs_controls, textvariable=search_offset_var, width=10)
offset_entry.grid(row=0, column=7, padx=0)
rom_controls.append(offset_entry)

scroll_btn = tk.Button(fs_controls, text="Scroll to Offset", command=scroll_to_offset)
scroll_btn.grid(row=1, column=7, padx=0)
rom_controls.append(scroll_btn)

# Output area for free space finder
fs_output = scrolledtext.ScrolledText(frame_hex, height=4)
fs_output.pack(padx=10, pady=5, fill='x')
rom_controls.append(fs_output)

# Add hex editor tab to notebook
notebook.add(frame_hex, text="Hex Editor")

#----------------------------------------------------------------------
# SCRIPT EDITOR TAB
#----------------------------------------------------------------------

frame_script = tk.Frame(notebook)

# Text input area with line numbers
text_frame = tk.Frame(frame_script)
text_frame.pack(fill='both', expand=True, padx=10, pady=(5, 0))

line_numbers = tk.Text(text_frame, width=4, padx=5, takefocus=0, border=0, background='lightgray', state='disabled')
line_numbers.pack(side='left', fill='y')

text_input = scrolledtext.ScrolledText(text_frame, height=20)
text_input.pack(side='right', fill='both', expand=True)
text_input.bind("<KeyRelease>", lambda e: update_line_numbers())
text_input.bind("<MouseWheel>", lambda e: update_line_numbers())

# Script utilities toolbar
script_util = tk.Frame(frame_script)
script_util.pack(fill='x', padx=10, pady=(5,5))

# Script type selector
script_selector = ttk.Combobox(script_util, values=[
    "Give Item", "Encounter Pokémon", "Battle Trainer", "Find Item", "Give Pokémon",
    "Road-Closed", "Heal Pokémon", "Person Talking", "HM Move Block",
    "Need Item to Proceed", "Move Tutor"
], width=20)
script_selector.set("Select Script")
script_selector.pack(side='left', padx=(2, 0))

# Script insertion button
insert_btn = tk.Button(script_util, text="Insert", command=handle_script_insert)
insert_btn.pack(side='left', padx=(5, 10))
ToolTip(insert_btn, "Inserts the designated script below all text in the script above.")

# Text wrapping button
wrap_btn = tk.Button(script_util, text="Wrap Messages", command=wrap_text)
wrap_btn.pack(side='left', padx=(0, 10))
ToolTip(wrap_btn, "Wraps all message boxes that begin with '=' at the proper intervals with \\n and \\p.")

# Script configuration options
script_config = tk.Frame(frame_script)
script_config.pack(fill='x', padx=10)

# Flag option
flag_label = tk.Label(script_config, text="Flag:")
flag_label.pack(side='left', padx=(10, 5))
flag_var = tk.StringVar(value="0x807")
flag_entry = tk.Entry(script_config, textvariable=flag_var, width=8)
flag_entry.pack(side='left', padx=5)

# Item options
item_label = tk.Label(script_config, text="Item ID:")
item_label.pack(side='left', padx=(0, 5))
item_var = tk.StringVar(value="ITEM_ID")
item_dropdown = ttk.Combobox(script_config, textvariable=item_var, values=list(item_dict.keys()) if item_dict else ["File Missing"], width=15)
item_dropdown.pack(side='left', padx=5)

qty_label = tk.Label(script_config, text="Qty:")
qty_label.pack(side='left')
qty_var = tk.StringVar(value="1")
qty_entry = tk.Entry(script_config, textvariable=qty_var, width=5)
qty_entry.pack(side='left', padx=5)

# Species options
species_label = tk.Label(script_config, text="Species:")
species_label.pack(side='left', padx=(10, 5))
species_var = tk.StringVar(value="SPECIES")
species_dropdown = ttk.Combobox(script_config, textvariable=species_var, values=list(species_dict.keys()) if species_dict else ["File Missing"], width=15)
species_dropdown.pack(side='left', padx=5)

level_label = tk.Label(script_config, text="Level:")
level_label.pack(side='left')
level_var = tk.StringVar(value="5")
level_entry = tk.Entry(script_config, textvariable=level_var, width=5)
level_entry.pack(side='left', padx=5)

# Add script editor tab to notebook
notebook.add(frame_script, text="Script Editor")

#----------------------------------------------------------------------
# OFFSET CALCULATOR WINDOW
#----------------------------------------------------------------------

offset_top = tk.Toplevel(root)
offset_top.title("Offset Calculator")
offset_top.geometry("350x370")
offset_top.withdraw()
offset_top.protocol("WM_DELETE_WINDOW", lambda: offset_top.withdraw())

container = tk.Frame(offset_top)
container.pack(padx=10, pady=10, anchor="nw")  # Anchor to top-left

# Format selector
tk.Label(container, text="Format:").grid(row=0, column=0, sticky="e", padx=(0,5))
calc_format_menu = ttk.Combobox(container, textvariable=calc_format_var, values=["0x", "$", "plain"], state='readonly', width=7)
calc_format_menu.grid(row=0, column=1, sticky="w")

# Start Offset + Byte Count
tk.Label(container, text="Start Offset:").grid(row=1, column=0, sticky="e")
entry_start = tk.Entry(container)
entry_start.grid(row=1, column=1, sticky="w")

tk.Label(container, text="Byte Count:").grid(row=2, column=0, sticky="e")
entry_size = tk.Entry(container)
entry_size.grid(row=2, column=1, sticky="w")

# FF/00 Option
tk.Label(container, text="Byte Type:").grid(row=3, column=0, sticky="e")
calc_type = tk.StringVar(value="FF")
calc_option_menu = ttk.OptionMenu(container, calc_type, "FF", "FF", "00")
calc_option_menu.grid(row=3, column=1, sticky="w")

# Calculate button
btn_calc = tk.Button(container, text="Calculate", command=calculate_offset)
btn_calc.grid(row=4, column=0, columnspan=2, pady=5)

# Output box
calc_output = tk.Text(container, height=4, width=40, state='disabled')
calc_output.grid(row=5, column=0, columnspan=2, pady=(0, 10))

# Offset difference
tk.Label(container, text="Offset A:").grid(row=6, column=0, sticky="e")
entry_offset_a = tk.Entry(container)
entry_offset_a.grid(row=6, column=1, sticky="w")

tk.Label(container, text="Offset B:").grid(row=7, column=0, sticky="e")
entry_offset_b = tk.Entry(container)
entry_offset_b.grid(row=7, column=1, sticky="w")

tk.Button(container, text="Calculate Bytes Between", command=calculate_difference).grid(row=8, column=0, columnspan=2, pady=(5, 10))

# Dec/Hex converter
dec_hex_frame = tk.LabelFrame(container, text="Dec/Hex")
dec_hex_frame.grid(row=9, column=0, columnspan=2, pady=(5,0), sticky="we")

dec_var = tk.StringVar()
hex_var = tk.StringVar()

tk.Label(dec_hex_frame, text="Decimal:").grid(row=0, column=0, sticky="e", padx=(5, 2))
dec_entry = tk.Entry(dec_hex_frame, textvariable=dec_var, width=15)
dec_entry.grid(row=0, column=1, sticky="w", padx=(0, 5))

tk.Label(dec_hex_frame, text="Hex:").grid(row=1, column=0, sticky="e", padx=(5, 2))
hex_entry = tk.Entry(dec_hex_frame, textvariable=hex_var, width=15)
hex_entry.grid(row=1, column=1, sticky="w", padx=(0, 5))

# Bind updates
dec_var.trace_add("write", update_hex_from_dec)
hex_var.trace_add("write", update_dec_from_hex)


#----------------------------------------------------------------------
# MENU SETUP
#----------------------------------------------------------------------

menu_bar = Menu(root)
root.config(menu=menu_bar)

# File menu
file_menu = Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Load Last ROM", command=load_last_rom)
file_menu.add_command(label="Open ROM", command=browse_file)
file_menu.add_command(label="Save ROM", command=save_rom)
menu_bar.add_cascade(label="File", menu=file_menu)

# Tools menu
tools_menu = Menu(menu_bar, tearoff=0)
tools_menu.add_command(label="Offset Calculator", command=lambda: offset_top.deiconify())
tools_menu.add_command(label="Erase Offset Range", command=show_erase_tool)
menu_bar.add_cascade(label="Tools", menu=tools_menu)

#----------------------------------------------------------------------
# MAIN APP ENTRY POINT
#----------------------------------------------------------------------

if __name__ == "__main__":
    setup_virtual_hex_editor()
    root.mainloop()
