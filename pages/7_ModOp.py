"""
7_ModOp.py — Mode Operatoire : guide visuel du process metier
pour les managers de projet RTE.
"""
import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ui_components import inject_css, render_header, render_sidebar

st.set_page_config(page_title="ModOp", page_icon="📖", layout="wide", initial_sidebar_state="expanded")
inject_css()
render_sidebar(active_page="modop")
render_header("Mode Operatoire — Guide du processus")

# ══════════════════════════════════════════════════════════════════════
# CSS specifique a la page ModOp
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* Workflow horizontal */
.workflow-container {
    display: flex; justify-content: center; align-items: stretch;
    gap: 0; margin: 2rem 0; flex-wrap: wrap;
}
.workflow-step {
    flex: 1; min-width: 180px; max-width: 240px;
    text-align: center; position: relative; padding: 0 0.5rem;
}
.workflow-circle {
    width: 72px; height: 72px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 0.8rem; font-size: 1.8rem;
    box-shadow: 0 4px 16px rgba(0,0,0,0.10);
    border: 3px solid #FFFFFF;
}
.workflow-title {
    font-weight: 700; font-size: 1rem; color: #1E293B;
    margin-bottom: 0.3rem;
}
.workflow-desc {
    font-size: 0.78rem; color: #64748B; line-height: 1.4;
}
.workflow-arrow {
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem; color: #CBD5E1; min-width: 40px;
    padding-top: 0; margin-top: 1.2rem;
}

