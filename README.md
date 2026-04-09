# ⚡ Guichet Unique RTE — Gestion des Demandes d'Études

## 🚀 Installation

```bash
cd guichet_unique
pip install -r requirements.txt
streamlit run 🏠_Tableau_de_Bord.py
```

## 📁 Structure du projet

```
guichet_unique/
├── 🏠_Tableau_de_Bord.py        # Dashboard (page publique)
├── config.py                     # Configuration centralisée (emails, SMTP, admin)
├── auth.py                       # Authentification par email + contrôle admin
├── email_service.py              # Service d'envoi d'emails (relance manager)
├── data_manager.py               # CRUD données + verrouillage fichier
├── ui_components.py              # Composants UI, sidebar, CSS RTE
├── requirements.txt
├── .streamlit/config.toml
├── assets/logo_rte.png
├── data/                         # Base Excel (créée automatiquement)
│   └── historique/               # Backups automatiques
└── pages/
    ├── 1_➕_Nouvelle_Demande.py  # Formulaire de création (auth requise)
    ├── 2_📋_Mes_Demandes.py     # Consultation / modification (auth requise)
    ├── 3_🎯_Attribution.py      # Attribution 2 étapes (auth + admin)
    ├── 4_📦_Import_Commandes.py # Import extraction commandes (auth requise)
    ├── 5_📊_Données.py          # Vue données + relance email (auth requise)
    └── 6_📈_Suivi.py            # Analyses avancées (auth requise)
```

## 🔐 Authentification

L'accès aux pages de demandes nécessite une connexion par email.

**Emails autorisés** : définis dans `config.py` → `AUTHORIZED_EMAILS`
**Emails admin** : définis dans `config.py` → `ADMIN_EMAILS` (accès direct à Attribution)
**Code admin** : `RTE2026` (pour les non-admins qui ont le code)

Le dashboard reste accessible sans connexion.

## 🎯 Attribution en 2 étapes

1. L'utilisateur sélectionne la demande et le GIE
2. Il clique sur "Attribuer cette demande"
3. Un encart de confirmation apparaît avec les détails
4. Il doit explicitement cliquer "Oui, confirmer" ou "Annuler"

## 📧 Relance manager par email

Sur la page Données, un bouton "Relancer" apparaît pour chaque demande attribuée sans commande.

**Mode simulation** (par défaut) : l'email n'est pas envoyé, un aperçu s'affiche.
**Mode réel** : configurer SMTP dans `config.py` et mettre `SMTP_ENABLED = True`.

## ⚙️ Configuration

Tout se configure dans `config.py` :
- `AUTHORIZED_EMAILS` — emails autorisés à se connecter
- `ADMIN_EMAILS` — emails avec accès admin direct
- `ADMIN_CODE` — code de fallback pour l'accès admin
- `SMTP_CONFIG` — serveur SMTP pour les relances
- `SMTP_ENABLED` — activer/désactiver l'envoi réel

## 📊 Export Excel

Chaque tableau de données dispose d'un bouton "Exporter en Excel" avec formatage RTE.
