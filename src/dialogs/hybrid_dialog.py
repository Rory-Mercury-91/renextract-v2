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
    
    # Détecter l'environnement
    is_wsl = False
    try:
        if hasattr(os, 'uname'):
            is_wsl = 'microsoft' in os.uname().release.lower()
        is_wsl = is_wsl or 'WSL_DISTRO_NAME' in os.environ or 'WSLENV' in os.environ
    except:
        is_wsl = False
    
    if is_wsl:
        print("DEBUG: WSL detected, folder dialog not available in WSL")
        # En WSL, on ne peut pas ouvrir de dialogue Windows
        # Retourner un chemin par défaut et afficher un message
        print("INFO: En mode WSL, le dialogue de dossier n'est pas disponible.")
        print("INFO: Utilisation du chemin par défaut: C:\\Users\\Public\\Documents")
        print("INFO: Pour tester avec un autre chemin, modifiez le code ou utilisez Windows natif.")
        return "C:\\Users\\Public\\Documents"
    
    # Méthode 1: PowerShell + System.Windows.Forms (Windows natif seulement)
    try:
        ps_script = """
        Add-Type -AssemblyName System.Windows.Forms
        $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
        $folderBrowser.Description = "Sélectionner le dossier de destination pour la restauration"
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
                print(f"DEBUG: PowerShell folder dialog returned: {output}")
                return output
            else:
                print("DEBUG: PowerShell folder dialog was cancelled")
                return ""
    except Exception as e:
        print(f"PowerShell method failed: {e}")
    
    # Méthode 2: Utiliser Windows native tools directement
    try:
        # Ecrire un script VBS pour utiliser l'explorateur Windows
        vbs_script = """
        Set objShell = CreateObject("Shell.Application")
        objShell.BrowseForFolder 0, "Sélectionner le dossier de destination pour la restauration:", 0, "C:\\"
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
    
    # Méthode 3: Fallback pour test
    print("DEBUG: All methods failed, returning fallback path")
    return "C:\\Users\\Public\\Documents"  # Valeur de test

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
