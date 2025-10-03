"""
Interface Windows native pour les dialogues de fichiers/dossiers
Utilise PowerShell sous Windows pour ouvrir les dialogues natifs
"""
import subprocess
import json
import sys
import os

def open_folder_dialog_windows():
    """Ouvre le dialogue Windows natif pour sélectionner un dossier."""
    if sys.platform != "win32":
        return ""
    
    try:
        # Script PowerShell pour ouvrir le dialogue Windows
        ps_script = """
        Add-Type -AssemblyName System.Windows.Forms
        $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
        $folderBrowser.Description = "Sélectionner le dossier SDK Ren'Py"
        $folderBrowser.SelectedPath = "C:\\"
        
        if ($folderBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            Write-Output $folderBrowser.SelectedPath
        }
        """
        
        # Exécuter PowerShell
        result = subprocess.run([
            "powershell", "-Command", ps_script
        ], capture_output=True, text=True, cwd="C:\\")
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            return ""
            
    except Exception as e:
        print(f"Erreur PowerShell: {e}")
        return ""

def open_file_dialog_windows():
    """Ouvre le dialogue Windows natif pour sélectionner un fichier."""
    if sys.platform != "win32":
        return ""
    
    try:
        # Script PowerShell pour ouvrir le dialogue de fichier
        ps_script = """
        Add-Type -AssemblyName System.Windows.Forms
        
        $openFileDialog = New-Object System.Windows.Forms.OpenFileDialog
        $openFileDialog.InitialDirectory = "C:\\Program Files"
        $openFileDialog.Filter = "Exécutables (*.exe)|*.exe|Tous les fichiers (*.*)|*.*"
        $openFileDialog.FilterIndex = 1
        $openFileDialog.Title = "Sélectionner un exécutable"
        
        if ($openFileDialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            Write-Output $openFileDialog.FileName
        }
        """
        
        # Exécuter PowerShell
        result = subprocess.run([
            "powershell", "-Command", ps_script
        ], capture_output=True, text=True, cwd="C:\\")
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            return ""
            
    except Exception as e:
        print(f"Erreur PowerShell: {e}")
        return ""

if __name__ == "__main__":
    print("Testing Windows native dialogs...")
    
    print("\nTesting folder dialog...")
    folder = open_folder_dialog_windows()
    print(f"Selected folder: '{folder}'")
    
    print("\nTesting file dialog...")
    file = open_file_dialog_windows()
    print(f"Selected file: '{file}'")
