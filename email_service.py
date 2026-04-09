"""
email_service.py — Service d'envoi d'emails (relance manager).
Supporte un mode simulation quand SMTP_ENABLED = False.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_CONFIG, SMTP_ENABLED

logger = logging.getLogger("guichet_unique.email")


def build_relance_html(demande: dict) -> str:
    """Construit le corps HTML de l'email de relance."""
    return f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #005F83, #00B2E3);
                    padding: 20px; border-radius: 12px 12px 0 0; text-align: center;">
            <h2 style="color: white; margin: 0;">Guichet Unique RTE</h2>
            <p style="color: rgba(255,255,255,0.8); margin: 4px 0 0;">Relance — Demande d'étude</p>
        </div>
        <div style="background: white; padding: 24px; border: 1px solid #E6EDF3;
                    border-radius: 0 0 12px 12px;">
            <p>Bonjour,</p>
            <p>Nous vous contactons au sujet de la demande d'étude suivante,
               qui n'a pas encore fait l'objet d'une commande :</p>

            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr style="background: #F0F4F8;">
                    <td style="padding: 8px 12px; font-weight: 600; width: 40%;">ID Demande</td>
                    <td style="padding: 8px 12px;">{demande.get('ID_Demande', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 12px; font-weight: 600;">Projet</td>
                    <td style="padding: 8px 12px;">{demande.get('Nom_Ouvrage_Projet', 'N/A')}</td>
                </tr>
                <tr style="background: #F0F4F8;">
                    <td style="padding: 8px 12px; font-weight: 600;">Trimestre</td>
                    <td style="padding: 8px 12px;">{demande.get('Trimestre_Attribution', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 12px; font-weight: 600;">Entreprise attribuée</td>
                    <td style="padding: 8px 12px;">{demande.get('Attribution_Finale', 'N/A')}</td>
                </tr>
                <tr style="background: #F0F4F8;">
                    <td style="padding: 8px 12px; font-weight: 600;">Montant estimé</td>
                    <td style="padding: 8px 12px;">{demande.get('Montant_Total', 'N/A')} k€</td>
                </tr>
                <tr>
                    <td style="padding: 8px 12px; font-weight: 600;">Statut</td>
                    <td style="padding: 8px 12px;">{demande.get('Statut', 'N/A')}</td>
                </tr>
            </table>

            <p>Merci de bien vouloir procéder à la commande ou de nous informer
               si cette demande n'est plus d'actualité.</p>

            <p style="color: #6B7280; font-size: 0.85rem; margin-top: 24px;">
                — Guichet Unique RTE (message automatique)
            </p>
        </div>
    </div>
    """


def send_relance_email(
    to_email: str,
    demande: dict,
    manager_name: str = "",
) -> dict:
    """
    Envoie un email de relance au manager.
    Retourne {"success": True/False, "message": "..."}.
    """
    subject = (
        f"[Guichet Unique] Relance — {demande.get('Nom_Ouvrage_Projet', 'Demande')} "
        f"({demande.get('ID_Demande', '')})"
    )
    html_body = build_relance_html(demande)

    # Mode simulation
    if not SMTP_ENABLED:
        logger.info(f"[SIMULATION] Email de relance → {to_email} | Sujet : {subject}")
        return {
            "success": True,
            "message": (
                f"📧 Mode simulation — Email qui serait envoyé à {to_email}\n\n"
                f"Sujet : {subject}"
            ),
            "simulated": True,
        }

    # Envoi réel
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{SMTP_CONFIG['sender_name']} <{SMTP_CONFIG['sender_email']}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        if SMTP_CONFIG["port"] == 465:
            server = smtplib.SMTP_SSL(SMTP_CONFIG["host"], SMTP_CONFIG["port"], timeout=15)
        else:
            server = smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"], timeout=15)
            if SMTP_CONFIG["use_tls"]:
                server.starttls()

        if SMTP_CONFIG["username"]:
            server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])

        server.sendmail(SMTP_CONFIG["sender_email"], [to_email], msg.as_string())
        server.quit()

        logger.info(f"Email envoyé à {to_email} pour demande {demande.get('ID_Demande')}")
        return {"success": True, "message": f"Email envoyé à {to_email}", "simulated": False}

    except Exception as e:
        logger.error(f"Erreur envoi email à {to_email}: {e}")
        return {"success": False, "message": f"Erreur d'envoi : {e}", "simulated": False}
