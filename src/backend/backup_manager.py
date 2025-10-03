#!/usr/bin/env python3
"""
Backup Manager for RenExtract v2
Standalone backup management system
"""
import os
import shutil
import datetime
import json
from typing import List, Dict, Optional
from pathlib import Path

class BackupType:
    """Énumération des types de sauvegarde"""
    SECURITY = "security"
    CLEANUP = "cleanup"
    RPA_BUILD = "rpa_build"
    REALTIME_EDIT = "realtime_edit"

class BackupManager:
    """Gestionnaire de sauvegardes pour RenExtract v2"""
    
    BACKUP_DESCRIPTIONS = {
        BackupType.SECURITY: "🛡️ Sécurité",
        BackupType.CLEANUP: "🧹 Nettoyage",
        BackupType.RPA_BUILD: "📦 Avant RPA",
        BackupType.REALTIME_EDIT: "⚡ Édition temps réel"
    }
    
    # Configuration de rotation par type
    ROTATION_CONFIG = {
        BackupType.REALTIME_EDIT: 10,  # Max 10 fichiers pour editing
        # Autres types: pas de rotation (None)
    }
    
    def __init__(self, base_dir: str = None):
        """Initialise le gestionnaire de sauvegardes"""
        if base_dir is None:
            # Déterminer le répertoire de base de l'application
            import sys
            if getattr(sys, 'frozen', False):
                # Mode exécutable (build)
                base_dir = os.path.dirname(sys.executable)
            else:
                # Mode développement - remonter de src/backend/ vers la racine
                current_file = os.path.abspath(__file__)
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        
        self.base_dir = base_dir
        self.backup_root = os.path.join(base_dir, "03_Backups")
        self.metadata_file = os.path.join(self.backup_root, "backup_metadata.json")
        
        # Debug: afficher les chemins
        print(f"DEBUG BackupManager: base_dir = {self.base_dir}")
        print(f"DEBUG BackupManager: backup_root = {self.backup_root}")
        print(f"DEBUG BackupManager: metadata_file = {self.metadata_file}")
        
        # Créer le dossier de backup s'il n'existe pas
        os.makedirs(self.backup_root, exist_ok=True)
        
        self._load_metadata()
    
    def _normalize_path(self, path: str) -> str:
        """Normalise un chemin pour qu'il soit accessible sur le système actuel"""
        if not path:
            return path
        
        # Convertir les chemins WSL Windows vers Linux
        if path.startswith('\\\\wsl.localhost\\'):
            # \\wsl.localhost\Arch\home\rory\projets\... -> /home/rory/projets/...
            path = path.replace('\\\\wsl.localhost\\Arch\\', '/')
            path = path.replace('\\', '/')
        
        # Convertir les chemins Windows vers format Unix
        if '\\' in path and not path.startswith('/'):
            path = path.replace('\\', '/')
        
        return path

    def _load_metadata(self):
        """Charge les métadonnées des sauvegardes"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    raw_metadata = json.load(f)
                
                # Normaliser les chemins dans les métadonnées
                self.metadata = {}
                for backup_id, backup_info in raw_metadata.items():
                    normalized_info = backup_info.copy()
                    if 'backup_path' in normalized_info:
                        normalized_info['backup_path'] = self._normalize_path(normalized_info['backup_path'])
                    if 'source_path' in normalized_info:
                        normalized_info['source_path'] = self._normalize_path(normalized_info['source_path'])
                    self.metadata[backup_id] = normalized_info
            else:
                self.metadata = {}
        except Exception as e:
            print(f"Erreur chargement métadonnées backups: {e}")
            self.metadata = {}
    
    def _save_metadata(self):
        """Sauvegarde les métadonnées"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde métadonnées backups: {e}")
    
    def _extract_game_name(self, filepath: str) -> str:
        """Extrait le nom du jeu à partir du chemin du fichier"""
        try:
            if not filepath:
                return "Projet_Inconnu"
            
            if filepath.startswith("clipboard_"):
                parts = filepath.split("_")
                return f"Clipboard_{parts[2].replace('.rpy', '')}" if len(parts) >= 3 else "Projet_Clipboard"
            
            normalized_path = filepath.replace('\\', '/')
            path_parts = [part for part in normalized_path.split('/') if part]
            
            # Chercher le dossier "game" dans le chemin
            game_indices = [i for i, part in enumerate(path_parts) if part.lower() == 'game']
            for game_index in reversed(game_indices):
                if game_index > 0:
                    game_name = path_parts[game_index - 1]
                    return game_name
            
            # Fallback: utiliser le dossier parent
            if len(path_parts) > 1:
                parent_folder = path_parts[-2]
                if ":" not in parent_folder:
                    return parent_folder
            
            return "Projet_Inconnu"
        except Exception as e:
            print(f"Erreur extraction nom de jeu pour {filepath}: {e}")
            return "Projet_Inconnu"
    
    def create_backup(self, source_path: str, backup_type: str = BackupType.SECURITY,
                    description: str = None) -> Dict[str, any]:
        """Crée une sauvegarde avec la structure hiérarchique"""
        result = {
            'success': False,
            'backup_path': None,
            'backup_id': None,
            'error': None
        }
    
        try:
            if not source_path or not os.path.exists(source_path):
                result['error'] = "Fichier source introuvable"
                return result
        
            if backup_type not in self.BACKUP_DESCRIPTIONS:
                backup_type = BackupType.SECURITY
        
            # Gestion des fichiers virtuels
            if source_path.startswith("clipboard_") and not os.path.exists(source_path):
                result['success'] = True
                result['error'] = None
                result['virtual_file'] = True
                result['message'] = "Fichier virtuel - pas de sauvegarde nécessaire"
                return result
        
            # Extraire le nom du jeu et du fichier
            game_name = self._extract_game_name(source_path)
            file_name = Path(source_path).stem  # Nom sans extension
            
            # Créer la structure hiérarchique: Game_name/file_name/backup_type/
            backup_folder = os.path.join(self.backup_root, game_name, file_name, backup_type)
            os.makedirs(backup_folder, exist_ok=True)
        
            timestamp = datetime.datetime.now()
            timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
            
            # Nom du fichier de sauvegarde (garder l'extension originale)
            original_ext = Path(source_path).suffix
            backup_filename = f"{file_name}_{timestamp_str}{original_ext}"
            backup_path = os.path.join(backup_folder, backup_filename)
        
            # Copier le fichier
            shutil.copy2(source_path, backup_path)
        
            # Appliquer la rotation si nécessaire
            if backup_type in self.ROTATION_CONFIG:
                self._apply_rotation(backup_folder, backup_type)
        
            # Créer les métadonnées
            backup_id = f"{game_name}_{file_name}_{timestamp_str}_{backup_type}"
        
            backup_metadata = {
                'id': backup_id,
                'source_path': source_path,
                'backup_path': backup_path,
                'game_name': game_name,
                'file_name': file_name,
                'type': backup_type,
                'created': timestamp.isoformat(),
                'size': os.path.getsize(backup_path),
                'description': description or f"Sauvegarde {self.BACKUP_DESCRIPTIONS[backup_type]}",
                'source_filename': os.path.basename(source_path),
                'backup_filename': backup_filename
            }
        
            self.metadata[backup_id] = backup_metadata
            self._save_metadata()
        
            result['success'] = True
            result['backup_path'] = backup_path
            result['backup_id'] = backup_id
        
            print(f"Backup créé: {game_name}/{file_name}/{backup_type}/{backup_filename}")
        
        except Exception as e:
            result['error'] = str(e)
            print(f"Erreur création backup: {e}")
    
        return result
    
    def _apply_rotation(self, backup_folder: str, backup_type: str):
        """Applique la rotation des fichiers pour un type donné"""
        try:
            max_files = self.ROTATION_CONFIG.get(backup_type)
            if max_files is None:
                return  # Pas de rotation pour ce type
            
            # Lister tous les fichiers de sauvegarde dans ce dossier
            backup_files = []
            for file in os.listdir(backup_folder):
                file_path = os.path.join(backup_folder, file)
                if os.path.isfile(file_path):
                    backup_files.append({
                        'path': file_path,
                        'name': file,
                        'mtime': os.path.getmtime(file_path)
                    })
            
            # Trier par date de modification (plus ancien en premier)
            backup_files.sort(key=lambda x: x['mtime'])
            
            # Supprimer les fichiers excédentaires
            while len(backup_files) >= max_files:
                oldest_file = backup_files.pop(0)
                try:
                    os.remove(oldest_file['path'])
                    print(f"Rotation: suppression de {oldest_file['name']}")
                    
                    # Supprimer des métadonnées si présent
                    self._remove_from_metadata(oldest_file['path'])
                    
                except Exception as e:
                    print(f"Erreur suppression rotation {oldest_file['name']}: {e}")
            
            if backup_type == BackupType.REALTIME_EDIT:
                print(f"Rotation editing: {len(backup_files) + 1}/{max_files} fichiers")
                
        except Exception as e:
            print(f"Erreur rotation {backup_type}: {e}")
    
    def _remove_from_metadata(self, backup_path: str):
        """Supprime une entrée des métadonnées par chemin"""
        try:
            to_remove = []
            for backup_id, metadata in self.metadata.items():
                if metadata.get('backup_path') == backup_path:
                    to_remove.append(backup_id)
            
            for backup_id in to_remove:
                del self.metadata[backup_id]
                
            if to_remove:
                self._save_metadata()
                
        except Exception as e:
            print(f"Erreur suppression métadonnées: {e}")
    
    def list_all_backups(self, game_filter: str = None, type_filter: str = None) -> List[Dict]:
        """Liste toutes les sauvegardes avec la structure hiérarchique"""
        backups = []
        
        try:
            if not os.path.exists(self.backup_root):
                return backups
            
            # Scanner la structure hiérarchique: Game_name/file_name/backup_type/
            for game_name in os.listdir(self.backup_root):
                if game_filter and game_filter != "Tous" and game_name != game_filter:
                    continue
                    
                game_path = os.path.join(self.backup_root, game_name)
                if not os.path.isdir(game_path) or game_name.startswith('.'):
                    continue
                
                # Parcourir les fichiers
                for file_name in os.listdir(game_path):
                    file_path = os.path.join(game_path, file_name)
                    if not os.path.isdir(file_path):
                        continue
                    
                    # Parcourir les types de backup
                    for backup_type in os.listdir(file_path):
                        if type_filter and backup_type != type_filter:
                            continue
                            
                        type_path = os.path.join(file_path, backup_type)
                        if not os.path.isdir(type_path):
                            continue
                        
                        # Scanner les fichiers de sauvegarde
                        for backup_file in os.listdir(type_path):
                            backup_full_path = os.path.join(type_path, backup_file)
                            if not os.path.isfile(backup_full_path):
                                continue
                            
                            backup_info = self._get_or_create_backup_info_hierarchical(
                                backup_full_path, game_name, file_name, backup_type
                            )
                            if backup_info:
                                backups.append(backup_info)
            
            # Trier par date de création (plus récent en premier)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            print(f"Erreur listage backups hiérarchiques: {e}")
        
        return backups
    
    def _get_or_create_backup_info_hierarchical(self, backup_path: str, game_name: str, 
                                              file_name: str, backup_type: str) -> Optional[Dict]:
        """Crée les infos de backup pour la structure hiérarchique"""
        try:
            backup_filename = os.path.basename(backup_path)
            
            # Chercher dans les métadonnées existantes
            for backup_id, metadata in self.metadata.items():
                if metadata.get('backup_path') == backup_path:
                    return metadata
            
            # Créer de nouvelles métadonnées
            stats = os.stat(backup_path)
            created_time = datetime.datetime.fromtimestamp(stats.st_ctime)
            backup_id = f"{game_name}_{file_name}_{created_time.strftime('%Y%m%d_%H%M%S')}_{backup_type}"
            
            # Reconstruire le nom de fichier source
            source_filename = self._reconstruct_source_filename(backup_filename, file_name)
            
            backup_info = {
                'id': backup_id,
                'backup_path': backup_path,
                'game_name': game_name,
                'file_name': file_name,
                'type': backup_type,
                'created': created_time.isoformat(),
                'size': stats.st_size,
                'description': f"Sauvegarde {self.BACKUP_DESCRIPTIONS.get(backup_type, backup_type)}",
                'source_filename': source_filename,
                'backup_filename': backup_filename,
                'source_path': None  # À reconstruire à la demande
            }
            
            # Sauvegarder dans les métadonnées
            self.metadata[backup_id] = backup_info
            return backup_info
            
        except Exception as e:
            print(f"Erreur création info backup hiérarchique {backup_path}: {e}")
            return None
    
    def _reconstruct_source_filename(self, backup_filename: str, file_name: str) -> str:
        """Reconstruit le nom de fichier source à partir du backup"""
        try:
            # Format: file_name_YYYYMMDD_HHMMSS.ext
            # Extraire l'extension
            backup_ext = Path(backup_filename).suffix
            
            # Le nom source est généralement le nom du fichier + extension
            if backup_ext:
                return f"{file_name}{backup_ext}"
            else:
                return f"{file_name}.rpy"  # Extension par défaut
                
        except Exception as e:
            print(f"Erreur reconstruction nom source: {e}")
            return f"{file_name}.rpy"
    
    def cleanup_empty_folders(self):
        """Nettoie les dossiers vides dans la structure hiérarchique"""
        try:
            cleaned_count = 0
            
            # Parcourir tous les jeux
            for game_name in os.listdir(self.backup_root):
                game_path = os.path.join(self.backup_root, game_name)
                if not os.path.isdir(game_path):
                    continue
                
                # Parcourir tous les fichiers
                for file_name in os.listdir(game_path):
                    file_path = os.path.join(game_path, file_name)
                    if not os.path.isdir(file_path):
                        continue
                    
                    # Parcourir tous les types
                    for backup_type in os.listdir(file_path):
                        type_path = os.path.join(file_path, backup_type)
                        if os.path.isdir(type_path) and not os.listdir(type_path):
                            os.rmdir(type_path)
                            cleaned_count += 1
                            print(f"Dossier vide supprimé: {game_name}/{file_name}/{backup_type}")
                    
                    # Supprimer le dossier fichier s'il est vide
                    if os.path.isdir(file_path) and not os.listdir(file_path):
                        os.rmdir(file_path)
                        cleaned_count += 1
                        print(f"Dossier fichier vide supprimé: {game_name}/{file_name}")
                
                # Supprimer le dossier jeu s'il est vide
                if os.path.isdir(game_path) and not os.listdir(game_path):
                    os.rmdir(game_path)
                    cleaned_count += 1
                    print(f"Dossier jeu vide supprimé: {game_name}")
            
            if cleaned_count > 0:
                print(f"Nettoyage: {cleaned_count} dossiers vides supprimés")
            
            return cleaned_count
            
        except Exception as e:
            print(f"Erreur nettoyage dossiers vides: {e}")
            return 0
