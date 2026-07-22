# ⛽ FuelTrack Web

Application web sécurisée d'inventaire des pleins de carburant avec OCR, géolocalisation et statistiques.

## 🚀 Déploiement rapide sur Render (Gratuit)

### 1. Créer un compte Render
- Allez sur [render.com](https://render.com)
- Inscrivez-vous avec GitHub ou email

### 2. Déployer via Blueprint
1. Dans votre dashboard Render, cliquez sur **"New +"** → **"Blueprint"**
2. Connectez votre repo GitHub ou uploadz les fichiers
3. Render détectera automatiquement le `render.yaml`
4. Cliquez sur **"Apply"**
5. Définissez votre mot de passe dans les variables d'environnement :
   - `ADMIN_PASSWORD` = votre mot de passe
   - `SECRET_KEY` = laissez la valeur générée automatiquement

### 3. Alternative : Déploiement manuel
1. **New +** → **"Web Service"**
2. Connectez votre repo ou uploadz un zip
3. Configuration :
   - **Runtime** : Python 3
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn -w 2 -b 0.0.0.0:$PORT app:app`
4. Ajoutez les variables d'environnement :
   - `ADMIN_PASSWORD` = votre mot de passe
   - `SECRET_KEY` = clé aléatoire longue (générez sur randomkeygen.com)
5. Ajoutez un **Disk** :
   - Name : `fueltrack-data`
   - Mount Path : `/data`
   - Size : 1 GB (gratuit)
6. Cliquez **"Create Web Service"**

## 🐳 Déploiement Docker

```bash
docker build -t fueltrack .
docker run -p 5000:5000 -e ADMIN_PASSWORD=votre_mdp -e SECRET_KEY=cle_aleatoire fueltrack
```

## 📁 Structure du projet

```
fueltrack-web/
├── app.py              # Backend Flask avec auth JWT
├── requirements.txt   # Dépendances
├── templates/
│   └── index.html      # Frontend complet (SPA)
├── uploads/            # Photos des pleins
├── fueltrack.db        # Base SQLite
├── Dockerfile          # Conteneurisation
├── render.yaml         # Config Render Blueprint
├── Procfile            # Config Heroku
└── .env.example        # Variables d'environnement
```

## 🔐 Sécurité

- **Authentification JWT** : Token stocké dans localStorage, valide 30 jours
- **Mot de passe hashé** : Werkzeug bcrypt
- **Protection API** : Toutes les routes protégées sauf login
- **CORS** : Configuré pour les appels cross-origin

## 🛠️ Développement local

```bash
# 1. Cloner
cd fueltrack-web

# 2. Environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Dépendances
pip install -r requirements.txt

# 4. Variables d'environnement
cp .env.example .env
# Éditez .env avec votre mot de passe

# 5. Lancer
python app.py
# → http://localhost:5000
```

## 📱 Utilisation sur mobile

1. Déployez sur Render
2. Ouvrez l'URL sur votre téléphone
3. Connectez-vous avec votre mot de passe
4. Ajoutez à l'écran d'accueil (Chrome → ⋮ → "Ajouter à l'écran d'accueil")
5. L'application fonctionne comme une app native avec caméra et GPS

## 📤 Export/Import

| Format | Usage |
|--------|-------|
| **CSV** | Excel, Google Sheets, analyse externe |
| **JSON** | Sauvegarde complète avec métadonnées |
| **Partage** | WhatsApp, email, Drive via API Web Share |

## 🔄 Mise à jour du mot de passe

Sur Render :
1. Dashboard → votre service → **Environment**
2. Modifiez `ADMIN_PASSWORD`
3. **Manual Deploy** → **Deploy latest commit**

## 🆓 Limites du gratuit (Render)

- **Disque** : 1 GB (suffisant pour des années de données)
- **CPU/RAM** : Limité mais suffisant pour usage personnel
- **Sleep** : Le service s'endort après 15 min d'inactivité (se réveille en ~30s)
- **Bande passante** : 100 GB/mois

## 📝 API REST

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/auth/login` | POST | Connexion |
| `/api/auth/check` | GET | Vérifier token |
| `/api/vehicles` | GET/POST | Liste/Ajout véhicules |
| `/api/vehicles/<id>` | DELETE | Supprimer véhicule |
| `/api/fills` | GET/POST | Liste/Ajout pleins |
| `/api/fills/<id>` | DELETE | Supprimer plein |
| `/api/stats` | GET | Statistiques |
| `/api/export/csv` | GET | Export CSV |
| `/api/export/json` | GET | Export JSON |
| `/api/import` | POST | Import JSON |

## 🐛 Dépannage

**"Token expiré"** → Reconnectez-vous
**"Caméra non accessible"** → Autorisez la caméra dans les paramètres du navigateur
**"Hors ligne"** → Vérifiez votre connexion ou si le serveur est en veille (Render)
