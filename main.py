import customtkinter as ctk
from models import BanditLevel, DatabaseManager, BanditApp

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Initialize Database
    db = DatabaseManager("bandit_data.db")

    # Seed data if empty (Initial setup)
    if not db.get_all_levels():
        initial_lvl = BanditLevel(0, "bandit0")
        db.save_level(initial_lvl)

    # Initialize GUI
    root = ctk.CTk()
    
    app = BanditApp(root, db)
    root.mainloop()

if __name__ == "__main__":
    main()