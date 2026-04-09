"""
config.py — Configuration centralisée de l'application.
Modifier ce fichier pour adapter les paramètres sans toucher au code métier.
"""

# ══════════════════════════════════════════════════════════════════════
# AUTHENTIFICATION
# ══════════════════════════════════════════════════════════════════════

# Emails autorisés à se connecter (minuscules)
AUTHORIZED_EMAILS = [
    "admin@rte-france.com",
    "manager1@rte-france.com",
    "manager2@rte-france.com",
    "charge.etudes@rte-france.com",
    # Ajouter ici les emails des utilisateurs autorisés
]

# Emails ayant le rôle administrateur (accès attribution sans code)
ADMIN_EMAILS = [
    "admin@rte-france.com",
]

# Code administrateur (fallback si l'utilisateur n'est pas dans ADMIN_EMAILS)
ADMIN_CODE = "RTE2026"


# ══════════════════════════════════════════════════════════════════════
# SMTP — Configuration pour l'envoi d'emails de relance
# ══════════════════════════════════════════════════════════════════════

SMTP_CONFIG = {
    "host": "smtp.rte-france.com",   # Serveur SMTP
    "port": 587,                      # Port (587 = TLS, 465 = SSL)
    "use_tls": True,                  # Activer TLS
    "username": "",                   # Laisser vide si pas d'auth SMTP
    "password": "",                   # Laisser vide si pas d'auth SMTP
    "sender_email": "guichet-unique@rte-france.com",
    "sender_name": "Guichet Unique RTE",
}

# Activer/désactiver l'envoi réel d'emails (False = mode simulation)
SMTP_ENABLED = False


# ══════════════════════════════════════════════════════════════════════
# APPLICATION
# ══════════════════════════════════════════════════════════════════════

APP_VERSION = "1.1"
