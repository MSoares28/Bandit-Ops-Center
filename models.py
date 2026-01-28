import sqlite3
import os
import customtkinter as ctk
import pyperclip

class BanditLevel:
    def __init__(self, lvl=0, password=""):
        self.level = lvl
        self.user = f"bandit{lvl}"
        self.host = "bandit.labs.overthewire.org"
        self.port = 2220
        self.password = password

    def get_ssh_command(self):
        return f"ssh {self.user}@{self.host} -p {self.port}"

class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name
        current_dir = os.path.dirname(__file__)
        self.db_path = os.path.join(current_dir, db_name)
        self.connection = sqlite3.connect(self.db_path)
        self.create_table()
            
    def create_table(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS levels (
                lvl INTEGER PRIMARY KEY,
                password TEXT
            )
        """)
        self.connection.commit() 

    def save_level(self, level_obj):
        cursor = self.connection.cursor()
        query = "INSERT OR REPLACE INTO levels (lvl, password) VALUES (?, ?)"
        cursor.execute(query, (level_obj.level, level_obj.password))
        self.connection.commit()

    def delete_level(self, lvl):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM levels WHERE lvl = ?", (lvl,))
        self.connection.commit()

    def get_all_levels(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT lvl, password FROM levels ORDER BY lvl ASC")
        rows = cursor.fetchall()
        return [BanditLevel(lvl=row[0], password=row[1]) for row in rows]

class BanditApp:
    def __init__(self, root, db_manager):
        self.root = root
        self.db = db_manager
        self.selected_level = None

        # Professional Palette (Light, Dark)
        self.bg_color = ("#F2F2F7", "#1A1A1A")
        self.card_color = ("#FFFFFF", "#242424")
        self.ssh_text_color = ("#2D7D46", "#00FF00") # Dark green for light, Neon for dark

        self.root.title("Bandit Ops Center v2.1")
        self.root.geometry("1000x650")
        self.root.configure(fg_color=self.bg_color)

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        # --- SIDEBAR (Clean & Modern) ---
        self.sidebar_frame = ctk.CTkFrame(self.root, width=240, corner_radius=0, fg_color=("#E5E5EA", "#111111"))
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="BANDIT CMD", 
                                        font=ctk.CTkFont(family="Inter", size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(40, 5))
        
        ctk.CTkLabel(self.sidebar_frame, text="COMMAND CENTER", text_color="gray", font=("Inter", 10, "bold")).grid(row=1, column=0, pady=(0, 20))

        self.level_list = ctk.CTkScrollableFrame(self.sidebar_frame, label_text="OPERATIONAL HISTORY", fg_color="transparent")
        self.level_list.grid(row=2, column=0, padx=15, pady=15, sticky="nsew")

        # Theme Switcher
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, 
                                                            values=["Dark", "Light", "System"],
                                                            command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=4, column=0, padx=20, pady=20)

        # --- MAIN DASHBOARD ---
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.grid(row=0, column=1, padx=40, pady=40, sticky="nsew")

        # Adaptive Header
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 30))
        
        self.level_title = ctk.CTkLabel(self.header_frame, text="System Idle...", 
                                        font=ctk.CTkFont(size=32, weight="bold"))
        self.level_title.pack(side="left")

        self.status_label = ctk.CTkLabel(self.header_frame, text="", text_color=self.ssh_text_color, font=("Inter", 13, "italic"))
        self.status_label.pack(side="right")

        # CARD 1: TARGET ACCESS (SSH)
        self.ssh_card = ctk.CTkFrame(self.main_container, corner_radius=20, fg_color=self.card_color, border_width=1, border_color=("#D1D1D6", "#333333"))
        self.ssh_card.pack(fill="x", pady=15, ipady=20)
        
        ctk.CTkLabel(self.ssh_card, text="TARGET DEPLOYMENT COMMAND", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray").pack(padx=30, anchor="w", pady=(20, 10))
        
        self.ssh_display = ctk.CTkLabel(self.ssh_card, text="Waiting for mission selection...", 
                                        font=ctk.CTkFont(family="Consolas", size=20), 
                                        text_color=self.ssh_text_color)
        self.ssh_display.pack(pady=10)

        self.btn_ssh_copy = ctk.CTkButton(self.ssh_card, text="COPY ACCESS STRING", width=250, height=45,
                                          corner_radius=10, font=ctk.CTkFont(weight="bold"), 
                                          command=self.copy_ssh)
        self.btn_ssh_copy.pack(pady=15)

        # CARD 2: INFILTRATION DATA (Passwords)
        self.creds_card = ctk.CTkFrame(self.main_container, corner_radius=20, fg_color=self.card_color, border_width=1, border_color=("#D1D1D6", "#333333"))
        self.creds_card.pack(fill="x", pady=15, ipady=20)

        ctk.CTkLabel(self.creds_card, text="ENCRYPTED CREDENTIALS", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray").pack(padx=30, anchor="w", pady=(20, 10))
        
        self.pass_input = ctk.CTkEntry(self.creds_card, placeholder_text="Stored password will appear here...",
                                        height=50, font=ctk.CTkFont(family="Consolas", size=18),
                                        fg_color=("#F9F9F9", "#1A1A1A"), border_color=("#D1D1D6", "#444444"),
                                        justify="center")
        self.pass_input.pack(fill="x", padx=80, pady=20)

        self.creds_actions = ctk.CTkFrame(self.creds_card, fg_color="transparent")
        self.creds_actions.pack(pady=5)

        self.btn_save = ctk.CTkButton(self.creds_actions, text="SAVE PROGRESS", fg_color="#34C759", hover_color="#28A745", text_color="white", command=self.save_progress)
        self.btn_save.grid(row=0, column=0, padx=10)

        self.btn_pass_copy = ctk.CTkButton(self.creds_actions, text="COPY PASS", command=self.copy_pass)
        self.btn_pass_copy.grid(row=0, column=1, padx=10)

        self.btn_delete = ctk.CTkButton(self.creds_actions, text="PURGE", fg_color="#FF3B30", hover_color="#D70015", width=60, command=self.delete_level)
        self.btn_delete.grid(row=0, column=2, padx=10)

        # CTA: NEXT MISSION
        self.btn_next = ctk.CTkButton(self.main_container, text="PROMOTE TO NEXT MISSION", 
                                        height=65, font=ctk.CTkFont(size=18, weight="bold"),
                                        corner_radius=12, border_width=2, fg_color="transparent",
                                        command=self.create_next)
        self.btn_next.pack(side="bottom", fill="x", pady=20)

    # --- Methods ---
    def change_appearance_mode(self, new_mode):
        ctk.set_appearance_mode(new_mode)

    def show_status(self, msg):
        self.status_label.configure(text=f"// {msg}")
        self.root.after(2500, lambda: self.status_label.configure(text=""))

    def refresh_list(self):
        for widget in self.level_list.winfo_children():
            widget.destroy()
        for lvl in self.db.get_all_levels():
            btn = ctk.CTkButton(self.level_list, text=f"MISSION {lvl.level}", 
                                fg_color="transparent", text_color=("black", "white"),
                                hover_color=("#D1D1D6", "#333333"), anchor="w",
                                command=lambda obj=lvl: self.load_details(obj))
            btn.pack(fill="x", pady=4, padx=5)

    def load_details(self, level_obj):
        self.selected_level = level_obj
        self.level_title.configure(text=f"MISSION {level_obj.level}")
        self.ssh_display.configure(text=level_obj.get_ssh_command())
        self.pass_input.delete(0, "end")
        self.pass_input.insert(0, level_obj.password)

    def save_progress(self):
        if self.selected_level:
            self.selected_level.password = self.pass_input.get()
            self.db.save_level(self.selected_level)
            self.show_status("DATA ENCRYPTED")

    def copy_ssh(self):
        if self.selected_level:
            pyperclip.copy(self.selected_level.get_ssh_command())
            self.show_status("SSH STRING COPIED")

    def copy_pass(self):
        if self.selected_level:
            pyperclip.copy(self.pass_input.get())
            self.show_status("PASSCODE COPIED")

    def delete_level(self):
        if self.selected_level:
            self.db.delete_level(self.selected_level.level)
            self.refresh_list()
            self.level_title.configure(text="System Idle...")
            self.ssh_display.configure(text="Waiting for mission selection...")
            self.pass_input.delete(0, "end")
            self.show_status("MISSION PURGED")

    def create_next(self):
        levels = self.db.get_all_levels()
        next_num = (levels[-1].level + 1) if levels else 0
        new_lvl = BanditLevel(lvl=next_num, password="")
        self.db.save_level(new_lvl)
        self.refresh_list()
        self.load_details(new_lvl)
        self.show_status(f"DEPLOYING MISSION {next_num}")