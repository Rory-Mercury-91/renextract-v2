# 📦 Implémentation Complète du Système d'Extraction

> **Documentation de l'implémentation du système d'extraction des textes Ren'Py**  
> Basé sur le flux `FLUX_02_EXTRACTION.md`

---

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Fonctionnalités Implémentées](#fonctionnalités-implémentées)
4. [Intégrations](#intégrations)
5. [Guide de Test](#guide-de-test)
6. [Corrections Appliquées](#corrections-appliquées)

---

## 🎯 Vue d'ensemble

Le système d'extraction est **100% opérationnel** et respecte fidèlement le flux documenté. Il permet d'extraire les textes des fichiers Ren'Py avec protection des codes, gestion des doublons, et génération de fichiers de traduction.

### ✅ Fichiers Générés
```
01_Temporary/
└── <NomDuJeu>/
    └── <nom_fichier>/
        ├── fichiers_a_traduire/
        │   ├── <nom>_dialogue.txt       # Dialogues principaux
        │   ├── <nom>_doublons.txt       # Doublons détectés
        │   └── <nom>_asterix.txt        # Astérisques/tildes
        └── fichiers_a_referencer/
            └── <nom>_positions.json     # Métadonnées reconstruction
```

### 🎯 Workflow Utilisateur
```
1. Charger un projet Ren'Py (header)
2. Sélectionner un fichier .rpy (onglet Extraction)
3. Cliquer "Extraire"
4. Observer la progression
5. Fichiers générés + ouverture automatique (si activée)
```

---

## 🏗️ Architecture

### 📦 Backend (`src/backend/extraction.py`)

#### **Classes Principales**
```python
class PlaceholderGenerator:
    """Génération de placeholders de protection"""
    
class DuplicateManager:
    """Gestion des doublons"""
    
class TextExtractor:
    """Classe principale d'extraction"""
    - _build_code_mapping()              # Protection codes
    - _apply_empty_text_protection()     # Protection vides
    - _build_asterix_mapping_with_stack() # Protection astérisques
    - _build_tilde_mapping_two_pass()     # Protection tildes
    - _extract_dialogue_and_handle_duplicates() # Extraction
    - _save_extraction_files()            # Sauvegarde
```

### 🌐 API REST (`app.py`)

#### **Endpoints d'Extraction**
- `POST /api/extraction/extract` - Extraction principale
- `POST /api/extraction/validate-file` - Validation fichier
- `POST /api/extraction/open-file` - Ouvrir fichier
- `POST /api/extraction/open-folder` - Ouvrir dossier
- `GET /api/extraction/get-settings` - Paramètres
- `POST /api/extraction/set-settings` - Configuration

#### **Endpoint Backup**
- `POST /api/backups/create` - Créer sauvegarde

### 🎨 Frontend

#### **Store Réactif** (`src/stores/extraction.ts`)
```typescript
// État de l'extraction
extractionStore: {
  isExtracting: boolean
  extractionProgress: string
  lastResult: ExtractionResult | null
  lastError: string | null
  settings: ExtractionSettings
}

// Actions
extractionActions.extractTexts()
extractionActions.openExtractionFiles()
extractionActions.openOutputFolder()
```

#### **Composant UI** (`src/components/ActionButtons.svelte`)
- Bouton "Extraire" connecté
- Indicateurs de progression
- Résultats visuels
- Gestion d'erreurs

---

## ⚙️ Fonctionnalités Implémentées

### 1️⃣ **Protection des Codes Ren'Py**
```python
# Protège les codes pour qu'ils ne soient pas traduits
Patterns protégés:
- Variables: [player_name], [score]
- Formatage: %s, %d, %(name)s
- Échappements: \n, \t, \r, \\, \"
- Balises HTML: <b>, <i>, <color=#xxx>
- Balises accolades: {color=#xxx}, {size=24}
- Codes spéciaux: {w}, {nw}, {p}, {fast}
```

### 2️⃣ **Protection des Textes Vides**
```python
# Protège les chaînes vides "" pour préserver la structure
"" → RENPY_EMPTY_001
```

### 3️⃣ **Protection des Astérisques**
```python
# Protège les textes en italique
* "Texte en italique" → * RENPY_ASTERISK_001
```

### 4️⃣ **Protection des Tildes**
```python
# Protège les textes barrés
~ "Texte barré" → ~ RENPY_TILDE_001
```

### 5️⃣ **Extraction des Dialogues**
- Extraction avec/sans gestion des doublons
- Préservation de la structure
- Métadonnées pour reconstruction

### 6️⃣ **Gestion des Doublons**
```python
# Détection et séparation des textes dupliqués
if detect_duplicates:
    - Textes uniques → _dialogue.txt
    - Doublons → _doublons.txt
else:
    - Tous les textes → _dialogue.txt
```

---

## 🔗 Intégrations

### 🛡️ **Backup Automatique**

#### **Flux d'Exécution**
```
1. Initialisation
2. 🛡️ SAUVEGARDE DE SÉCURITÉ (backup avant extraction)
   └─> Type: 'security'
   └─> Description: "Sauvegarde avant extraction"
   └─> Dossier: 03_Backups/<Game>/<file>/security/
3. Protection des codes
4. Extraction
5. Génération fichiers
6. Ouverture automatique (si activée)
```

#### **Comportement**
- ✅ Backup réussi : Continue l'extraction
- ⚠️ Backup échoué : Warning dans console + Continue quand même

#### **Structure Backup**
```
03_Backups/
└── <GameName>/
    └── <file_name>/
        └── security/
            ├── <file>_20250108_143052.rpy
            └── backup_metadata.json
```

### 🚀 **Ouverture Automatique des Fichiers**

#### **Paramètre Utilisateur**
```typescript
// Settings → Ouvertures automatiques → Ouverture automatique des fichiers
Settings.autoOpenings.files: boolean
```

#### **Flux d'Ouverture**
```typescript
// Après extraction réussie
if (settings.autoOpenings.files) {
  // Ouvre tous les fichiers générés
  - <file>_dialogue.txt
  - <file>_doublons.txt (si présent)
  - <file>_asterix.txt (si présent)
  
  // Délai de 150ms entre chaque ouverture
}
```

#### **Support Multiplateforme**
- **Windows** : `os.startfile(filepath)`
- **macOS** : `subprocess.call(['open', filepath])`
- **Linux** : `subprocess.call(['xdg-open', filepath])`

### 🔄 **Connexion au Projet Global**

- ✅ Utilise le projet chargé dans le header
- ✅ Synchronisation avec `projectStore`
- ✅ Fichier sélectionné → Extraction disponible
- ✅ Bouton actif seulement si fichier chargé

---

## 🧪 Guide de Test

### Test 1 : Extraction Standard
```
1. Charger un projet Ren'Py
2. Sélectionner un fichier .rpy avec dialogues
3. Cliquer "Extraire"
4. Vérifier progression :
   - "Initialisation..."
   - "Création de la sauvegarde de sécurité..."
   - "Protection des codes et variables..."
5. Vérifier création fichiers dans 01_Temporary/
6. Vérifier ouverture automatique (si activée)
```

### Test 2 : Backup de Sécurité
```
1. Extraire un fichier
2. Aller dans l'onglet "Backups"
3. Vérifier présence du backup de type "🛡️ Sécurité"
4. Vérifier description "Sauvegarde avant extraction"
5. Vérifier métadonnées JSON
```

### Test 3 : Ouverture Automatique
```
1. Aller dans Settings
2. Activer "Ouverture automatique des fichiers"
3. Extraire un fichier
4. Vérifier que les fichiers s'ouvrent automatiquement

5. Désactiver l'option
6. Extraire un nouveau fichier
7. Vérifier que les fichiers ne s'ouvrent PAS
```

### Test 4 : Gestion des Doublons
```
1. Charger un fichier avec textes dupliqués
2. Vérifier que detect_duplicates = true
3. Extraire
4. Vérifier création de _doublons.txt
5. Vérifier séparation dialogues/doublons
```

### Test 5 : Protection des Codes
```
1. Charger un fichier avec [variables], {tags}, etc.
2. Extraire
3. Ouvrir _positions.json
4. Vérifier présence des mappings de protection :
   - mapping: codes protégés
   - asterix_mapping: astérisques
   - tilde_mapping: tildes
   - empty_mapping: textes vides
```

---

## 🔧 Corrections Appliquées

### ✅ **Correction du Dossier d'Extraction**

#### **Problème**
Le système créait `01_Temporaires/` au lieu d'utiliser `01_Temporary/`

#### **Solution**
```python
# src/backend/extraction.py - Ligne 198
# AVANT
temp_dir = "01_Temporaires"  # ❌

# APRÈS
temp_dir = "01_Temporary"    # ✅
```

#### **Cohérence**
```
01_Temporary/   ← Extraction
02_Reports/     ← Rapports
03_Backups/     ← Sauvegardes
04_Configs/     ← Configuration
```

---

## 📊 Statistiques et Métadonnées

### **Compteurs Affichés**
```typescript
{
  extracted_count: 12,      // Dialogues principaux
  asterix_count: 3,         // Astérisques
  tilde_count: 1,           // Tildes
  empty_count: 2,           // Textes vides
  duplicate_count: 4        // Doublons
}
```

### **Fichier _positions.json**
```json
{
  "line_to_content_indices": {
    "42": [0, 1],
    "108": [2]
  },
  "original_lines": {
    "42": "    mc \"Texte1\" \"Texte2\"",
    "108": "    narrator \"Texte3\""
  },
  "all_contents_linear": [
    "Texte1",
    "Texte2",
    "Texte3"
  ],
  "mapping": {
    "[player_name]": "RENPY_CODE_001"
  },
  "asterix_mapping": {
    "RENPY_ASTERISK_001": "Texte en italique"
  },
  "tilde_mapping": {
    "RENPY_TILDE_001": "Texte barré"
  },
  "empty_mapping": {
    "RENPY_EMPTY_001": ""
  }
}
```

---

## 🎨 Interface Utilisateur

### **Indicateurs de Progression**
```
🔄 Extraction en cours...
   1. Initialisation de l'extraction...
   2. Création de la sauvegarde de sécurité...
   3. Protection des codes et variables...
```

### **Résultat Succès**
```
✅ Extraction terminée
   12 dialogues • 3 astérisques • 2 doublons
   [📂 Ouvrir dossier]
```

### **Résultat Erreur**
```
❌ Erreur d'extraction
   <Message d'erreur détaillé>
```

### **États du Bouton "Extraire"**
- 🟢 **Actif** : Fichier chargé, prêt à extraire
- 🔴 **Inactif** : Aucun fichier chargé  
- ⏸️ **Désactivé** : Extraction en cours

---

## 🔍 Logs Console (Debug)

### **Extraction Complète**
```javascript
🚀 Lancement de l'extraction { file: '...', lines: 1234 }
✅ Sauvegarde créée: /path/to/backup/file.rpy
📤 Début de l'extraction
✅ Extraction réussie: { extracted_count: 12, ... }
📂 Ouverture automatique des fichiers: [...]
```

### **Backup Échoué (Warning)**
```javascript
⚠️ Sauvegarde échouée: <raison>
📤 Début de l'extraction (continue quand même)
✅ Extraction réussie
```

---

## 📁 Fichiers Créés/Modifiés

### **✨ Nouveaux Fichiers**
- `src/backend/extraction.py` - Backend extraction complet
- `src/stores/extraction.ts` - Store réactif extraction
- `IMPLEMENTATION_EXTRACTION.md` - Cette documentation

### **🔄 Fichiers Modifiés**

#### **Backend**
- `app.py` - 7 nouveaux endpoints (6 extraction + 1 backup)

#### **Frontend**
- `src/lib/api.ts` - 7 nouvelles fonctions API
- `src/components/ActionButtons.svelte` - Bouton connecté + UI
- `src/stores/project.ts` - Synchronisation avec extraction

#### **Configuration**
- `tsconfig.json` - Alias `$stores`
- `vite.config.ts` - Alias `$stores`

---

## 🎉 Récapitulatif Final

### ✅ **Conformité au Flux**
- ✅ **ÉTAPE 1** : Validation initiale
- ✅ **ÉTAPE 2** : Sauvegarde de sécurité
- ✅ **ÉTAPE 3** : Initialisation extracteur
- ✅ **ÉTAPE 4** : Protection des codes
- ✅ **ÉTAPE 5** : Extraction dialogues
- ✅ **ÉTAPE 6** : Sauvegarde fichiers
- ✅ **POST** : Ouverture automatique

### ✅ **Fonctionnalités**
- ✅ Protection complète des codes Ren'Py
- ✅ Gestion des doublons
- ✅ Backup automatique avant extraction
- ✅ Ouverture automatique configurable
- ✅ Génération fichiers de traduction
- ✅ Métadonnées pour reconstruction
- ✅ Support multiplateforme
- ✅ Dossier correct (01_Temporary)

### ✅ **Intégrations**
- ✅ Système de backup
- ✅ Paramètres utilisateur
- ✅ Projet global (header)
- ✅ Architecture de l'application

---

## 🔜 Prochaines Étapes

Le système d'extraction est **100% opérationnel** et prêt pour :

1. **FLUX_03 : Reconstruction** 🔨
   - Reconstruire les fichiers traduits
   - Restaurer les codes protégés
   - Valider la cohérence

2. **FLUX_04 : Vérification** 🔍
   - Vérifier la cohérence des traductions
   - Détecter les erreurs de syntaxe
   - Générer des rapports

**Le système d'extraction est complet et fonctionnel !** 🚀