/* Detail cards */
.modop-card {
    background: #FFFFFF; border-radius: 14px; padding: 1.5rem 1.8rem;
    border: 1px solid #F0F1F3; margin-bottom: 1.2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.03);
    transition: transform 0.15s ease;
}
.modop-card:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(0,0,0,0.07); }
.modop-card-header {
    display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.8rem;
}
.modop-card-icon {
    width: 44px; height: 44px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem; flex-shrink: 0;
}
.modop-card-title { font-weight: 700; font-size: 1.05rem; color: #1E293B; }
.modop-card-subtitle { font-size: 0.75rem; color: #94A3B8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.modop-card-body { font-size: 0.88rem; color: #475569; line-height: 1.6; }
.modop-card-body ul { margin: 0.4rem 0 0 1rem; padding: 0; }
.modop-card-body li { margin-bottom: 0.3rem; }

/* Status flow */
.status-flow {
    display: flex; align-items: center; justify-content: center;
    gap: 0.3rem; margin: 1.5rem 0; flex-wrap: wrap;
}
.status-pill {
    padding: 0.4rem 1rem; border-radius: 20px;
    font-size: 0.82rem; font-weight: 600; letter-spacing: 0.2px;
}
.status-arrow { font-size: 1.1rem; color: #CBD5E1; }

/* Tips box */
.tip-box {
    background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%);
    border: 1px solid #BBF7D0; border-radius: 12px;
    padding: 1rem 1.3rem; margin-top: 1rem;
    display: flex; gap: 0.6rem; align-items: flex-start;
}
.tip-icon { font-size: 1.2rem; flex-shrink: 0; margin-top: 0.1rem; }
.tip-text { font-size: 0.85rem; color: #166534; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# SECTION 1 — Vue d'ensemble du workflow
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="text-align:center; margin-bottom:0.5rem;">
    <span style="font-size:0.75rem; font-weight:600; color:#94A3B8; text-transform:uppercase; letter-spacing:1px;">
        Cycle de vie d'une demande d'etude
    </span>
</div>

<div class="workflow-container">
    <div class="workflow-step">
        <div class="workflow-circle" style="background: linear-gradient(135deg, #0E86D4, #00B4D8);">📝</div>
        <div class="workflow-title">1. Creation</div>
        <div class="workflow-desc">Le manager remplit le formulaire guide et enregistre en brouillon</div>
    </div>
    <div class="workflow-arrow">→</div>
    <div class="workflow-step">
        <div class="workflow-circle" style="background: linear-gradient(135deg, #F59E0B, #FBBF24);">📤</div>
        <div class="workflow-title">2. Soumission</div>
        <div class="workflow-desc">Le manager valide et soumet sa demande pour attribution</div>
    </div>
    <div class="workflow-arrow">→</div>
    <div class="workflow-step">
        <div class="workflow-circle" style="background: linear-gradient(135deg, #8B5CF6, #A78BFA);">🎯</div>
        <div class="workflow-title">3. Attribution</div>
        <div class="workflow-desc">L'admin attribue la demande a un GIE avec confirmation</div>
    </div>
    <div class="workflow-arrow">→</div>
    <div class="workflow-step">
        <div class="workflow-circle" style="background: linear-gradient(135deg, #22C55E, #4ADE80);">✅</div>
        <div class="workflow-title">4. Commande</div>
        <div class="workflow-desc">Import du systeme de commandes et cloture automatique</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Flux des statuts
st.markdown("""
<div class="status-flow">
    <span class="status-pill" style="background:#F1F5F9; color:#64748B;">Brouillon</span>
    <span class="status-arrow">→</span>
    <span class="status-pill" style="background:#FFF7ED; color:#C2410C;">Soumise</span>
    <span class="status-arrow">→</span>
    <span class="status-pill" style="background:#EFF6FF; color:#1D4ED8;">Attribuee</span>
    <span class="status-arrow">→</span>
    <span class="status-pill" style="background:#F0FDF4; color:#15803D;">Commandee</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════
# SECTION 2 — Detail de chaque etape
# ══════════════════════════════════════════════════════════════════════

c1, c2 = st.columns(2)

with c1:
    # Etape 1 — Creation
    st.markdown("""
    <div class="modop-card">
        <div class="modop-card-header">
            <div class="modop-card-icon" style="background:#EFF6FF;">📝</div>
            <div>
                <div class="modop-card-title">Etape 1 — Creation de la demande</div>
                <div class="modop-card-subtitle">Manager de projet</div>
            </div>
        </div>
        <div class="modop-card-body">
            <ul>
                <li><b>Selectionnez votre EOTP</b> : le manager et le nom du projet se remplissent automatiquement depuis le referentiel SIEPR</li>
                <li>Remplissez les sections du formulaire (accordeons depliables)</li>
                <li>Les champs obligatoires sont : <b>EOTP</b>, <b>Trimestre</b></li>
                <li>La demande est enregistree en statut <b>Brouillon</b></li>
                <li>Vous pouvez la modifier a tout moment avant soumission</li>
            </ul>
        </div>
        <div class="tip-box">
            <div class="tip-icon">💡</div>
            <div class="tip-text">Le formulaire conserve vos saisies meme si des champs obligatoires sont manquants. Corrigez uniquement les erreurs signalees.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Etape 3 — Attribution
    st.markdown("""
    <div class="modop-card">
        <div class="modop-card-header">
            <div class="modop-card-icon" style="background:#F5F3FF;">🎯</div>
            <div>
                <div class="modop-card-title">Etape 3 — Attribution a un GIE</div>
                <div class="modop-card-subtitle">Administrateur</div>
            </div>
        </div>
        <div class="modop-card-body">
            <ul>
                <li>L'administrateur accede a la page <b>Attribution</b> (acces protege)</li>
                <li>Il selectionne la demande et le GIE a attribuer</li>
                <li>Une <b>confirmation en 2 etapes</b> empeche les erreurs :
                    <br>① Clic sur "Attribuer" → ② Confirmation explicite</li>
                <li>L'attribution est <b>irreversible</b> — la demande est verrouillee</li>
                <li>Le statut passe a <b>Attribuee</b></li>
            </ul>
        </div>
        <div class="tip-box">
            <div class="tip-icon">🔒</div>
            <div class="tip-text">Apres attribution, le manager ne peut plus modifier sa demande. Les preferences GIE sont visibles par l'admin.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    # Etape 2 — Soumission
    st.markdown("""
    <div class="modop-card">
        <div class="modop-card-header">
            <div class="modop-card-icon" style="background:#FFFBEB;">📤</div>
            <div>
                <div class="modop-card-title">Etape 2 — Soumission pour attribution</div>
                <div class="modop-card-subtitle">Manager de projet</div>
            </div>
        </div>
        <div class="modop-card-body">
            <ul>
                <li>Dans <b>Mes demandes</b>, selectionnez la demande a soumettre</li>
                <li>Cliquez sur <b>"Soumettre la demande"</b></li>
                <li><b>Regle des 3 mois :</b>
                    <br>• Demande > 3 mois → soumission directe
                    <br>• Demande < 3 mois → cocher "Hors attribution en masse" + justification obligatoire</li>
                <li>Une alerte verte confirme la soumission</li>
                <li>Le statut passe a <b>Soumise</b></li>
            </ul>
        </div>
        <div class="tip-box">
            <div class="tip-icon">⏱️</div>
            <div class="tip-text">La regle des 3 mois garantit que les demandes recentes passent par une validation supplementaire avant d'entrer dans le cycle d'attribution.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Etape 4 — Commande
    st.markdown("""
    <div class="modop-card">
        <div class="modop-card-header">
            <div class="modop-card-icon" style="background:#F0FDF4;">✅</div>
            <div>
                <div class="modop-card-title">Etape 4 — Commande et cloture</div>
                <div class="modop-card-subtitle">Administrateur</div>
            </div>
        </div>
        <div class="modop-card-body">
            <ul>
                <li>L'admin importe un fichier Excel de commandes via la page <b>Import</b></li>
                <li>Le rapprochement est automatique par <b>EOTP2</b></li>
                <li>Les demandes matchees passent au statut <b>Commandee</b></li>
                <li>Les EOTP non trouves sont listes pour verification manuelle</li>
                <li>Le tableau de bord se met a jour en temps reel</li>
            </ul>
        </div>
        <div class="tip-box">
            <div class="tip-icon">📧</div>
            <div class="tip-text">Si une demande attribuee n'a pas de commande, l'admin peut envoyer une relance email au manager directement depuis la page Donnees.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════
# SECTION 3 — Roles et permissions
# ══════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="text-align:center; margin-bottom:1rem;">
    <span style="font-size:0.75rem; font-weight:600; color:#94A3B8; text-transform:uppercase; letter-spacing:1px;">
        Roles et permissions
    </span>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="modop-card" style="text-align:center; border-top: 3px solid #0E86D4;">
        <div style="font-size:2rem; margin-bottom:0.5rem;">👤</div>
        <div class="modop-card-title">Manager de projet</div>
        <div class="modop-card-body" style="text-align:left; margin-top:0.8rem;">
            <ul>
                <li>Creer des demandes</li>
                <li>Modifier ses brouillons</li>
                <li>Soumettre pour attribution</li>
                <li>Consulter ses demandes</li>
                <li>Exporter en Excel</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="modop-card" style="text-align:center; border-top: 3px solid #F59E0B;">
        <div style="font-size:2rem; margin-bottom:0.5rem;">🔑</div>
        <div class="modop-card-title">Administrateur</div>
        <div class="modop-card-body" style="text-align:left; margin-top:0.8rem;">
            <ul>
                <li>Tout ce que fait le manager</li>
                <li>Attribuer les demandes</li>
                <li>Importer les commandes</li>
                <li>Voir toutes les demandes</li>
                <li>Envoyer des relances email</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="modop-card" style="text-align:center; border-top: 3px solid #22C55E;">
        <div style="font-size:2rem; margin-bottom:0.5rem;">🌐</div>
        <div class="modop-card-title">Visiteur</div>
        <div class="modop-card-body" style="text-align:left; margin-top:0.8rem;">
            <ul>
                <li>Consulter le tableau de bord</li>
                <li>Voir les KPI globaux</li>
                <li>Consulter le mode operatoire</li>
                <li style="color:#94A3B8;">Pas de creation/modification</li>
                <li style="color:#94A3B8;">Pas d'export</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════
# SECTION 4 — FAQ rapide
# ══════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="text-align:center; margin-bottom:1rem;">
    <span style="font-size:0.75rem; font-weight:600; color:#94A3B8; text-transform:uppercase; letter-spacing:1px;">
        Questions frequentes
    </span>
</div>
""", unsafe_allow_html=True)

with st.expander("Comment modifier une demande deja soumise ?"):
    st.markdown(
        "Une demande **Soumise** ne peut plus etre modifiee directement. "
        "Contactez l'administrateur pour qu'il la repasse en Brouillon, "
        "ou annulez la demande et recreez-en une nouvelle."
    )

with st.expander("Que signifie 'Demande hors attribution en masse' ?"):
    st.markdown(
        "Les demandes de moins de 3 mois sont normalement traitees lors du cycle trimestriel. "
        "Si vous devez soumettre une demande urgente avant le prochain cycle, "
        "cochez cette case et fournissez une justification. "
        "L'administrateur en sera informe."
    )

with st.expander("Mon EOTP n'apparait pas dans la liste — que faire ?"):
    st.markdown(
        "L'EOTP doit exister dans le referentiel **SIEPR** (`data/SIEPR.xlsx`). "
        "Si votre EOTP est nouveau ou manquant, contactez l'administrateur pour "
        "qu'il mette a jour le fichier de reference."
    )

with st.expander("Comment suivre l'avancement de mes demandes ?"):
    st.markdown(
        "Rendez-vous sur **Mes demandes** pour voir le statut de chacune, "
        "ou sur **Suivi & analyses** pour une vue globale avec graphiques. "
        "Le **Tableau de bord** affiche les KPI en temps reel."
    )

with st.expander("Qui peut attribuer une demande ?"):
    st.markdown(
        "Seuls les **administrateurs** ont acces a la page Attribution. "
        "L'acces est protege soit par l'email (liste `ADMIN_EMAILS` dans la config), "
        "soit par un code d'acces communique en interne."
    )
