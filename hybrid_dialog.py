"""
Solution hybride pour les dialogues de fichiers Windows
Combine plusieurs méthodes pour maximalkan compatibility
"""
import subprocess
import json
import sys
import os

def open_folder_dialog_hybrid():
    """Essaie plusieurs méthodes pour ouvrir un dialogue de dossier."""
    
    # Méthode 1: PowerShell + System.Windows.Forms
    try:
        ps_script = """
        Add-Type -AssemblyName System.Windows.Forms
        $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
        $folderBrowser.Description = "Sélectionner le dossier SDK Ren'Py"
        $folderBrowser.SelectedPath = "C:\\"
        
        if ($folderBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            Write-Output $folderBrowser.SelectedPath
        } else {
            Write-Output "CANCELLED"
        }
        """
        
        result = subprocess.run([
            "powershell.exe", "-WindowStyle", "Hidden", "-Command", ps_script
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output and output != "CANCELLED":
                return output
    except Exception as e:
        print(f"PowerShell method failed: {e}")
    
    # Méthode 2: Utiliser Windows native tools directement
    try:
        # Ecrire un script VBS pour utiliser l'explorateur Windows
        vbs_script = """
        Set objShell = CreateObject("Shell.Application")
        objShell.BrowseForFolder 0, "Sélectionner le dossier SDK Ren'Py:", 0, "C:\\"
        """
        
        # Créer fichier temporaire VBS
        with open("temp_folder_dialog.vbs", "w", encoding="utf-8") as f:
            f.write(vbs_script)
        
        result = subprocess.run([
            "wscript.exe", "temp_folder_dialog.vbs"
        ], capture_output=True, timeout=30)
        
        # Cleanup
        if os.path.exists("temp_folder_dialog.vbs"):
            os.remove("temp_folder_dialog.vbs")
            
        return ""  # VBS ne permet pas de récupérer la sélection
    except Exception as e:
        print(f"VBS method failed: {e}")
    
    # Méthode 3: Fallback vers echo pour test
    return "C:\\Program Files"  # Valeur de test

def open_file_dialog_hybrid():
    """Essaie plusieurs méthodes pour ouvrir un dialogue de fichier."""
    
    # Méthode 1: PowerShell + System.Windows.Forms
    try:
        ps_script = """
        Add-Type -AssemblyName System.Windows.Forms
        
        $openFileDialog = New-Object System.Windows.Forms.OpenFileDialog
        $openFileDialog.InitialDirectory = "C:\\Program Files"
        $openFileDialog.Filter = "Exécutables (*.exe)|*.exe|Tous les fichiers (*.*)|*.*"
        $openFileDialog.FilterIndex = 1
        $openFileDialog.Title = "Sélectionner un exécutable"
        
        if ($openFileDialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            Write-Output $openFileDialog.FileName
        } else {
            Write-Output "CANCELLED"
        }
        """
        
        result = subprocess.run([
            "powershell.exe", "-WindowStyle", "Hidden", "-Command", ps_script
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output and output != "CANCELLED":
                return output
    except Exception as e:
        print(f"PowerShell method failed: {e}")
    
    # Fallback temporaire pour test
    return "C:\\Windows\\notepad.exe"  # Valeur de test

if __name__ == "__main__":
    print("Testing hybrid dialogs...")
    
    print("\nTesting folder dialog...")
    folder = open_folder_dialog_hybrid()
    print(f"Selected folder: '{folder}'")
    
    print("\nTesting file dialog...")
    file = open_file_dialog_hybrid()
    print(f"Selected file: '{file}'")
