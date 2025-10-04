"""
Solution hybride pour les dialogues de fichiers
Utilise tkinter quand possible, fallback vers modal web sinon
"""
import subprocess
import tkinter as tk
from tkinter import filedialog


def open_folder_dialog_hybrid():
    """Ouvre un dialogue de sélection de dossier avec tkinter ou fallback."""
    # Méthode 1: Essayer tkinter (fonctionne sur Windows avec interface
    # graphique)
    try:
        # Créer une fenêtre racine cachée
        root = tk.Tk()
        root.withdraw()  # Cacher la fenêtre principale

        # Ouvrir le dialogue de sélection de dossier
        folder_path = filedialog.askdirectory(
            title="Sélectionner le dossier SDK Ren'Py",
            initialdir="C:\\"
        )

        # Nettoyer
        root.destroy()

        if folder_path:
            return folder_path

    except (tk.TclError, OSError) as e:
        print(f"Tkinter folder dialog failed: {e}")

    # Méthode 2: Fallback - ouvrir l'explorateur Windows
    try:
        subprocess.run(["explorer.exe", "C:\\"], timeout=2, check=False)
        print("Explorateur Windows ouvert pour aide visuelle")
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"Explorer fallback failed: {e}")

    # Retourner vide pour déclencher le modal web
    return ""


def open_file_dialog_hybrid():
    """Ouvre un dialogue de sélection de fichier avec tkinter ou fallback."""
    # Méthode 1: Essayer tkinter (fonctionne sur Windows avec interface
    # graphique)
    try:
        # Créer une fenêtre racine cachée
        root = tk.Tk()
        root.withdraw()  # Cacher la fenêtre principale

        # Ouvrir le dialogue de sélection de fichier
        file_path = filedialog.askopenfilename(
            title="Sélectionner un exécutable",
            initialdir="C:\\Program Files",
            filetypes=[
                ("Exécutables", "*.exe"),
                ("Tous les fichiers", "*.*")
            ]
        )

        # Nettoyer
        root.destroy()

        if file_path:
            return file_path

    except (tk.TclError, OSError) as e:
        print(f"Tkinter file dialog failed: {e}")

    # Méthode 2: Fallback - ouvrir l'explorateur Windows
    try:
        subprocess.run(["explorer.exe", "C:\\Program Files"],
                       timeout=2, check=False)
        print("Explorateur Windows ouvert pour aide visuelle")
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"Explorer fallback failed: {e}")

    # Retourner vide pour déclencher le modal web
    return ""


if __name__ == "__main__":
    print("Testing tkinter dialogs...")

    print("\nTesting folder dialog...")
    folder = open_folder_dialog_hybrid()
    print(f"Selected folder: '{folder}'")

    print("\nTesting file dialog...")
    file = open_file_dialog_hybrid()
    print(f"Selected file: '{file}'")
