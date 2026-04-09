"""
auth.py — Authentification par email.
Gère la connexion, la session utilisateur et la protection des pages.
"""
import streamlit as st
import logging
from typing import Optional
from config import AUTHORIZED_EMAILS, ADMIN_EMAILS, ADMIN_CODE

logger = logging.getLogger("guichet_unique.auth")


def get_current_user() -> Optional[dict]:
    """Retourne les infos de l'utilisateur connecté, ou None."""
    if st.session_state.get("authenticated"):
        return {
            "email": st.session_state.get("user_email", ""),
            "is_admin": st.session_state.get("user_is_admin", False),
        }
    return None


def logout():
    """Déconnecte l'utilisateur."""
    for key in ["authenticated", "user_email", "user_is_admin", "admin_authenticated"]:
        st.session_state.pop(key, None)
    logger.info("Utilisateur déconnecté")


def _render_login_page():
    """Affiche la page de connexion style RTE."""
    import base64, os
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo_rte.png")
    logo_b64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()

    # CSS spécifique login
    st.markdown("""
    <style>
    .login-container {
        max-width: 420px; margin: 4rem auto; text-align: center;
    }
    .login-logo { width: 80px; border-radius: 50%; margin-bottom: 1rem; }
    .login-title {
        font-size: 1.5rem; font-weight: 700; color: #005F83;
        margin-bottom: 0.3rem;
    }
    .login-subtitle {
        font-size: 0.9rem; color: #6B7280; margin-bottom: 2rem;
    }
    .login-card {
        background: white; border: 1px solid #E6EDF3;
        border-radius: 16px; padding: 2rem;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="login-container">
        <img src="data:image/png;base64,{logo_b64}" class="login-logo" alt="RTE">
        <div class="login-title">Guichet Unique</div>
        <div class="login-subtitle">Connectez-vous avec votre email RTE</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Adresse email",
                placeholder="prenom.nom@rte-france.com",
                key="login_email_input",
            )
            submitted = st.form_submit_button(
                "🔑 Se connecter",
                use_container_width=True,
                type="primary",
            )

            if submitted:
                email_clean = email.strip().lower()
                if not email_clean:
                    st.error("Veuillez entrer votre adresse email.")
                elif email_clean not in [e.lower() for e in AUTHORIZED_EMAILS]:
                    st.error("⛔ Adresse email non autorisée.")
                    logger.warning(f"Tentative de connexion refusée : {email_clean}")
                else:
                    # Connexion réussie
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = email_clean
                    st.session_state["user_is_admin"] = email_clean in [
                        e.lower() for e in ADMIN_EMAILS
                    ]
                    # Si admin par email, pré-autoriser la page attribution
                    if st.session_state["user_is_admin"]:
                        st.session_state["admin_authenticated"] = True
                    logger.info(f"Connexion réussie : {email_clean}")
                    st.rerun()

        st.caption("Contactez votre administrateur si vous n'avez pas accès.")


def require_auth() -> dict:
    """
    Bloque la page si l'utilisateur n'est pas connecté.
    Affiche la page de login à la place.
    Retourne les infos utilisateur si connecté.
    """
    user = get_current_user()
    if user:
        return user

    _render_login_page()
    st.stop()


def check_admin_access() -> bool:
    """
    Vérifie l'accès admin. Si l'utilisateur est admin par email,
    accès direct. Sinon, demande le code admin.
    """
    # Déjà authentifié admin
    if st.session_state.get("admin_authenticated"):
        return True

    # Admin par email
    user = get_current_user()
    if user and user.get("is_admin"):
        st.session_state["admin_authenticated"] = True
        return True

    # Sinon, formulaire de code
    st.markdown("""
    <div class="admin-lock-box">
        <h3>🔒 Accès restreint</h3>
        <p style="color:#6B7280; margin-bottom:0;">
            Cette page nécessite un code administrateur.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("admin_code_form"):
            code = st.text_input(
                "Code administrateur",
                type="password",
                placeholder="Entrez le code…",
            )
            submitted = st.form_submit_button(
                "🔓 Valider", use_container_width=True, type="primary",
            )
            if submitted:
                if code == ADMIN_CODE:
                    st.session_state["admin_authenticated"] = True
                    st.rerun()
                else:
                    st.error("❌ Code incorrect.")

    return False
