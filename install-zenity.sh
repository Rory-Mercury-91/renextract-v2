#!/bin/bash

# Script d'installation de zenity pour WSL
# Ce script installe zenity pour permettre l'utilisation des dialogues graphiques

echo "🌐 Installation de zenity pour WSL..."
echo "=================================="

# Vérifier si on est dans WSL
if [[ -f /proc/version ]] && grep -q "microsoft" /proc/version; then
    echo "✅ Environnement WSL détecté"
else
    echo "⚠️  Ce script est conçu pour WSL, mais l'environnement actuel ne semble pas être WSL"
    read -p "Voulez-vous continuer quand même ? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Mettre à jour les paquets
echo "📦 Mise à jour des paquets..."
sudo apt update

# Installer zenity
echo "🔧 Installation de zenity..."
sudo apt install -y zenity

# Vérifier l'installation
echo "✅ Vérification de l'installation..."
if zenity --version; then
    echo "🎉 zenity a été installé avec succès !"
    echo "Les dialogues de fichier devraient maintenant fonctionner dans l'application."
else
    echo "❌ Erreur lors de l'installation de zenity"
    exit 1
fi

echo ""
echo "💡 Conseils d'utilisation :"
echo "- Les chemins Windows sont accessibles via /mnt/c/, /mnt/d/, etc."
echo "- Vous pouvez maintenant utiliser les dialogues graphiques dans l'application"
echo "- Si les dialogues ne fonctionnent toujours pas, redémarrez l'application"
