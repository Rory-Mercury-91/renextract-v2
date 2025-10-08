# 📦 Implémentation Complète - Extraction & Reconstruction

> **Documentation de l'implémentation des systèmes d'extraction et de reconstruction**  
> Basé sur `FLUX_02_EXTRACTION.md` et `FLUX_03_RECONSTRUCTION.md`

---

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Système d'Extraction](#système-dextraction)
4. [Système de Reconstruction](#système-de-reconstruction)
5. [Intégrations](#intégrations)
6. [Guide de Test](#guide-de-test)
7. [Corrections Appliquées](#corrections-appliquées)

---

## 🎯 Vue d'ensemble

Les systèmes d'**extraction** et de **reconstruction** sont **100% opérationnels** et respectent fidèlement les flux documentés. Ils permettent le workflow complet de traduction : extraction des textes → traduction → reconstruction du fichier traduit.

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

### 📦 Backend

#### **Extraction** (`src/backend/extraction.py`)

**Classes Principales**
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

#### **Reconstruction** (`src/backend/reconstruction.py`)

**Classes Principales**
```python
class FileReconstructor:
    """Classe principale de reconstruction"""
    - load_file_content()               # Charge fichier + métadonnées
    - _load_data_for_reconstruction()   # Charge JSON + traductions
    - _load_translation_files()         # Charge .txt multi-fichiers
    - reconstruct_file()                # Reconstruction principale
    - _rebuild_content()                # Reconstruit lignes traduites
    - _replace_all_placeholders()       # Restaure codes/astérisques/tildes
    - _add_reconstruction_marker()      # Ajoute marqueur fin de fichier
```

**Fonctions Utilitaires**
```python
validate_translation_files()          # Validation avant reconstruction
fix_unescaped_quotes_in_txt()        # Correction guillemets automatique
```

### 🌐 API REST (`app.py`)

#### **Endpoints d'Extraction**
- `POST /api/extraction/extract` - Extraction principale
- `POST /api/extraction/validate-file` - Validation fichier
- `POST /api/extraction/open-file` - Ouvrir fichier
- `POST /api/extraction/open-folder` - Ouvrir dossier
- `GET /api/extraction/get-settings` - Paramètres
- `POST /api/extraction/set-settings` - Configuration

#### **Endpoints de Reconstruction**
- `POST /api/reconstruction/validate` - Validation fichiers traduction
- `POST /api/reconstruction/fix-quotes` - Correction guillemets
- `POST /api/reconstruction/reconstruct` - Reconstruction principale

#### **Endpoint Backup**
- `POST /api/backups/create` - Créer sauvegarde

### 🎨 Frontend

#### **Stores Réactifs**

**Extraction** (`src/stores/extraction.ts`)
```typescript
extractionStore: {
  isExtracting: boolean
  extractionProgress: string
  lastResult: ExtractionResult | null
  settings: ExtractionSettings
}

extractionActions.extractTexts()
extractionActions.openExtractionFiles()
extractionActions.openOutputFolder()
```

**Reconstruction** (`src/stores/reconstruction.ts`)
```typescript
reconstructionStore: {
  isReconstructing: boolean
  reconstructionProgress: string
  lastResult: ReconstructionResult | null
  lastValidation: ValidationResult | null
}

reconstructionActions.validateFiles()
reconstructionActions.reconstructFile()
reconstructionActions.openReconstructedFile()
```

#### **Composant UI** (`src/components/ActionButtons.svelte`)
- Bouton "Extraire" connecté avec indicateurs
- Bouton "Reconstruire" connecté avec indicateurs
- Progression en temps réel
- Résultats visuels (vert extraction, émeraude reconstruction)
- Gestion d'erreurs complète

---

## 🔧 Système d'Extraction

### ⚙️ Fonctionnalités Implémentées

#### 1️⃣ **Protection des Codes Ren'Py**
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
- `src/backend/reconstruction.py` - Backend reconstruction complet
- `src/stores/extraction.ts` - Store réactif extraction
- `src/stores/reconstruction.ts` - Store réactif reconstruction
- `IMPLEMENTATION_EXTRACTION.md` - Cette documentation

### **🔄 Fichiers Modifiés**

#### **Backend**
- `app.py` - 10 nouveaux endpoints (6 extraction + 3 reconstruction + 1 backup)

#### **Frontend**
- `src/lib/api.ts` - 10 nouvelles fonctions API
- `src/components/ActionButtons.svelte` - Boutons Extraire + Reconstruire connectés
- `src/components/WorkFolders.svelte` - Ouverture dossiers de travail
- `src/stores/project.ts` - Synchronisation avec extraction

#### **Configuration**
- `tsconfig.json` - Alias `$stores`
- `vite.config.ts` - Alias `$stores`

---

## 🎉 Récapitulatif Final

### ✅ **Extraction - Conformité au Flux**
- ✅ **ÉTAPE 1** : Validation initiale
- ✅ **ÉTAPE 2** : Sauvegarde de sécurité
- ✅ **ÉTAPE 3** : Initialisation extracteur
- ✅ **ÉTAPE 4** : Protection des codes
- ✅ **ÉTAPE 5** : Extraction dialogues
- ✅ **ÉTAPE 6** : Sauvegarde fichiers
- ✅ **POST** : Ouverture automatique

### ✅ **Reconstruction - Conformité au Flux**
- ✅ **ÉTAPE 1** : Validation initiale
- ✅ **ÉTAPE 2** : Correction guillemets automatique
- ✅ **ÉTAPE 3** : Validation extraction effectuée
- ✅ **ÉTAPE 5** : Validation fichiers traduction
- ✅ **ÉTAPE 7** : Reconstruction proprement dite
- ✅ **ÉTAPE 8** : Remplacement placeholders
- ✅ **ÉTAPE 9** : Marqueur reconstruction + sauvegarde

### ✅ **Fonctionnalités Complètes**
- ✅ Protection complète des codes Ren'Py
- ✅ Gestion des doublons
- ✅ Backup automatique avant extraction
- ✅ Ouverture automatique configurable
- ✅ Génération fichiers de traduction
- ✅ Métadonnées pour reconstruction
- ✅ Validation fichiers avant reconstruction
- ✅ Correction guillemets automatique
- ✅ Reconstruction ligne par ligne
- ✅ Restauration des placeholders (ordre critique)
- ✅ Support multiplateforme
- ✅ Dossiers corrects (01_Temporary)

### ✅ **Intégrations**
- ✅ Système de backup
- ✅ Paramètres utilisateur
- ✅ Projet global (header)
- ✅ Architecture de l'application
- ✅ Ouverture dossiers de travail

---

---

## 🔨 Système de Reconstruction

### 📦 Backend (`src/backend/reconstruction.py`)

#### **Classe FileReconstructor**
```python
class FileReconstructor:
    - load_file_content()               # Charge fichier + métadonnées
    - _load_data_for_reconstruction()   # Charge JSON + traductions
    - _load_translation_files()         # Charge .txt multi-fichiers
    - reconstruct_file()                # Reconstruction principale
    - _rebuild_content()                # Reconstruit lignes traduites
    - _replace_all_placeholders()       # Restaure codes/astérisques/tildes
    - _add_reconstruction_marker()      # Ajoute marqueur fin de fichier
```

#### **Fonctions Utilitaires**
```python
validate_translation_files()          # Validation avant reconstruction
fix_unescaped_quotes_in_txt()        # Correction guillemets automatique
```

### 🌐 API REST (`app.py`)

#### **Endpoints de Reconstruction**
- `POST /api/reconstruction/validate` - Validation fichiers traduction
- `POST /api/reconstruction/fix-quotes` - Correction guillemets
- `POST /api/reconstruction/reconstruct` - Reconstruction principale

### 🎨 Frontend

#### **Store Réactif** (`src/stores/reconstruction.ts`)
```typescript
// État de la reconstruction
reconstructionStore: {
  isReconstructing: boolean
  reconstructionProgress: string
  lastResult: ReconstructionResult | null
  lastValidation: ValidationResult | null
}

// Actions
reconstructionActions.validateFiles()
reconstructionActions.fixQuotesInFiles()
reconstructionActions.reconstructFile()
reconstructionActions.openReconstructedFile()
```

### 🔄 Flux de Reconstruction

```
1. Validation initiale (fichier chargé + extraction effectuée)
2. Correction automatique des guillemets non-échappés
3. Validation des fichiers de traduction (compteurs)
4. Chargement des métadonnées (_positions.json)
5. Chargement des traductions (_dialogue.txt, _asterix.txt, etc.)
6. Reconstruction ligne par ligne avec traductions
7. Remplacement des placeholders (codes → astérisques → tildes → vides)
8. Ajout marqueur de reconstruction
9. Sauvegarde du fichier traduit
```

### ✅ Fonctionnalités Reconstruction

#### **1. Correction Automatique des Guillemets**
```python
# Corrige " en \" dans les fichiers de traduction
fix_unescaped_quotes_in_txt(filepath)
```

#### **2. Validation des Fichiers**
```python
# Vérifie cohérence des compteurs
validate_translation_files(
  filepath,
  extracted_count,  # Dialogues attendus
  asterix_count,    # Astérisques attendus
  tilde_count       # Tildes attendus
)
```

#### **3. Reconstruction Ligne par Ligne**
```python
# Pour chaque ligne avec traduction:
nouvelle_ligne = prefixe + traduction + suffixe + suffixe_ligne
```

#### **4. Remplacement des Placeholders**
```python
# Ordre CRITIQUE (ne pas modifier):
1. Codes/variables:   RENPY_CODE_001 → [player_name]
2. Astérisques:       RENPY_ASTERISK_001 → * "traduction"
3. Tildes:            RENPY_TILDE_001 → ~ "traduction"
4. Vides:             RENPY_EMPTY_001 → ""
```

#### **5. Marqueur de Reconstruction**
```python
# Ajouté automatiquement à la fin du fichier
# Fichier reconstruit après traduction par RenExtract le 2025-01-08 14:30:45
```

### 📁 Fichiers Générés

#### **Mode 'new_file'** (par défaut)
```
game/tl/french/
└── script_translated.rpy    # Nouveau fichier créé
```

#### **Mode 'overwrite'**
```
game/tl/french/
└── script.rpy               # Fichier original écrasé (backup auto créé)
```

---

## 🔜 Prochaines Étapes

Les systèmes d'**extraction** et de **reconstruction** sont **100% opérationnels** !

**Prochaine implémentation** :

**FLUX_04 : Vérification** 🔍
- Vérifier la cohérence des traductions
- Détecter les textes non traduits
- Détecter les erreurs de syntaxe
- Générer des rapports HTML

**Les systèmes d'extraction et reconstruction sont complets et fonctionnels !** 🚀
