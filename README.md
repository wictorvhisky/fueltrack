# ⛽ FuelTrack Web

Application web sécurisée d'inventaire des pleins de carburant avec OCR, géolocalisation et statistiques.

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
