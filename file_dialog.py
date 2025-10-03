"""
Script pour ouvrir des dialogues Windows natifs depuis l'application web.
"""
import sys
import os

def open_folder_dialog():
    """Ouvre un dialogue pour sélectionner un dossier."""
    try:
        if sys.platform == "win32":
            import tkinter as tk
            from tkinter import filedialog
            
            # Main window invisible
            root = tk.Tk()
            root.withdraw()
            
            # Dialogue dossier
            folder_path = filedialog.askdirectory(
                title="Sélectionner le dossier SDK Ren'Py",
                initialdir="C:\\"
            )
            
            root.destroy()
            return folder_path if folder_path else ""
        else:
            # Fallback pour autres OS
            return ""
    except Exception as e:
        print(f"Erreur dialogue dossier: {e}")
        return ""

def open_file_dialog():
    """Ouvre un dialogue pour sélectionner un fichier exécutable."""
    try:
        if sys.platform == "win32":
            import tkinter as tk
            from tkinter import filedialog
            
            # Main window invisible
            root = tk.Tk()
            root.withdraw()
            
            # Dialogue fichier
            file_path = filedialog.askopenfilename(
                title="Sélectionner un exécutable",
                filetypes=[
                    ("Exécutables", "*.exe"),
                    ("Tous les fichiers", "*.*")
                ],
                initialdir="C:\\Program Files"
            )
            
            root.destroy()
            return file_path if file_path else ""
        else:
            # Fallback pour autres OS
            return ""
    except Exception as e:
        print(f"Erreur dialogue fichier: {e}")
        return ""

if __name__ == "__main__":
    # Test du script
    print("Testing folder dialog...")
    folder = open_folder_dialog()
    print(f"Selected folder: {folder}")
    
    print("\nTesting file dialog...") 
    file = open_file_dialog()
    print(f"Selected file: {file}")
