#!/bin/bash
# Script pour démarrer l'environnement de développement complet

echo "🚀 Démarrage de l'environnement de développement RenExtract v2"
echo "=============================================================="

# Fonction pour nettoyer les processus à la sortie
cleanup() {
    echo "🛑 Arrêt des serveurs..."
    pkill -f "python.*flask"
    pkill -f "vite"
    exit 0
}

# Capturer Ctrl+C
trap cleanup SIGINT

# Démarrer le backend Flask
echo "📡 Démarrage du backend Flask (port 5000)..."
cd /home/kanon/projects/renextract-v2
source .venv/bin/activate
python -c "
import sys
sys.path.append('src/backend')
from flask import Flask
from flask_cors import CORS
from src.backend.api.routes import API

app = Flask(__name__)
CORS(app)
app.register_blueprint(API)

print('✅ Backend Flask démarré sur http://127.0.0.1:5000')
app.run(host='127.0.0.1', port=5000, debug=False)
" &

# Attendre un peu que le backend démarre
sleep 2

# Démarrer le frontend Vite
echo "🌐 Démarrage du frontend Vite (port 3000)..."
npm run dev &

echo ""
echo "✅ Environnement de développement démarré !"
echo "📡 Backend API: http://localhost:5000"
echo "🌐 Frontend: http://localhost:3000"
echo "🔗 Proxy: /api → http://127.0.0.1:5000"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter tous les serveurs"

# Attendre indéfiniment
wait
