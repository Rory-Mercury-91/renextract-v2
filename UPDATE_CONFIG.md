# Configuration des Mises à Jour Automatiques

Ce document explique comment configurer le système de mise à jour automatique de votre application.

## Configuration GitHub

Pour que les mises à jour automatiques fonctionnent, vous devez configurer les informations de votre dépôt GitHub.

### Méthode 1: Variables d'environnement (Recommandée)

Créez un fichier `.env` à la racine du projet avec le contenu suivant :

```env
# Configuration GitHub pour les mises à jour automatiques
GITHUB_REPO_OWNER=votre-username
GITHUB_REPO_NAME=renextract-v2
APP_VERSION=2.0.0

# Configuration des mises à jour automatiques
UPDATE_CHECK_INTERVAL_HOURS=24
AUTO_CHECK_UPDATES=true
AUTO_DOWNLOAD_UPDATES=false
AUTO_INSTALL_UPDATES=false
```

### Méthode 2: Modification directe du fichier de configuration

Modifiez le fichier `src/backend/config.py` et changez les valeurs suivantes :

```python
# Configuration GitHub pour les mises à jour
GITHUB_REPO_OWNER = "votre-username"  # Votre nom d'utilisateur GitHub
GITHUB_REPO_NAME = "renextract-v2"    # Le nom de votre dépôt
APP_VERSION = "2.0.0"                 # Version actuelle de votre app
```

## Configuration des Mises à Jour

### Variables d'environnement disponibles

- `UPDATE_CHECK_INTERVAL_HOURS` : Intervalle de vérification en heures (défaut: 24)
- `AUTO_CHECK_UPDATES` : Vérification automatique (défaut: true)
- `AUTO_DOWNLOAD_UPDATES` : Téléchargement automatique (défaut: false)
- `AUTO_INSTALL_UPDATES` : Installation automatique (défaut: false)

### Configuration via l'interface utilisateur

Vous pouvez également configurer les mises à jour via l'interface utilisateur :

1. Cliquez sur l'icône de paramètres à côté du bouton "Vérifier les mises à jour"
2. Configurez les options selon vos préférences
3. Sauvegardez la configuration

## Fonctionnement

### Vérification des mises à jour

L'application vérifie automatiquement les mises à jour :

- Au démarrage (si `AUTO_CHECK_UPDATES=true`)
- Selon l'intervalle configuré
- Manuellement via le bouton "Vérifier les mises à jour"

### Processus de mise à jour

1. **Vérification** : L'app contacte l'API GitHub pour vérifier les nouvelles versions
2. **Téléchargement** : Si une mise à jour est disponible, elle peut être téléchargée
3. **Installation** : La mise à jour peut être installée automatiquement ou manuellement
4. **Redémarrage** : L'application redémarre avec la nouvelle version

### Compatibilité des versions

Le système compare les versions en utilisant le format sémantique (ex: 2.1.0 > 2.0.0).

## GitHub Actions

Pour que les mises à jour fonctionnent, votre dépôt GitHub doit avoir :

1. **GitHub Actions configurées** : Le workflow de build doit créer des releases
2. **Releases publiées** : Chaque version doit être publiée comme release sur GitHub
3. **Assets attachés** : Les exécutables doivent être attachés aux releases

### Exemple de workflow GitHub Actions

Votre workflow doit créer des releases avec des assets nommés selon votre OS :

- Windows : `app-windows-v2.1.0.exe`
- Linux : `app-linux-v2.1.0`
- macOS : `app-macos-v2.1.0`

## Dépannage

### Erreurs courantes

1. **"GITHUB_REPO_OWNER doit être configuré"**
   - Solution : Configurez la variable d'environnement ou modifiez `config.py`

2. **"Erreur de connexion"**
   - Solution : Vérifiez votre connexion internet et l'URL du dépôt

3. **"Aucun exécutable trouvé"**
   - Solution : Vérifiez que les assets sont correctement nommés dans les releases

### Logs de débogage

Les logs de débogage sont affichés dans la console. Recherchez les messages commençant par "DEBUG:" pour diagnostiquer les problèmes.

## Sécurité

- Les mises à jour sont téléchargées depuis GitHub (HTTPS)
- Les fichiers sont vérifiés avant installation
- Une sauvegarde de l'exécutable actuel est créée avant installation
- L'installation nécessite une confirmation utilisateur (sauf si `AUTO_INSTALL_UPDATES=true`)

## Support

Si vous rencontrez des problèmes avec les mises à jour automatiques :

1. Vérifiez la configuration GitHub
2. Consultez les logs de débogage
3. Testez manuellement la vérification des mises à jour
4. Vérifiez que les releases GitHub sont correctement configurées
