import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import sys
import subprocess
from pynput import keyboard
import threading
import time
import winreg
import base64
import zlib

class HotkeyManager:
    def __init__(self):
        self.hotkeys = []
        self.listener = None
        self.is_running = False
        self.load_config()
        
    def load_config(self):
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'hotkeys.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    self.hotkeys = data.get('hotkeys', [])
            else:
                # Create default hotkeys
                self.hotkeys = [
                    {
                        'id': 1,
                        'modifiers': ['ctrl', 'shift'],
                        'key': 'c',
                        'command': 'calc',
                        'description': 'Open Calculator'
                    },
                    {
                        'id': 2,
                        'modifiers': ['ctrl', 'shift'],
                        'key': 'n',
                        'command': 'notepad',
                        'description': 'Open Notepad'
                    },
                    {
                        'id': 3,
                        'modifiers': ['ctrl', 'shift'],
                        'key': 'p',
                        'command': 'cmd',
                        'description': 'Open Command Prompt'
                    }
                ]
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.hotkeys = []
    
    def save_config(self):
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'hotkeys.json')
            with open(config_path, 'w') as f:
                json.dump({'hotkeys': self.hotkeys}, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def add_hotkey(self, modifiers, key, command, description):
        new_id = max([h['id'] for h in self.hotkeys], default=0) + 1
        hotkey = {
            'id': new_id,
            'modifiers': modifiers,
            'key': key,
            'command': command,
            'description': description
        }
        self.hotkeys.append(hotkey)
        self.save_config()
        return new_id
    
    def update_hotkey(self, hotkey_id, modifiers, key, command, description):
        """Update an existing hotkey"""
        for hotkey in self.hotkeys:
            if hotkey['id'] == hotkey_id:
                hotkey['modifiers'] = modifiers
                hotkey['key'] = key
                hotkey['command'] = command
                hotkey['description'] = description
                self.save_config()
                return True
        return False
    
    def remove_hotkey(self, hotkey_id):
        self.hotkeys = [h for h in self.hotkeys if h['id'] != hotkey_id]
        self.save_config()
    
    def execute_command(self, command):
        try:
            print(f"Executing: {command}")
            subprocess.Popen(command, shell=True)
            return True
        except Exception as e:
            print(f"Error executing command '{command}': {e}")
            return False

    def start_listener(self):
        """Start listening for hotkeys"""
        if self.is_running:
            return True
            
        try:
            # Build hotkey dictionary
            hotkeys_dict = {}
            
            for hotkey in self.hotkeys:
                try:
                    combo_parts = []
                    for mod in hotkey['modifiers']:
                        if mod == 'ctrl': combo_parts.append('<ctrl>')
                        elif mod == 'shift': combo_parts.append('<shift>')
                        elif mod == 'alt': combo_parts.append('<alt>')
                    
                    # Handle different key formats
                    key = hotkey['key'].lower()
                    
                    # Map special keys to pynput format
                    key_mapping = {
                        'escape': '<esc>', 'tab': '<tab>', 'caps_lock': '<caps_lock>',
                        'shift': '<shift>', 'ctrl': '<ctrl>', 'alt': '<alt>',
                        'space': '<space>', 'enter': '<enter>', 'backspace': '<backspace>',
                        'delete': '<delete>', 'insert': '<insert>', 'home': '<home>',
                        'end': '<end>', 'page_up': '<page_up>', 'page_down': '<page_down>',
                        'print_screen': '<print_screen>', 'scroll_lock': '<scroll_lock>',
                        'pause': '<pause>', 'up': '<up>', 'down': '<down>',
                        'left': '<left>', 'right': '<right>',
                        'numpad_0': '<num_0>', 'numpad_1': '<num_1>', 'numpad_2': '<num_2>',
                        'numpad_3': '<num_3>', 'numpad_4': '<num_4>', 'numpad_5': '<num_5>',
                        'numpad_6': '<num_6>', 'numpad_7': '<num_7>', 'numpad_8': '<num_8>',
                        'numpad_9': '<num_9>', 'numpad_add': '<num_add>',
                        'numpad_subtract': '<num_subtract>', 'numpad_multiply': '<num_multiply>',
                        'numpad_divide': '<num_divide>', 'numpad_decimal': '<num_decimal>',
                        'numpad_enter': '<num_enter>'
                    }
                    
                    # Use mapped key or the original key
                    mapped_key = key_mapping.get(key, key)
                    combo_str = '+'.join(combo_parts) + '+' + mapped_key
                    command = hotkey['command']
                    
                    hotkeys_dict[combo_str] = lambda cmd=command: self.execute_command(cmd)
                    print(f"Registered: {combo_str} -> {command}")
                    
                except Exception as e:
                    print(f"Failed to register {hotkey['description']}: {e}")
                    continue
            
            self.listener = keyboard.GlobalHotKeys(hotkeys_dict)
            self.listener.start()
            self.is_running = True
            print("Hotkey listener started successfully")
            return True
            
        except Exception as e:
            print(f"Error starting hotkey listener: {e}")
            self.is_running = False
            return False
    
    def stop_listener(self):
        if self.listener:
            try:
                self.listener.stop()
                self.listener = None
                self.is_running = False
                print("Hotkey listener stopped")
            except Exception as e:
                print(f"Error stopping listener: {e}")
        else:
            self.is_running = False

class ModernHotkeyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hotkey Manager Pro v5")
        self.root.geometry("1350x800")
        self.root.minsize(1000, 700)
        
        # Track currently editing hotkey
        self.editing_hotkey_id = None
        
        # Initialize state first
        self.is_running = False
        
        # Set window icon and style
        self.root.configure(bg='#f0f0f0')
        
        self.manager = HotkeyManager()
        self.setup_styles()
        self.setup_gui()
        self.refresh_hotkeys_list()
        self.update_ui_state()
        
    def setup_styles(self):
        """Configure modern styles"""
        style = ttk.Style()
        
        # Configure colors
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#34495e',
            'accent': '#3498db',
            'success': '#27ae60',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'light': '#ecf0f1',
            'dark': '#2c3e50'
        }
        
        # Configure styles
        style.configure('Primary.TButton', 
                       background=self.colors['accent'],
                       foreground='black',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8))
        
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='black',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8))
        
        style.configure('Danger.TButton',
                       background=self.colors['danger'],
                       foreground='black',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8))
        
        style.configure('Warning.TButton',
                       background=self.colors['warning'],
                       foreground='black',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(15, 8))
        
        style.configure('Title.TLabel',
                       font=('Segoe UI', 20, 'bold'),
                       foreground=self.colors['primary'],
                       background='#f0f0f0')
        
        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 12),
                       foreground=self.colors['secondary'],
                       background='#f0f0f0')
        
        style.configure('Status.TLabel',
                       font=('Segoe UI', 11, 'bold'),
                       padding=(10, 5))
        
        style.configure('Modern.TFrame',
                       background='#ffffff',
                       relief='raised',
                       borderwidth=1)
        
    def setup_gui(self):
        # Main container
        main_container = ttk.Frame(self.root, padding=20, style='Modern.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header Section
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="🚀 Hotkey Manager Pro v5", style='Title.TLabel').pack(side=tk.LEFT)
        
        # Status indicator
        self.status_frame = ttk.Frame(header_frame)
        self.status_frame.pack(side=tk.RIGHT)
        
        # Use grid for better alignment control
        self.status_indicator = ttk.Label(self.status_frame, text="●", font=('Segoe UI', 20), foreground='red')
        self.status_var = tk.StringVar(value="STOPPED")
        status_label = ttk.Label(self.status_frame, textvariable=self.status_var, style='Status.TLabel')
        
        # Use grid for perfect vertical centering
        self.status_indicator.grid(row=0, column=0, padx=(0, 10), sticky='ns')
        status_label.grid(row=0, column=1, sticky='ns')
        self.status_frame.grid_rowconfigure(0, weight=1)
        
        # NEW: Import/Export and Help buttons
        header_buttons = ttk.Frame(header_frame)
        header_buttons.pack(side=tk.RIGHT)
        
        # Import/Export button
        ttk.Button(header_buttons, text="📁 IMPORT/EXPORT", 
                  command=self.show_import_export, style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 10))
        
        # Help button
        ttk.Button(header_buttons, text="❓ HELP", 
                  command=self.show_help, style='Primary.TButton').pack(side=tk.LEFT)
        
        # Control Panel
        control_frame = ttk.LabelFrame(main_container, text="Control Panel", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        control_buttons = ttk.Frame(control_frame)
        control_buttons.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(control_buttons, text="▶ START HOTKEYS", 
                                  command=self.start_daemon, style='Success.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_buttons, text="⏹ STOP HOTKEYS", 
                                 command=self.stop_daemon, style='Danger.TButton')
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_buttons, text="🔄 RESTART", 
                  command=self.restart_daemon, style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_buttons, text="📊 TEST ALL", 
                  command=self.test_all_hotkeys, style='Warning.TButton').pack(side=tk.LEFT)
        
        # Quick Stats
        stats_frame = ttk.Frame(control_frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.stats_var = tk.StringVar(value="Hotkeys: 0 | Active: 0")
        ttk.Label(stats_frame, textvariable=self.stats_var, style='Subtitle.TLabel').pack()
        
        # Main Content Area
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left Panel - Add/Edit Hotkey Form
        left_panel = ttk.LabelFrame(content_frame, text="Add/Edit Hotkey", padding=15)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Hotkey Combination
        combo_frame = ttk.Frame(left_panel)
        combo_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(combo_frame, text="Hotkey Combination:", style='Subtitle.TLabel').pack(anchor=tk.W)
        
        # Modifiers
        mod_frame = ttk.Frame(combo_frame)
        mod_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mod_frame, text="Modifiers:").pack(side=tk.LEFT)
        
        self.ctrl_var = tk.BooleanVar(value=True)
        self.shift_var = tk.BooleanVar(value=True)
        self.alt_var = tk.BooleanVar()
        
        ttk.Checkbutton(mod_frame, text="Ctrl", variable=self.ctrl_var).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Checkbutton(mod_frame, text="Shift", variable=self.shift_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(mod_frame, text="Alt", variable=self.alt_var).pack(side=tk.LEFT, padx=5)
        
        # Key - ENHANCED WITH NUMPAD AND SPECIAL KEYS
        key_frame = ttk.Frame(combo_frame)
        key_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(key_frame, text="Key:").pack(side=tk.LEFT)
        self.key_var = tk.StringVar()

        # Enhanced key list with numpad and special keys
        key_values = (
            # Alphabet
            [chr(i) for i in range(ord('A'), ord('Z')+1)] +
            # Numbers
            [str(i) for i in range(1, 13)] +
            # Function keys
            [f'F{i}' for i in range(1, 13)] +
            # Numpad keys
            ['numpad_0', 'numpad_1', 'numpad_2', 'numpad_3', 'numpad_4', 
             'numpad_5', 'numpad_6', 'numpad_7', 'numpad_8', 'numpad_9',
             'numpad_add', 'numpad_subtract', 'numpad_multiply', 'numpad_divide',
             'numpad_decimal', 'numpad_enter'] +
            # Special keys
            ['escape', 'tab', 'caps_lock', 'shift', 'ctrl', 'alt', 
             'space', 'enter', 'backspace', 'delete'] +
            # Punctuation and symbols
            [',', '.', '/', ';', "'", '[', ']', '-', '=', '`', '\\'] +
            # Navigation keys
            ['insert', 'home', 'end', 'page_up', 'page_down', 
             'print_screen', 'scroll_lock', 'pause'] +
            # Arrow keys
            ['up', 'down', 'left', 'right']
        )

        key_combo = ttk.Combobox(key_frame, textvariable=self.key_var, width=12, values=key_values)
        key_combo.pack(side=tk.LEFT, padx=(10, 0))
        key_combo.set('C')
        
        # Command Section with Browse Button
        ttk.Label(left_panel, text="Application Command:", style='Subtitle.TLabel').pack(anchor=tk.W, pady=(10, 0))
        
        # Command entry with browse button RIGHT NEXT TO IT
        command_frame = ttk.Frame(left_panel)
        command_frame.pack(fill=tk.X, pady=5)
        
        self.command_var = tk.StringVar()
        self.command_entry = ttk.Entry(command_frame, textvariable=self.command_var, font=('Segoe UI', 10))
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Browse button for applications
        self.browse_btn = ttk.Button(command_frame, text="📋", width=3,
                                   command=self.open_appsfolder)
        self.browse_btn.pack(side=tk.RIGHT)
        
        # Create tooltip for browse button
        self.create_tooltip(self.browse_btn, "Open Windows Applications Folder to find exact paths")
        
        # Quick Command Buttons
        quick_cmd_frame = ttk.Frame(left_panel)
        quick_cmd_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(quick_cmd_frame, text="Quick commands:").pack(side=tk.LEFT)
        
        quick_commands = [
            ("🧮 Calculator", "calc"),
            ("📝 Notepad", "notepad"),
            ("💻 CMD", "cmd"),
            ("📁 Explorer", "explorer"),
            ("🌐 Chrome", "chrome"),
            ("🎵 Spotify", "spotify")
        ]
        
        for text, cmd in quick_commands:
            ttk.Button(quick_cmd_frame, text=text, 
                      command=lambda c=cmd: self.command_var.set(c)).pack(side=tk.LEFT, padx=2)
        
        # Instructions for using shell:appsfolder
        instructions_frame = ttk.Frame(left_panel)
        instructions_frame.pack(fill=tk.X, pady=5)
        
        instructions_text = (
            "💡 Tip: Click the 📋 button to open Windows Applications Folder.\n"
            "Right-click any app → Properties → Copy the 'Target' path"
        )
        ttk.Label(instructions_frame, text=instructions_text, 
                 font=('Segoe UI', 9), foreground='#666666', wraplength=400).pack()
        
        # Description
        ttk.Label(left_panel, text="Description:", style='Subtitle.TLabel').pack(anchor=tk.W, pady=(10, 0))
        
        self.desc_var = tk.StringVar()
        desc_entry = ttk.Entry(left_panel, textvariable=self.desc_var, font=('Segoe UI', 10))
        desc_entry.pack(fill=tk.X, pady=5)
        
        # Add/Update Button
        self.add_update_btn = ttk.Button(left_panel, text="➕ ADD HOTKEY", 
                                       command=self.add_or_update_hotkey, style='Primary.TButton')
        self.add_update_btn.pack(fill=tk.X, pady=(15, 0))
        
        # Cancel Edit Button (initially hidden)
        self.cancel_edit_btn = ttk.Button(left_panel, text="❌ CANCEL EDIT", 
                                        command=self.cancel_edit, style='Danger.TButton')
        self.cancel_edit_btn.pack(fill=tk.X, pady=(5, 0))
        self.cancel_edit_btn.pack_forget()  # Hide initially
        
        # Right Panel - Hotkey List
        right_panel = ttk.LabelFrame(content_frame, text="Active Hotkeys", padding=15)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Treeview with scrollbar
        tree_frame = ttk.Frame(right_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('ID', 'Hotkey', 'Command', 'Description')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        column_config = {
            'ID': {'width': 60, 'anchor': tk.CENTER},
            'Hotkey': {'width': 150, 'anchor': tk.CENTER},
            'Command': {'width': 200},
            'Description': {'width': 250}
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, **column_config[col])
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind click event for editing
        self.tree.bind('<<TreeviewSelect>>', self.on_hotkey_select)
        
        # Action Buttons
        action_frame = ttk.Frame(right_panel)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(action_frame, text="🗑️ REMOVE SELECTED", 
                  command=self.remove_hotkey, style='Danger.TButton').pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="🔄 REFRESH LIST", 
                  command=self.refresh_hotkeys_list, style='Primary.TButton').pack(side=tk.LEFT)
        
        ttk.Button(action_frame, text="🧹 CLEAR ALL", 
                  command=self.clear_all_hotkeys, style='Warning.TButton').pack(side=tk.RIGHT)
        
        # Footer
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.message_var = tk.StringVar(value="Ready to manage your hotkeys! Add your first hotkey above.")
        ttk.Label(footer_frame, textvariable=self.message_var, style='Subtitle.TLabel').pack()
        
        # Set defaults
        self.command_var.set("calc")
        self.desc_var.set("Open Calculator")
        
    def show_import_export(self):
        """Show import/export dialog"""
        import_window = tk.Toplevel(self.root)
        import_window.title("Import/Export Hotkeys")
        import_window.geometry("600x500")
        import_window.transient(self.root)
        import_window.grab_set()
        
        # Center the window
        import_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (600 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (500 // 2)
        import_window.geometry(f"600x500+{x}+{y}")
        
        # Main content frame
        content_frame = ttk.Frame(import_window, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Export Section
        export_frame = ttk.LabelFrame(content_frame, text="Export Hotkeys", padding=15)
        export_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(export_frame, text="Export your current hotkeys to share with others:").pack(anchor=tk.W)
        
        # Export buttons
        export_buttons = ttk.Frame(export_frame)
        export_buttons.pack(fill=tk.X, pady=10)
        
        ttk.Button(export_buttons, text="📄 Export to File", 
                  command=self.export_to_file, style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(export_buttons, text="🔐 Export as Encoded String", 
                  command=self.export_as_string, style='Success.TButton').pack(side=tk.LEFT)
        
        # Import Section
        import_frame = ttk.LabelFrame(content_frame, text="Import Hotkeys", padding=15)
        import_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(import_frame, text="Import hotkeys from file or encoded string:").pack(anchor=tk.W)
        
        # Import buttons
        import_buttons = ttk.Frame(import_frame)
        import_buttons.pack(fill=tk.X, pady=10)
        
        ttk.Button(import_buttons, text="📂 Import from File", 
                  command=self.import_from_file, style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(import_buttons, text="🔓 Import from String", 
                  command=self.import_from_string, style='Success.TButton').pack(side=tk.LEFT)
        
        # Import text area
        ttk.Label(import_frame, text="Paste encoded string here:").pack(anchor=tk.W, pady=(10, 5))
        
        self.import_text = tk.Text(import_frame, height=6, font=('Consolas', 9))
        self.import_text.pack(fill=tk.BOTH, expand=True)
        
        # Quick actions
        quick_frame = ttk.Frame(import_frame)
        quick_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(quick_frame, text="🔄 Replace All Hotkeys", 
                  command=lambda: self.import_hotkeys(replace=True), style='Danger.TButton').pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(quick_frame, text="➕ Merge Hotkeys", 
                  command=lambda: self.import_hotkeys(replace=False), style='Warning.TButton').pack(side=tk.LEFT)
        
        # Close button
        ttk.Button(content_frame, text="Close", 
                  command=import_window.destroy, style='Primary.TButton').pack(pady=10)
    
    def export_to_file(self):
        """Export hotkeys to a JSON file"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Hotkeys",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                export_data = {
                    'version': '1.0',
                    'exported_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'hotkeys': self.manager.hotkeys
                }
                
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                messagebox.showinfo("Success", f"Hotkeys exported to:\n{filename}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export hotkeys:\n{str(e)}")
    
    def export_as_string(self):
        """Export hotkeys as an encoded string"""
        try:
            export_data = {
                'version': '1.0',
                'exported_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'hotkeys': self.manager.hotkeys
            }
            
            # Convert to JSON string, compress, and base64 encode
            json_str = json.dumps(export_data)
            compressed = zlib.compress(json_str.encode('utf-8'))
            encoded = base64.b64encode(compressed).decode('ascii')
            
            # Show encoded string in a new window
            string_window = tk.Toplevel(self.root)
            string_window.title("Encoded Hotkeys")
            string_window.geometry("500x350")  # Increased height
            string_window.transient(self.root)
            string_window.grab_set()  # Make it modal
            
            # Center the window
            string_window.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (500 // 2)
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (350 // 2)
            string_window.geometry(f"500x350+{x}+{y}")
            
            content_frame = ttk.Frame(string_window, padding=20)
            content_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(content_frame, text="Encoded Hotkey String", 
                     font=('Segoe UI', 12, 'bold')).pack(pady=(0, 10))
            ttk.Label(content_frame, text="Share this string with others:").pack(anchor=tk.W)
            
            text_widget = tk.Text(content_frame, height=8, font=('Consolas', 9))
            text_widget.pack(fill=tk.BOTH, expand=True, pady=10)
            text_widget.insert('1.0', encoded)
            text_widget.config(state='disabled')
            
            # Copy button with better styling
            copy_frame = ttk.Frame(content_frame)
            copy_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(copy_frame, text="📋 Copy to Clipboard", 
                      command=lambda: self.copy_to_clipboard(encoded, string_window), 
                      style='Success.TButton').pack(side=tk.LEFT, padx=(0, 10))
            
            ttk.Button(copy_frame, text="Close", 
                      command=string_window.destroy, 
                      style='Primary.TButton').pack(side=tk.LEFT)
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to encode hotkeys:\n{str(e)}")
    
    def copy_to_clipboard(self, text, window):
        """Copy text to clipboard and provide feedback"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            # Show success message
            messagebox.showinfo("Success", "Encoded string copied to clipboard!", parent=window)
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy to clipboard:\n{str(e)}", parent=window)
    
    def import_from_file(self):
        """Import hotkeys from a JSON file"""
        try:
            filename = filedialog.askopenfilename(
                title="Import Hotkeys",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r') as f:
                    import_data = json.load(f)
                
                self.process_import_data(import_data, filename)
                
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import hotkeys:\n{str(e)}")
    
    def import_from_string(self):
        """Import hotkeys from an encoded string"""
        try:
            encoded_string = self.import_text.get('1.0', tk.END).strip()
            
            if not encoded_string:
                messagebox.showwarning("Warning", "Please enter an encoded string")
                return
            
            # Try to decode base64 and decompress
            try:
                compressed = base64.b64decode(encoded_string)
                json_str = zlib.decompress(compressed).decode('utf-8')
                import_data = json.loads(json_str)
            except:
                # If decoding fails, try to parse as plain JSON
                import_data = json.loads(encoded_string)
            
            self.process_import_data(import_data, "encoded string")
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to decode hotkeys:\n{str(e)}")
    
    def process_import_data(self, import_data, source):
        """Process imported hotkey data"""
        try:
            if 'hotkeys' not in import_data:
                messagebox.showerror("Import Error", "Invalid hotkey file format")
                return
            
            hotkeys = import_data['hotkeys']
            
            if not isinstance(hotkeys, list):
                messagebox.showerror("Import Error", "Invalid hotkey data format")
                return
            
            # Show import options
            self.show_import_options(hotkeys, source)
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to process imported data:\n{str(e)}")
    
    def show_import_options(self, imported_hotkeys, source):
        """Show options for importing hotkeys"""
        options_window = tk.Toplevel(self.root)
        options_window.title("Import Options")
        options_window.geometry("450x300")  # Increased size
        options_window.transient(self.root)
        options_window.grab_set()
        
        # Center the window
        options_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (450 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (350 // 2)
        options_window.geometry(f"450x325+{x}+{y}")
        
        content_frame = ttk.Frame(options_window, padding=20)  # More padding
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text=f"Import {len(imported_hotkeys)} hotkeys from {source}", 
                 font=('Segoe UI', 12, 'bold')).pack(pady=(0, 20))
        
        # Import options
        self.import_option = tk.StringVar(value="merge")
        
        options_frame = ttk.Frame(content_frame)
        options_frame.pack(fill=tk.X, pady=10)
        
        ttk.Radiobutton(options_frame, text=f"Merge with existing ({len(self.manager.hotkeys)} current)", 
                       variable=self.import_option, value="merge").pack(anchor=tk.W, pady=8)
        
        ttk.Radiobutton(options_frame, text="Replace all existing hotkeys", 
                       variable=self.import_option, value="replace").pack(anchor=tk.W, pady=8)
        
        ttk.Radiobutton(options_frame, text="Keep only non-conflicting hotkeys", 
                       variable=self.import_option, value="noconflict").pack(anchor=tk.W, pady=8)
        
        # Action buttons with better spacing
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="✅ IMPORT", 
                  command=lambda: self.finalize_import(imported_hotkeys, options_window), 
                  style='Success.TButton').pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(button_frame, text="❌ CANCEL", 
                  command=options_window.destroy, 
                  style='Danger.TButton').pack(side=tk.LEFT)
    
    def finalize_import(self, imported_hotkeys, window):
        """Finalize the import based on selected option"""
        try:
            option = self.import_option.get()
            original_count = len(self.manager.hotkeys)
            
            if option == "replace":
                # Replace all hotkeys
                self.manager.hotkeys = imported_hotkeys
                new_count = len(imported_hotkeys)
                action = "replaced"
                
            elif option == "merge":
                # Merge hotkeys (keep both, allow duplicates)
                current_ids = {h['id'] for h in self.manager.hotkeys}
                max_id = max(current_ids) if current_ids else 0
                
                for hotkey in imported_hotkeys:
                    # Assign new IDs to avoid conflicts
                    hotkey['id'] = max_id + 1
                    max_id += 1
                    self.manager.hotkeys.append(hotkey)
                
                new_count = len(self.manager.hotkeys)
                action = "merged"
                
            else:  # noconflict
                # Keep only non-conflicting hotkeys
                current_combos = {frozenset(h['modifiers']): h['key'].lower() for h in self.manager.hotkeys}
                added_count = 0
                max_id = max([h['id'] for h in self.manager.hotkeys], default=0)
                
                for hotkey in imported_hotkeys:
                    combo_key = frozenset(hotkey['modifiers'])
                    if combo_key not in current_combos or current_combos[combo_key] != hotkey['key'].lower():
                        hotkey['id'] = max_id + 1
                        max_id += 1
                        self.manager.hotkeys.append(hotkey)
                        added_count += 1
                
                new_count = len(self.manager.hotkeys)
                action = f"added {added_count} non-conflicting"
            
            # Save and refresh
            self.manager.save_config()
            self.refresh_hotkeys_list()
            
            if self.is_running:
                self.restart_daemon()
            
            window.destroy()
            messagebox.showinfo("Import Successful", 
                              f"Successfully {action} hotkeys!\n"
                              f"Original: {original_count}\n"
                              f"New total: {new_count}")
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import hotkeys:\n{str(e)}")
    
    def import_hotkeys(self, replace=False):
        """Quick import from the text area"""
        try:
            encoded_string = self.import_text.get('1.0', tk.END).strip()
            
            if not encoded_string:
                messagebox.showwarning("Warning", "Please enter an encoded string")
                return
            
            # Try to decode
            try:
                compressed = base64.b64decode(encoded_string)
                json_str = zlib.decompress(compressed).decode('utf-8')
                import_data = json.loads(json_str)
            except:
                import_data = json.loads(encoded_string)
            
            if replace:
                self.manager.hotkeys = import_data['hotkeys']
                action = "replaced"
            else:
                # Merge
                current_ids = {h['id'] for h in self.manager.hotkeys}
                max_id = max(current_ids) if current_ids else 0
                
                for hotkey in import_data['hotkeys']:
                    hotkey['id'] = max_id + 1
                    max_id += 1
                    self.manager.hotkeys.append(hotkey)
                action = "merged"
            
            self.manager.save_config()
            self.refresh_hotkeys_list()
            
            if self.is_running:
                self.restart_daemon()
            
            messagebox.showinfo("Success", f"Hotkeys {action} successfully!")
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import hotkeys:\n{str(e)}")

    def show_help(self):
        """Show comprehensive help dialog with examples"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Hotkey Manager Pro - Help Guide")
        help_window.geometry("900x700")
        help_window.transient(self.root)
        help_window.grab_set()
        
        # Bring to front
        help_window.lift()
        help_window.attributes('-topmost', True)
        help_window.after_idle(help_window.attributes, '-topmost', False)
        
        # Center the help window
        help_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (900 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (700 // 2)
        help_window.geometry(f"900x700+{x}+{y}")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(help_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Quick Start
        quick_start_frame = ttk.Frame(notebook, padding=10)
        notebook.add(quick_start_frame, text="🚀 Quick Start")
        
        quick_start_text = """
🎯 WHAT IS HOTKEY MANAGER PRO?

A powerful tool that lets you create global keyboard shortcuts to launch 
applications, open websites, run commands, and more - instantly!

🔧 BASIC USAGE:

1. Choose Modifiers (Ctrl, Shift, Alt)
2. Select a Key (A-Z, 1-12, F1-F12)  
3. Enter a Command (see examples below)
4. Add Description
5. Click START HOTKEYS

💡 TIPS:
• Click existing hotkeys to edit them
• Use 📋 button to find application paths
• Hotkeys work even when minimized
• Run as Administrator for best results
"""
        ttk.Label(quick_start_frame, text=quick_start_text, font=('Segoe UI', 10), 
                 justify=tk.LEFT, wraplength=850).pack(anchor=tk.W)
        
        # Tab 2: Command Examples
        examples_frame = ttk.Frame(notebook, padding=10)
        notebook.add(examples_frame, text="💡 Command Examples")
        
        examples_text = """
🎮 BASIC APPLICATIONS:
calc                    - Calculator
notepad                 - Notepad  
cmd                     - Command Prompt
explorer                - File Explorer
mspaint                 - Paint
taskmgr                 - Task Manager
control                 - Control Panel

🌐 WEBSITES & LINKS:
start https://google.com        - Open website
start mailto:email@example.com  - Open email client
start outlook:calendar          - Outlook calendar

📁 FOLDERS & LOCATIONS:
explorer C:\\                     - C: drive
explorer shell:Downloads        - Downloads folder
explorer shell:Desktop          - Desktop
explorer C:\\Users\\Name\\Documents - Specific folder

🎯 SYSTEM TOOLS:
devmgmt.msc             - Device Manager
services.msc            - Services
eventvwr.msc            - Event Viewer
appwiz.cpl              - Programs & Features
control printers        - Printers dialog

⚙️ WITH PARAMETERS:
cmd /k "echo Hello"     - CMD that stays open
powershell -Command "Get-Date"  - PowerShell command
"chrome.exe" --incognito        - Chrome incognito
"firefox.exe" -private-window   - Firefox private
explorer /select,"C:\\file.txt" - Select file in Explorer

🎮 STEAM GAMES:
"C:\\Program Files (x86)\\Steam\\steam.exe" -applaunch 322170  - Geometry Dash
"C:\\Program Files (x86)\\Steam\\steam.exe" -applaunch 730     - Counter-Strike 2

🔧 ADVANCED:
powershell -Command "Start-Process notepad; Start-Process calc"  - Multiple apps
cmd /c "command1 && command2"   - Run multiple commands
"""
        
        examples_text_widget = tk.Text(examples_frame, wrap=tk.WORD, font=('Consolas', 9), 
                                      bg='#f8f9fa', relief='flat', padx=10, pady=10)
        examples_text_widget.insert('1.0', examples_text)
        examples_text_widget.config(state='disabled')
        
        scrollbar = ttk.Scrollbar(examples_frame, orient=tk.VERTICAL, command=examples_text_widget.yview)
        examples_text_widget.configure(yscrollcommand=scrollbar.set)
        
        examples_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tab 3: Advanced Features
        advanced_frame = ttk.Frame(notebook, padding=10)
        notebook.add(advanced_frame, text="⚡ Advanced")
        
        advanced_text = """
🎛️ APPLICATION PARAMETERS:

CHROME/EDGE:
--incognito / -inprivate    - Private browsing
--new-window                - New window
--profile-directory="Name"  - Specific profile
--disable-extensions        - No extensions

FIREFOX:
-private-window             - Private browsing
-new-tab URL               - New tab
-profilemanager            - Profile manager

FILE EXPLORER:
/select,"path"             - Select file/folder
/e,                        - Open in explorer view
/root,                     - Specify root folder

POWERSHELL:
-Command "script"          - Run PowerShell command
-ExecutionPolicy Bypass    - Bypass execution policy
-File "script.ps1"         - Run PowerShell script

🔍 FINDING PATHS:

1. Use 📋 button for installed apps
2. Search in Start Menu → Right-click → Open file location
3. Common locations:
   • C:\\Program Files\\
   • C:\\Program Files (x86)\\
   • C:\\Users\\YourName\\AppData\\Local\\
   • C:\\Users\\YourName\\AppData\\Roaming\\

🎯 TROUBLESHOOTING:

• "File not found" → Use full path with quotes
• "Access denied" → Run as Administrator  
• Command not working → Test in Command Prompt first
• Hotkeys not working → Click START HOTKEYS button

💾 STEAM GAME IDs:
Find IDs from Steam Store URLs:
store.steampowered.com/app/322170/ → ID: 322170
"""
        
        advanced_text_widget = tk.Text(advanced_frame, wrap=tk.WORD, font=('Consolas', 9), 
                                      bg='#f8f9fa', relief='flat', padx=10, pady=10)
        advanced_text_widget.insert('1.0', advanced_text)
        advanced_text_widget.config(state='disabled')
        
        scrollbar_advanced = ttk.Scrollbar(advanced_frame, orient=tk.VERTICAL, command=advanced_text_widget.yview)
        advanced_text_widget.configure(yscrollcommand=scrollbar_advanced.set)
        
        advanced_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_advanced.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close button
        ttk.Button(help_window, text="Close Help", 
                  command=help_window.destroy, style='Primary.TButton').pack(pady=10)
    
    def create_tooltip(self, widget, text):
        """Create a tooltip that appears when hovering over a widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(tooltip, text=text, background="#ffffe0", relief='solid', borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
    def open_appsfolder(self):
        """Open Windows shell:appsfolder to let users find application paths"""
        try:
            # Open shell:appsfolder - this opens the actual Windows Applications folder
            subprocess.Popen('explorer shell:appsfolder', shell=True)
            
            # Show instructions to the user - CHANGED: Bring to front
            instructions_window = tk.Toplevel(self.root)
            instructions_window.title("Find Application Path")
            instructions_window.geometry("500x300")
            instructions_window.transient(self.root)
            instructions_window.grab_set()
            
            # CHANGED: Bring to front and make sure it stays on top
            instructions_window.lift()
            instructions_window.attributes('-topmost', True)
            instructions_window.after_idle(instructions_window.attributes, '-topmost', False)
            
            # Center the instructions window
            instructions_window.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (500 // 2)
            y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (300 // 2)
            instructions_window.geometry(f"500x300+{x}+{y}")
            
            # Instructions content
            content_frame = ttk.Frame(instructions_window, padding=20)
            content_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(content_frame, text="📋 How to Find Application Path", 
                     font=('Segoe UI', 14, 'bold')).pack(pady=(0, 15))
            
            instructions = (
                "Windows Applications Folder is now open!\n\n"
                "To get an application's path:\n"
                "1. Find the application you want\n"
                "2. Right-click it → Select 'Properties'\n" 
                "3. Copy the 'Target' path\n"
                "4. Paste it in the Application Command field\n\n"
                "This method works for all installed applications!"
            )
            
            ttk.Label(content_frame, text=instructions, font=('Segoe UI', 11), 
                     justify=tk.LEFT, wraplength=450).pack(fill=tk.BOTH, expand=True)
            
            ttk.Button(content_frame, text="OK", 
                      command=instructions_window.destroy, style='Primary.TButton').pack(pady=(15, 0))
            
        except Exception as e:
            print(f"Error opening appsfolder: {e}")
            messagebox.showerror("Error", 
                "Could not open Applications Folder.\n"
                "Please manually browse for the application executable.")
            # Fallback to file browser
            self.browse_application_fallback()
    
    def browse_application_fallback(self):
        """Fallback to traditional file browser"""
        file_path = filedialog.askopenfilename(
            title="Select Application",
            initialdir="C:\\Program Files",
            filetypes=[
                ("Executable files", "*.exe"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            # Add quotes if path contains spaces
            if " " in file_path:
                file_path = f'"{file_path}"'
            
            self.command_var.set(file_path)
            
            if not self.desc_var.get():
                app_name = os.path.basename(file_path).replace('.exe', '').title()
                self.desc_var.set(f"Open {app_name}")
    
    def on_hotkey_select(self, event):
        """When a hotkey is selected in the list, load it into the form for editing"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, 'values')
            hotkey_id = int(values[0])
            
            # Find the hotkey data
            for hotkey in self.manager.hotkeys:
                if hotkey['id'] == hotkey_id:
                    # Set editing mode
                    self.editing_hotkey_id = hotkey_id
                    
                    # Load data into form
                    self.ctrl_var.set('ctrl' in hotkey['modifiers'])
                    self.shift_var.set('shift' in hotkey['modifiers'])
                    self.alt_var.set('alt' in hotkey['modifiers'])
                    self.key_var.set(hotkey['key'].upper())
                    self.command_var.set(hotkey['command'])
                    self.desc_var.set(hotkey['description'])
                    
                    # Update UI for editing mode
                    self.add_update_btn.configure(text="💾 UPDATE HOTKEY")
                    self.cancel_edit_btn.pack(fill=tk.X, pady=(5, 0))
                    self.message_var.set(f"Editing Hotkey ID: {hotkey_id} - Make changes and click UPDATE")
                    break
    
    def cancel_edit(self):
        """Cancel editing mode and clear the form"""
        self.editing_hotkey_id = None
        self.add_update_btn.configure(text="➕ ADD HOTKEY")
        self.cancel_edit_btn.pack_forget()
        
        # Clear form
        self.ctrl_var.set(True)
        self.shift_var.set(True)
        self.alt_var.set(False)
        self.key_var.set('C')
        self.command_var.set('')
        self.desc_var.set('')
        
        # Clear selection in treeview
        self.tree.selection_remove(self.tree.selection())
        self.message_var.set("Edit cancelled. Ready to add new hotkey.")
    
    def add_or_update_hotkey(self):
        """Handle both adding new hotkeys and updating existing ones"""
        modifiers = self.get_modifiers()
        key = self.key_var.get().lower()
        command = self.command_var.get()
        description = self.desc_var.get()
        
        if not modifiers:
            messagebox.showerror("Error", "Please select at least one modifier (Ctrl, Shift, or Alt)")
            return
            
        if not key:
            messagebox.showerror("Error", "Please enter a key")
            return
            
        if not command:
            messagebox.showerror("Error", "Please enter a command")
            return
            
        if not description:
            messagebox.showerror("Error", "Please enter a description")
            return
        
        # Check for duplicates (excluding the one we're editing)
        for hotkey in self.manager.hotkeys:
            if (set(hotkey['modifiers']) == set(modifiers) and 
                hotkey['key'].lower() == key.lower() and
                hotkey['id'] != self.editing_hotkey_id):
                messagebox.showerror("Error", "This hotkey combination is already in use!")
                return
        
        try:
            if self.editing_hotkey_id:
                # Update existing hotkey
                self.manager.update_hotkey(self.editing_hotkey_id, modifiers, key, command, description)
                self.message_var.set(f"✅ Hotkey updated: {'+'.join(modifiers)}+{key.upper()}")
            else:
                # Add new hotkey
                self.manager.add_hotkey(modifiers, key, command, description)
                self.message_var.set(f"✅ Hotkey added: {'+'.join(modifiers)}+{key.upper()}")
            
            self.refresh_hotkeys_list()
            
            # Restart if running
            was_running = self.is_running
            if was_running:
                self.restart_daemon()
            
            # Clear form and exit edit mode
            self.cancel_edit()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to {'update' if self.editing_hotkey_id else 'add'} hotkey: {str(e)}")
    
    def get_modifiers(self):
        modifiers = []
        if self.ctrl_var.get():
            modifiers.append('ctrl')
        if self.shift_var.get():
            modifiers.append('shift')
        if self.alt_var.get():
            modifiers.append('alt')
        return modifiers
        
    def update_ui_state(self):
        """Update UI based on running state"""
        if self.is_running:
            self.status_var.set("RUNNING")
            self.status_indicator.configure(foreground='green')
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.message_var.set("✅ Hotkeys are active! Try your configured shortcuts.")
        else:
            self.status_var.set("STOPPED")
            self.status_indicator.configure(foreground='red')
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.message_var.set("⏸️ Hotkeys are stopped. Click START to enable.")
        
        # Update stats
        total = len(self.manager.hotkeys)
        active = total if self.is_running else 0
        self.stats_var.set(f"Hotkeys: {total} | Active: {active}")
        
    def remove_hotkey(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a hotkey to remove")
            return
        
        item = selected[0]
        hotkey_id = self.tree.item(item)['values'][0]
        
        if messagebox.askyesno("Confirm Removal", "Are you sure you want to remove this hotkey?"):
            self.manager.remove_hotkey(hotkey_id)
            self.refresh_hotkeys_list()
            
            # If we were editing this hotkey, cancel edit mode
            if self.editing_hotkey_id == hotkey_id:
                self.cancel_edit()
            
            if self.is_running:
                self.restart_daemon()
            
            self.message_var.set(f"✅ Hotkey {hotkey_id} removed")
    
    def clear_all_hotkeys(self):
        if not self.manager.hotkeys:
            messagebox.showinfo("Info", "No hotkeys to clear")
            return
            
        if messagebox.askyesno("Confirm Clear", "Remove ALL hotkeys? This cannot be undone."):
            self.manager.hotkeys = []
            self.manager.save_config()
            self.refresh_hotkeys_list()
            
            # Cancel any ongoing edit
            if self.editing_hotkey_id:
                self.cancel_edit()
            
            if self.is_running:
                self.restart_daemon()
            
            self.message_var.set("🧹 All hotkeys cleared")
    
    def test_all_hotkeys(self):
        """Test all hotkeys by executing their commands"""
        if not self.manager.hotkeys:
            messagebox.showinfo("Info", "No hotkeys to test")
            return
            
        for hotkey in self.manager.hotkeys:
            try:
                self.manager.execute_command(hotkey['command'])
                time.sleep(0.5)  # Small delay between executions
            except Exception as e:
                print(f"Failed to test {hotkey['description']}: {e}")
        
        self.message_var.set("🧪 Testing all hotkeys...")
    
    def refresh_hotkeys_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for hotkey in self.manager.hotkeys:
            combo = '+'.join(hotkey['modifiers']) + '+' + hotkey['key'].upper()
            self.tree.insert('', tk.END, values=(
                hotkey['id'], combo, hotkey['command'], hotkey['description']
            ))
        
        self.update_ui_state()
    
    def start_daemon(self):
        try:
            if self.manager.start_listener():
                self.is_running = True
                self.update_ui_state()
                self.message_var.set("🎉 Hotkeys activated! Your shortcuts are now live.")
            else:
                messagebox.showerror("Error", "Failed to start hotkey listener")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start hotkeys:\n{str(e)}")
    
    def stop_daemon(self):
        self.manager.stop_listener()
        self.is_running = False
        self.update_ui_state()
        self.message_var.set("⏹️ Hotkeys stopped")
    
    def restart_daemon(self):
        self.stop_daemon()
        time.sleep(0.5)
        self.start_daemon()
        self.message_var.set("🔄 Hotkeys restarted")

def main():
    try:
        import pynput
    except ImportError:
        messagebox.showerror("Error", "Please install pynput:\npip install pynput")
        return
    
    root = tk.Tk()
    app = ModernHotkeyGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
