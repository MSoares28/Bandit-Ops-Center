import sqlite3
import os
import customtkinter as ctk
import pyperclip
from tkinter import messagebox

# --- BanditLevel & DatabaseManager permanecem iguais ---
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
        self.seed_level_zero()
            
    def create_table(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS levels (
                lvl INTEGER PRIMARY KEY,
                password TEXT
            )
        """)
        self.connection.commit()

    def seed_level_zero(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM levels")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO levels (lvl, password) VALUES (0, 'bandit0')")
            self.connection.commit()

    def save_level(self, level_obj):
        cursor = self.connection.cursor()
        query = "INSERT OR REPLACE INTO levels (lvl, password) VALUES (?, ?)"
        cursor.execute(query, (level_obj.level, level_obj.password))
        self.connection.commit()

    def delete_level(self, lvl):
        if lvl == 0: return False
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM levels WHERE lvl = ?", (lvl,))
        self.connection.commit()
        return True

    def get_all_levels(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT lvl, password FROM levels ORDER BY lvl ASC")
        rows = cursor.fetchall()
        return [BanditLevel(lvl=row[0], password=row[1]) for row in rows]

# --- BanditApp Reformulado ---
class BanditApp:
    def __init__(self, root, db_manager):
        self.root = root
        self.db = db_manager
        self.selected_level = None
        self.ssh_text_color = ("#2D7D46", "#00FF00")

        self.root.title("Bandit Ops Center v2.4")
        self.root.geometry("1000x650")

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.setup_ui()
        self.refresh_list()
        
        levels = self.db.get_all_levels()
        if levels: self.load_details(levels[0])

    def setup_ui(self):
        # --- SIDEBAR (Limpa) ---
        self.sidebar_frame = ctk.CTkFrame(self.root, width=240, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.sidebar_frame, text="BANDIT OPS", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=30)

        self.level_list = ctk.CTkScrollableFrame(self.sidebar_frame, label_text="MISSIONS")
        self.level_list.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")

        # --- MAIN DASHBOARD ---
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.grid(row=0, column=1, padx=30, pady=30, sticky="nsew")

        self.level_title = ctk.CTkLabel(self.main_container, text="Mission Control", font=ctk.CTkFont(size=28, weight="bold"))
        self.level_title.pack(pady=(0, 20))

        # SSH CARD
        self.ssh_card = ctk.CTkFrame(self.main_container, corner_radius=15)
        self.ssh_card.pack(fill="x", pady=10, ipady=15)
        self.ssh_display = ctk.CTkLabel(self.ssh_card, text="---", font=("Consolas", 18), text_color=self.ssh_text_color)
        self.ssh_display.pack(pady=10)
        ctk.CTkButton(self.ssh_card, text="COPY SSH COMMAND", command=self.copy_ssh).pack()

        # PASSWORD CARD (Onde a mágica acontece)
        self.creds_card = ctk.CTkFrame(self.main_container, corner_radius=15)
        self.creds_card.pack(fill="x", pady=10, ipady=15)

        self.pass_input = ctk.CTkEntry(self.creds_card, placeholder_text="Paste password here...", 
                                        height=45, font=("Consolas", 16), justify="center")
        self.pass_input.pack(fill="x", padx=60, pady=15)

        # Centralized action buttons
        self.actions_frame = ctk.CTkFrame(self.creds_card, fg_color="transparent")
        self.actions_frame.pack(pady=10)

        self.btn_save = ctk.CTkButton(self.actions_frame, text="SAVE", fg_color="#2d7d46", command=self.save_progress)
        self.btn_save.grid(row=0, column=0, padx=5)

        self.btn_edit = ctk.CTkButton(self.actions_frame, text="EDIT", fg_color="#5a5a5a", command=self.enable_edit)
        self.btn_edit.grid(row=0, column=1, padx=5)

        self.btn_pass_copy = ctk.CTkButton(self.actions_frame, text="COPY PASS", command=self.copy_pass)
        self.btn_pass_copy.grid(row=0, column=2, padx=5)

        self.btn_delete = ctk.CTkButton(self.actions_frame, text="DELETE", fg_color="#942a2a", command=self.delete_level)
        self.btn_delete.grid(row=0, column=3, padx=5)

        # Progress buttons
        self.btn_add_next = ctk.CTkButton(self.main_container, text="LOCKED: SAVE PASSWORD", 
                                          height=60, font=ctk.CTkFont(size=18, weight="bold"),
                                          state="disabled", fg_color="gray",
                                          command=self.create_next)
        self.btn_add_next.pack(fill="x", padx=40, pady=30)

        # Toast Notification Label
        self.toast_label = ctk.CTkLabel(self.main_container, text="", 
                                         font=ctk.CTkFont(size=12, slant="italic"),
                                         text_color=self.ssh_text_color)
        self.toast_label.pack(pady=5)

    def enable_edit(self):
        """Libera a caixa de texto para edição"""
        self.pass_input.configure(state="normal")
        self.btn_save.configure(state="normal")
        self.pass_input.focus()

    def check_progression(self):
        levels = self.db.get_all_levels()
        if not levels: return
        last_lvl = levels[-1]
        
        if last_lvl.level >= 33:
            self.btn_add_next.configure(text="ALL MISSIONS DEPLOYED", state="disabled", fg_color="#1a1a1a")
            return

        if last_lvl.password and last_lvl.password.strip() != "" and last_lvl.password != "bandit0":
             # Se for o level 0, a senha já vem preenchida, mas queremos que o usuário jogue.
             # Para o Level 0 especificamente, vamos liberar se ele estiver selecionado ou já salvo.
             pass 

        # Lógica simplificada: se o último nível tem algo escrito, libera o próximo
        if last_lvl.password and len(last_lvl.password.strip()) > 5: # Senhas do Bandit são longas
            self.btn_add_next.configure(text=f"UNLOCK MISSION {last_lvl.level + 1} ➔", state="normal", fg_color="#2d7d46")
        else:
            self.btn_add_next.configure(text="LOCKED: SAVE CURRENT PASSWORD", state="disabled", fg_color="gray")

    def refresh_list(self):
        for widget in self.level_list.winfo_children():
            widget.destroy()
        for lvl in self.db.get_all_levels():
            btn = ctk.CTkButton(self.level_list, text=f"Mission {lvl.level}", 
                                fg_color="transparent", border_width=1,
                                command=lambda obj=lvl: self.load_details(obj))
            btn.pack(fill="x", pady=2)
        self.check_progression()

    def load_details(self, level_obj):
        self.selected_level = level_obj
        self.level_title.configure(text=f"BANDIT MISSION {level_obj.level}")
        self.ssh_display.configure(text=level_obj.get_ssh_command())
        
        # Limpa e carrega a senha
        self.pass_input.configure(state="normal")
        self.pass_input.delete(0, "end")
        self.pass_input.insert(0, level_obj.password)
        
        # Lock input if a password already exists
        if level_obj.password and level_obj.password.strip() != "":
            self.pass_input.configure(state="disabled")
            self.btn_save.configure(state="disabled")
        else:
            self.pass_input.configure(state="normal")
            self.btn_save.configure(state="normal")

        # Trava Delete no Level 0
        state = "disabled" if level_obj.level == 0 else "normal"
        color = "gray" if level_obj.level == 0 else "#942a2a"
        self.btn_delete.configure(state=state, fg_color=color)

    def save_progress(self):
        if self.selected_level:
            new_pass = self.pass_input.get()
            if new_pass.strip() == "":
                messagebox.showwarning("Warning", "Password cannot be empty!")
                return
                
            self.selected_level.password = new_pass
            self.db.save_level(self.selected_level)
            
            # Lock UI after successful save
            self.pass_input.configure(state="disabled")
            self.btn_save.configure(state="disabled")
            self.show_toast("Progress secured and locked!")
            self.check_progression()

    def create_next(self):
        levels = self.db.get_all_levels()
        if not levels: return
        last_lvl = levels[-1]
        new_num = last_lvl.level + 1
        
        if new_num <= 33:
            new_lvl = BanditLevel(lvl=new_num, password="")
            self.db.save_level(new_lvl)
            self.refresh_list()
            self.load_details(new_lvl)

    def delete_level(self):
        if self.selected_level and self.selected_level.level != 0:
            self.db.delete_level(self.selected_level.level)
            self.refresh_list()
            levels = self.db.get_all_levels()
            self.load_details(levels[-1])

    def copy_ssh(self):
        if self.selected_level:
            pyperclip.copy(self.selected_level.get_ssh_command())
            self.show_toast("SSH command copied!")

    def copy_pass(self):
        if self.selected_level:
            # Copy directly from the object to ensure data integrity
            pyperclip.copy(self.selected_level.password)
            self.show_toast("Password copied to clipboard!")

    def show_toast(self, message):
        """Displays a temporary feedback message on screen"""
        self.toast_label.configure(text=f"✔ {message}")
        # Clear the message after 2 seconds
        self.root.after(2000, lambda: self.toast_label.configure(text=""))

    def enable_edit(self):
        """Unlocks the password field for manual changes"""
        self.pass_input.configure(state="normal")
        self.btn_save.configure(state="normal")
        self.pass_input.focus()        