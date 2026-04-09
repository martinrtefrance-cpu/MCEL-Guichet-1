# Déploiement sur Streamlit Cloud

## 1. Prérequis

- Un compte GitHub avec le projet poussé dans un repository
- Un compte Streamlit Cloud (https://share.streamlit.io)

## 2. Structure du projet

```
guichet_unique/
├── .streamlit/
│   └── config.toml          # Thème et config serveur
├── assets/
│   └── logo_rte.png
├── data/
│   ├── guichet_unique_db.xlsx
│   ├── SIEPR.xlsx            # Référentiel EOTP
│   └── historique/
├── pages/
│   ├── 1_Nouvelle_Demande.py
│   ├── 2_Mes_Demandes.py
│   ├── 3_Attribution.py
│   ├── 4_Import_Commandes.py
│   ├── 5_Donnees.py
│   ├── 6_Suivi.py
│   └── 7_ModOp.py
├── Tableau_de_Bord.py        # ← Point d'entrée principal
├── auth.py
├── config.py
├── data_manager.py
├── email_service.py
├── ui_components.py
├── requirements.txt
└── README.md
```

## 3. Déployer sur Streamlit Cloud

1. **Pousser le code** sur un repo GitHub (public ou privé)

2. **Se connecter** à https://share.streamlit.io avec votre compte GitHub

3. **Créer une nouvelle app** :
   - Repository : votre repo GitHub
   - Branch : `main`
   - Main file path : `Tableau_de_Bord.py`

4. **Configurer les secrets** (optionnel, pour l'envoi réel d'emails) :
   Dans Streamlit Cloud > Settings > Secrets, ajouter :
   ```toml
   [smtp]
   host = "smtp.rte-france.com"
   port = 587
   username = ""
   password = ""
   sender_email = "guichet-unique@rte-france.com"
   enabled = false
   ```

5. **Lancer le déploiement** — Streamlit Cloud installe automatiquement
   les dépendances depuis `requirements.txt`

## 4. Limitations Streamlit Cloud

- **Stockage éphémère** : le filesystem est réinitialisé à chaque redémarrage.
  Les données dans `data/guichet_unique_db.xlsx` seront perdues.
  → Pour un usage production, prévoir une base de données externe
  (PostgreSQL, Google Sheets, Supabase, etc.)

- **Mise en veille** : les apps Community Cloud se mettent en veille
  après ~7 jours sans trafic. Voir section 5 ci-dessous.

## 5. Maintenir l'application active — Solution UptimeRobot

Streamlit Cloud met les apps en veille après une période d'inactivité.
La solution recommandée est d'utiliser un service de monitoring HTTP
qui pingue l'URL de l'app régulièrement.

### Option A : UptimeRobot (recommandé, gratuit)

1. Créer un compte sur https://uptimerobot.com (plan gratuit = 50 monitors)

2. Créer un nouveau monitor :
   - Type : **HTTP(s)**
   - Friendly Name : `Guichet Unique RTE`
   - URL : `https://votre-app.streamlit.app`
   - Monitoring Interval : **every 5 minutes**

3. C'est tout — UptimeRobot enverra une requête HTTP GET toutes les
   5 minutes, ce qui empêche Streamlit Cloud de mettre l'app en veille.

### Option B : Cron-job.org (alternative gratuite)

1. Créer un compte sur https://cron-job.org

2. Créer un cron job :
   - URL : `https://votre-app.streamlit.app`
   - Schedule : toutes les 5 minutes (`*/5 * * * *`)
   - Request method : GET

### Option C : GitHub Actions (si le repo est sur GitHub)

Ajouter le fichier `.github/workflows/keepalive.yml` (fourni dans le projet)
pour un ping automatique toutes les 25 minutes via GitHub Actions.

### Pourquoi ces solutions sont acceptables

- Elles utilisent des requêtes HTTP GET standard (aucun hack)
- Streamlit Cloud supporte officiellement le trafic entrant
- Aucune modification du code de l'application n'est nécessaire
- UptimeRobot fournit aussi des alertes si l'app tombe
