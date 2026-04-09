"""
ui_components.py — Composants d'interface, style SaaS Dashboard.
Contraste corrigé : secondaryBackgroundColor est clair, sidebar foncée via CSS.
"""
import streamlit as st
import pandas as pd
import io
import os

RTE_BLUE = "#00B4D8"
RTE_DARK_BLUE = "#0E86D4"
RTE_LIGHT_BLUE = "#E8F4FD"
LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo_rte.png")
PLACEHOLDER = "..."

PAGE_PATHS = {
    "dashboard":   "Tableau_de_Bord.py",
    "nouvelle":    "pages/1_Nouvelle_Demande.py",
    "demandes":    "pages/2_Mes_Demandes.py",
    "attribution": "pages/3_Attribution.py",
    "import":      "pages/4_Import_Commandes.py",
    "donnees":     "pages/5_Donnees.py",
    "suivi":       "pages/6_Suivi.py",
    "modop":       "pages/7_ModOp.py",
}


def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Page layout */
    .block-container { max-width: 1200px !important; padding: 1.5rem 2rem 3rem !important; }
    .stApp > header + div, .stApp { background: #F8F9FB !important; }

    /* ══ HEADER ════════════════════════════════════════════ */
    .rte-header {
        background: linear-gradient(135deg, #0E86D4 0%, #00B4D8 100%);
        padding: 1.1rem 1.8rem; border-radius: 16px;
        display: flex; align-items: center; gap: 1rem;
        margin-bottom: 1.8rem;
        box-shadow: 0 8px 32px rgba(14,134,212,0.18);
    }
    .rte-header img { height: 44px; border-radius: 12px; }
    .rte-header h1 { color: #FFFFFF; font-size: 1.35rem; font-weight: 700; margin: 0; }
    .rte-header p { color: rgba(255,255,255,0.75); margin: 0; font-size: 0.82rem; }

    /* ══ KPI CARDS ═════════════════════════════════════════ */
    .kpi-card {
        background: #FFFFFF; border-radius: 14px; padding: 1.3rem 1rem;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.04);
        border: 1px solid #F0F1F3; border-left: 4px solid #00B4D8;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 6px 24px rgba(0,0,0,0.08); }
    .kpi-value { font-size: 2rem; font-weight: 700; color: #0E86D4; line-height: 1.1; }
    .kpi-label { font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 0.4rem; font-weight: 600; }

    /* ══ BADGES ════════════════════════════════════════════ */
    .badge { display: inline-block; padding: 0.22rem 0.7rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-brouillon { background: #F1F5F9; color: #64748B; }
    .badge-soumise   { background: #FFF7ED; color: #C2410C; }
    .badge-attribuee { background: #EFF6FF; color: #1D4ED8; }
    .badge-commandee { background: #F0FDF4; color: #15803D; }
    .badge-annulee   { background: #FEF2F2; color: #B91C1C; }

    /* ══ SECTION HEADERS ══════════════════════════════════ */
    .section-header {
        background: linear-gradient(135deg, #0E86D4 0%, #00B4D8 100%);
        color: #FFFFFF; padding: 0.6rem 1.3rem; border-radius: 10px;
        font-weight: 600; font-size: 0.92rem; margin: 1.5rem 0 1rem 0;
        box-shadow: 0 2px 8px rgba(14,134,212,0.15);
    }

    /* ══ TABLES ════════════════════════════════════════════ */
    .dataframe { font-size: 0.85rem !important; }
    .dataframe th {
        background: #0E86D4 !important; color: #FFFFFF !important;
        font-weight: 600 !important; padding: 0.65rem 0.8rem !important;
    }
    .dataframe td { padding: 0.55rem 0.8rem !important; color: #1E293B !important; background: #FFFFFF !important; }

    /* ══ INFO / ALERTS / CONFIRM ══════════════════════════ */
    .info-box {
        background: #FFFFFF; border-left: 4px solid #00B4D8;
        padding: 1rem 1.3rem; border-radius: 0 12px 12px 0;
        margin: 0.8rem 0; font-size: 0.88rem; color: #334155;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .admin-lock-box {
        background: #FFFFFF; border: 1px solid #F0F1F3; border-radius: 16px;
        padding: 2.5rem; text-align: center; max-width: 420px; margin: 3rem auto;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    }
    .admin-lock-box h3 { color: #0E86D4; margin-bottom: 0.5rem; font-weight: 700; }
    .confirm-box {
        background: #FFFBEB; border: 2px solid #F59E0B; border-radius: 14px;
        padding: 1.5rem; margin: 1rem 0;
    }
    .confirm-box h4 { color: #B45309; margin: 0 0 0.5rem 0; font-weight: 700; }

    @keyframes alert-slide-in { from { transform: translateY(-16px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    .success-alert {
        background: #FFFFFF; border: 2px solid #22C55E; border-radius: 14px;
        padding: 1.3rem 1.8rem; margin: 1rem 0 1.5rem;
        display: flex; align-items: center; gap: 1rem;
        animation: alert-slide-in 0.4s ease-out;
        box-shadow: 0 4px 20px rgba(34,197,94,0.12);
    }
    .success-alert-icon { font-size: 2.2rem; flex-shrink: 0; }
    .success-alert-title { font-size: 1.05rem; font-weight: 700; color: #15803D; margin: 0; }
    .success-alert-msg { font-size: 0.85rem; color: #166534; margin: 0.15rem 0 0; }

    /* ══ SIDEBAR — couleur principale #00538B ══════════════════════════
       Palette de contraste (fond = #00538B, luminosité L≈33%) :
         texte repos     #FFFFFF        ratio ≈ 7.2:1  ✓ AAA
         texte secondaire #E0EFFA       ratio ≈ 5.6:1  ✓ AA
         label section   #B8D8EE       ratio ≈ 4.2:1  ✓ AA
         hover bg        rgba(255,255,255,0.13) → +13% blanc
         actif bg        rgba(255,255,255,0.20) → +20% blanc + barre #7DD3FC
         séparateurs     rgba(255,255,255,0.14)
       ═══════════════════════════════════════════════════════════════ */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] > div:first-child {
        background: #00538B !important;
        padding-top: 0 !important;
    }
    section[data-testid="stSidebar"] > div:first-child > div:first-child {
        margin-top: 0 !important; padding-top: 0 !important;
    }
    button[data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] { display: none !important; pointer-events: none !important; }
    section[data-testid="stSidebar"] {
        min-width: 280px !important; max-width: 300px !important; transform: none !important;
    }
    section[data-testid="stSidebar"] ul[data-testid="stSidebarNavItems"],
    section[data-testid="stSidebar"] nav[data-testid="stSidebarNav"] { display: none !important; }

    /* ── Texte global : blanc pur pour contraste maximal ── */
    section[data-testid="stSidebar"] * { color: #FFFFFF !important; }

    /* ── Brand ── */
    .sidebar-brand {
        background: transparent; margin: 0;
        padding: 1.2rem 1.2rem 0.8rem;
        display: flex; align-items: center; gap: 0.75rem;
        border-bottom: 1px solid rgba(255,255,255,0.14);
        margin-bottom: 0.5rem;
    }
    .sidebar-brand img {
        width: 38px; height: 38px; border-radius: 10px;
        border: 2px solid rgba(255,255,255,0.30);
    }
    .sidebar-brand-text {
        font-weight: 700; font-size: 1rem; line-height: 1.2;
        color: #FFFFFF !important;
    }
    .sidebar-brand-sub {
        font-size: 0.68rem; font-weight: 500;
        letter-spacing: 0.5px; text-transform: uppercase;
        color: #B8D8EE !important;   /* bleu clair très lisible sur #00538B */
    }
    section[data-testid="stSidebar"] .sidebar-brand-text { color: #FFFFFF !important; }
    section[data-testid="stSidebar"] .sidebar-brand-sub  { color: #B8D8EE !important; }

    /* ── Pill utilisateur ── */
    .sidebar-user-pill {
        background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18);
        border-radius: 10px; padding: 0.5rem 0.8rem; margin: 0.6rem 0 0.3rem;
        display: flex; align-items: center; gap: 0.5rem;
    }
    .sidebar-user-dot { width: 7px; height: 7px; border-radius: 50%; background: #4ADE80; flex-shrink: 0; }
    .sidebar-user-email {
        font-size: 0.75rem; font-weight: 600;
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        color: #FFFFFF !important;
    }

    /* ── Bouton Se déconnecter ── */
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.10) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255,255,255,0.22) !important;
        border-radius: 8px !important; font-size: 0.78rem !important; font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.20) !important;
        color: #FFFFFF !important;
        border-color: rgba(255,255,255,0.35) !important;
        transform: none !important; box-shadow: none !important;
    }

    /* ── Label de section "Navigation" ── */
    .sidebar-nav-label {
        font-size: 0.62rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 1.4px; padding: 0.8rem 0 0.3rem 0.3rem;
        color: #B8D8EE !important;   /* bleu clair — distinctif mais lisible */
    }
    section[data-testid="stSidebar"] .sidebar-nav-label { color: #B8D8EE !important; }

    /* ── Liens de navigation — état repos ── */
    section[data-testid="stSidebar"] [data-testid="stPageLink"] { margin-bottom: 2px; width: 100%; }
    section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
        display: block !important; width: 100% !important; border-radius: 8px !important;
        padding: 0.52rem 0.75rem !important;
        font-size: 0.86rem !important; font-weight: 500 !important;
        color: #E0EFFA !important;       /* blanc légèrement teinté bleu — doux mais lisible */
        transition: all 0.15s ease !important;
        border: none !important; text-decoration: none !important;
        background: transparent !important;
        letter-spacing: 0.1px !important;
    }

    /* ── Hover : surbrillance blanche douce ── */
    section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
        background: rgba(255,255,255,0.13) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* ── Élément actif (page courante) ── */
    /* Fond +20% blanc, texte blanc pur, barre gauche cyan vif */
    section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][disabled],
    section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-disabled="true"] {
        background: rgba(255,255,255,0.20) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        box-shadow: inset 3px 0 0 #7DD3FC !important;  /* barre cyan très visible */
        opacity: 1 !important;
    }

    /* ── Cartes stats (En attente / Attribuées…) ── */
    .sidebar-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 0.4rem; margin: 0.7rem 0; }
    .sidebar-stat {
        background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.16);
        border-radius: 8px; padding: 0.45rem 0.5rem; text-align: center;
    }
    .sidebar-stat-val { font-size: 1.1rem; font-weight: 700; line-height: 1.1; }
    .sidebar-stat-lbl {
        font-size: 0.60rem; text-transform: uppercase;
        letter-spacing: 0.5px; font-weight: 600;
        color: #B8D8EE !important;   /* libellé secondaire — distinct de la valeur */
    }
    section[data-testid="stSidebar"] .sidebar-stat-lbl { color: #B8D8EE !important; }

    /* ── Pied de sidebar ── */
    .sidebar-footer {
        margin-top: 1.5rem; padding-top: 0.8rem;
        border-top: 1px solid rgba(255,255,255,0.14);
        text-align: center; font-size: 0.65rem; line-height: 1.6;
        color: #B8D8EE !important;
    }
    section[data-testid="stSidebar"] .sidebar-footer { color: #B8D8EE !important; }

    /* ══ ACCORDION / EXPANDER ═════════════════════════════ */
    .streamlit-expanderHeader {
        background: #FFFFFF !important; border-radius: 10px !important;
        font-weight: 600 !important; color: #0E86D4 !important;
        font-size: 0.92rem !important; border: 1px solid #F0F1F3 !important;
    }
    .streamlit-expanderContent {
        border: 1px solid #F0F1F3 !important; border-top: none !important;
        border-radius: 0 0 10px 10px !important; background: #FFFFFF !important;
    }

    /* ══ BUTTONS ═══════════════════════════════════════════ */
    .stButton > button {
        border-radius: 10px !important; font-weight: 600 !important;
        transition: all 0.2s ease !important; box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
        border: 1px solid transparent !important; color: #1E293B !important;
    }
    .stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 4px 16px rgba(14,134,212,0.2) !important; }
    .stButton > button[kind="primary"] { background: linear-gradient(135deg, #00B4D8, #0E86D4) !important; color: #FFFFFF !important; }
    .stDownloadButton > button {
        border-radius: 10px !important; font-weight: 600 !important;
        border: 1px solid #E2E8F0 !important; background: #FFFFFF !important; color: #0E86D4 !important;
    }
    .stDownloadButton > button:hover { background: #F8FAFC !important; border-color: #00B4D8 !important; color: #00B4D8 !important; }

    /* ══ FORM INPUTS — forced light bg + dark text ════════ */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input {
        border-radius: 10px !important; border-color: #E2E8F0 !important;
        background: #FFFFFF !important; color: #1E293B !important;
    }
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        border-radius: 10px !important; border-color: #E2E8F0 !important;
        background: #FFFFFF !important; color: #1E293B !important;
    }
    /* Dropdown menu items — light bg */
    [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] {
        background: #FFFFFF !important;
    }
    [data-baseweb="menu"] li, [role="option"] {
        color: #1E293B !important; background: #FFFFFF !important;
    }
    [data-baseweb="menu"] li:hover, [role="option"]:hover {
        background: #EEF2F6 !important;
    }
    /* Input labels */
    .stTextInput label, .stTextArea label, .stSelectbox label,
    .stMultiSelect label, .stNumberInput label, .stDateInput label,
    .stCheckbox label, .stRadio label {
        color: #1E293B !important; font-weight: 500 !important;
    }
    /* Focus ring */
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #00B4D8 !important; box-shadow: 0 0 0 2px rgba(14,134,212,0.15) !important;
    }

    /* ══ FORM ERROR HIGHLIGHT ═════════════════════════════ */
    .field-error .stTextInput > div > div > input,
    .field-error .stSelectbox > div > div {
        border-color: #EF4444 !important; box-shadow: 0 0 0 2px rgba(239,68,68,0.15) !important;
    }

    /* ══ METRICS ══════════════════════════════════════════ */
    [data-testid="stMetric"] {
        background: #FFFFFF; border: 1px solid #F0F1F3; border-radius: 12px;
        padding: 1rem 1.2rem !important; box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    [data-testid="stMetricLabel"] { font-size: 0.72rem !important; font-weight: 600 !important; color: #94A3B8 !important; text-transform: uppercase; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 700 !important; color: #0E86D4 !important; }

    /* ══ TABS ═════════════════════════════════════════════ */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; background: #FFFFFF; border-radius: 10px; padding: 4px; border: 1px solid #F0F1F3; }
    .stTabs [data-baseweb="tab"] { font-weight: 600 !important; color: #64748B !important; border-radius: 8px !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background: #EFF6FF !important; color: #00B4D8 !important; }

    /* ══ DATAFRAME / CHARTS ═══════════════════════════════ */
    [data-testid="stDataFrame"] { border-radius: 12px !important; border: 1px solid #F0F1F3 !important; overflow: hidden; }
    .stPlotlyChart { background: #FFFFFF; border-radius: 14px; border: 1px solid #F0F1F3; padding: 0.5rem; }

    /* ══ HIDE BRANDING ════════════════════════════════════ */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# HEADER / KPI / SMALL COMPONENTS — unchanged logic
# ══════════════════════════════════════════════════════════════════════

def render_header(subtitle=""):
    logo_b64 = ""
    if os.path.exists(LOGO_PATH):
        import base64
        with open(LOGO_PATH, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
    st.markdown(f"""
    <div class="rte-header">
        <img src="data:image/png;base64,{logo_b64}" alt="RTE">
        <div><h1>Guichet Unique — Demandes d'Etudes</h1><p>{subtitle}</p></div>
    </div>
    """, unsafe_allow_html=True)


def render_kpi_cards(kpi: dict):
    cols = st.columns(6)
    items = [
        ("total", "Total Demandes", "#0E86D4"), ("brouillon", "Brouillons", "#94A3B8"),
        ("soumises", "Soumises", "#F59E0B"), ("attribuees", "Attribuees", "#00B4D8"),
        ("commandees", "Commandees", "#22C55E"), ("annulees", "Annulees", "#EF4444"),
    ]
    for col, (key, label, color) in zip(cols, items):
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: {color};">
                <div class="kpi-value" style="color: {color};">{kpi[key]}</div>
                <div class="kpi-label">{label}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


def render_taux_cards(kpi: dict):
    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        st.markdown(f"""<div class="kpi-card" style="border-left-color: #00B4D8;">
            <div class="kpi-value" style="color: #00B4D8;">{kpi['taux_attribution']}%</div>
            <div class="kpi-label">Taux d'attribution</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="kpi-card" style="border-left-color: #22C55E;">
            <div class="kpi-value" style="color: #22C55E;">{kpi['taux_commande']}%</div>
            <div class="kpi-label">Taux de commande</div></div>""", unsafe_allow_html=True)


def section_header(title: str, icon: str = ""):
    st.markdown(f'<div class="section-header">{icon} {title}</div>', unsafe_allow_html=True)

def status_badge(statut: str) -> str:
    css_class = {"Brouillon": "badge-brouillon", "Soumise": "badge-soumise", "Attribuée": "badge-attribuee", "Commandée": "badge-commandee", "Annulée": "badge-annulee"}.get(statut, "badge-brouillon")
    return f'<span class="badge {css_class}">{statut}</span>'

def info_box(text: str):
    st.markdown(f'<div class="info-box">{text}</div>', unsafe_allow_html=True)

def clean_select(val: str) -> str:
    return "" if val == PLACEHOLDER else val

def show_success_alert(title: str, message: str):
    st.markdown(f"""<div class="success-alert">
        <div class="success-alert-icon">✅</div>
        <div><p class="success-alert-title">{title}</p><p class="success-alert-msg">{message}</p></div>
    </div>""", unsafe_allow_html=True)

def notify_success(message: str):
    st.toast(message, icon="✅")

def notify_error(message: str):
    st.toast(message, icon="❌")


# ══════════════════════════════════════════════════════════════════════
# FRISE D'ATTRIBUTION TRIMESTRIELLE
# ══════════════════════════════════════════════════════════════════════
#
# POURQUOI LE HTML S'AFFICHAIT COMME DU TEXTE
# ─────────────────────────────────────────────────────────────────────
# Streamlit's st.markdown(..., unsafe_allow_html=True) PEUT afficher le
# HTML brut (balises visibles, styles en clair) dans deux cas courants :
#
#   1. F-strings multilignes avec CSS inline complexe : le parser
#      Markdown de Streamlit (mistune) peut interpréter certains blocs
#      comme du code ou du texte brut au lieu de HTML, surtout quand
#      les chaînes contiennent des guillemets imbriqués ou des sauts
#      de ligne à l'intérieur d'attributs style="...".
#
#   2. Streamlit 1.31+ renforce la sanitisation HTML dans st.markdown ;
#      des divs avec de longues propriétés CSS inline peuvent être
#      échappés par sécurité.
#
# CORRECTION APPLIQUÉE
# ─────────────────────────────────────────────────────────────────────
# On utilise st.components.v1.html(html_content, height=N) qui injecte
# le HTML dans un <iframe> isolé. Ce composant ne passe PAS par le
# parser Markdown : il reçoit du HTML pur et l'affiche tel quel, sans
# aucune sanitisation ni interprétation Markdown. C'est la méthode
# officielle Streamlit pour les composants HTML riches.
# ══════════════════════════════════════════════════════════════════════

def render_frise_attribution():
    """
    Affiche la frise des attributions trimestrielles sous forme de cartes
    visuelles alignées horizontalement, avec légende et texte explicatif.

    ─────────────────────────────────────────────────────────────────────
    SOURCE DE DONNÉES : get_attribution_calendar() (data_manager.py)
    ─────────────────────────────────────────────────────────────────────
    Cette fonction ne contient PLUS aucune logique de calcul de trimestres.
    Toute la logique métier est centralisée dans get_attribution_calendar().
    C'est la même fonction qui alimente le formulaire 1_Nouvelle_Demande.py,
    garantissant une cohérence parfaite entre la frise et les choix proposés.

    Rendu via st.components.v1.html() — PAS st.markdown(unsafe_allow_html)
    car le parser Markdown peut afficher les balises brutes pour du HTML
    complexe. components.html() injecte dans un <iframe> isolé, sans
    sanitisation, rendu garanti par le navigateur.

    Hauteur iframe : 290 px (voir décomposition en commentaire inline).
    """
    import streamlit.components.v1 as components
    from data_manager import get_attribution_calendar

    cal                      = get_attribution_calendar()
    quarters                 = cal["quarters"]
    current_y, current_q     = cal["current"]
    target_y,  target_q      = cal["target"]
    target_label             = cal["target_label"]
    q_months                 = cal["q_months"]

    # ── Cartes HTML ──────────────────────────────────────────────────
    cards_html = []
    for y, q in quarters:
        label   = f"T{q} {y}"
        months  = q_months[q]
        is_cur  = (y == current_y and q == current_q)
        is_tgt  = (y == target_y  and q == target_q)
        is_past = (y < current_y) or (y == current_y and q < current_q)

        if is_cur:
            bg, border = "linear-gradient(135deg,#0E86D4,#00B4D8)", "2px solid #0E86D4"
            tc, mc     = "#FFFFFF", "rgba(255,255,255,0.85)"
            badge = '<span class="badge">EN COURS</span>'
        elif is_tgt:
            bg, border = "linear-gradient(135deg,#F59E0B,#FBBF24)", "2px solid #F59E0B"
            tc, mc     = "#FFFFFF", "rgba(255,255,255,0.85)"
            badge = '<span class="badge">PROCHAINE<br>ATTRIBUTION</span>'
        elif is_past:
            bg, border = "#F1F5F9", "1px solid #E2E8F0"
            tc, mc     = "#94A3B8", "#CBD5E1"
            badge      = ""
        else:
            bg, border = "#FFFFFF", "1px solid #E2E8F0"
            tc, mc     = "#1E293B", "#64748B"
            badge      = ""

        badge_block = f'<div style="margin-top:0.4rem;">{badge}</div>' if badge else ""
        cards_html.append(f"""
        <div class="card">
          <div style="background:{bg};border:{border};border-radius:12px;
                      padding:0.85rem 0.6rem;text-align:center;height:100%;
                      box-shadow:0 2px 8px rgba(0,0,0,0.07);box-sizing:border-box;">
            <div style="font-size:1.1rem;font-weight:700;color:{tc};line-height:1.1;">{label}</div>
            <div style="font-size:0.65rem;color:{mc};margin-top:0.25rem;">{months}</div>
            {badge_block}
          </div>
        </div>""")

    frise_cards = "\n".join(cards_html)

    # ── HTML complet ─────────────────────────────────────────────────
    # Hauteur réelle :  padding(10) + titre(30) + texte(44) + marge(12)
    #                 + cartes(110) + scrollbar+marge(14) + légende(28)
    #                 + padding bas(14) = 262 px → height=290 (28 px marge)
    # Pas d'overflow:hidden sur html/body → évite toute troncature.
    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    background: transparent;
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    padding: 10px 2px 14px 2px;
  }}
  .frise-title {{ font-size:0.95rem; font-weight:700; color:#1E293B; margin-bottom:5px; }}
  .frise-info  {{ font-size:0.80rem; color:#64748B; line-height:1.45; margin-bottom:10px; }}
  .frise-info b {{ color:#D97706; }}
  .cards-row {{
    display:flex; gap:7px;
    overflow-x:auto; overflow-y:visible;
    align-items:stretch; padding-bottom:6px;
  }}
  .card {{ flex:1 1 0; min-width:115px; }}
  .cards-row::-webkit-scrollbar       {{ height:3px; }}
  .cards-row::-webkit-scrollbar-track {{ background:#F1F5F9; border-radius:4px; }}
  .cards-row::-webkit-scrollbar-thumb {{ background:#CBD5E1; border-radius:4px; }}
  .badge {{
    display:inline-block; font-size:0.55rem; font-weight:700;
    letter-spacing:0.4px; border-radius:20px; padding:0.18rem 0.5rem;
    line-height:1.5; background:rgba(255,255,255,0.28); color:#fff;
  }}
  .legend {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:10px; align-items:center; }}
  .legend-item {{ display:flex; align-items:center; gap:5px; font-size:0.70rem; color:#475569; }}
  .legend-dot {{ width:10px; height:10px; border-radius:3px; flex-shrink:0; }}
</style></head>
<body>
  <div class="frise-title">&#128197; Frise des attributions trimestrielles</div>
  <div class="frise-info">
    Si vous d&eacute;posez une demande aujourd'hui, elle sera attribu&eacute;e lors de la
    <b>prochaine attribution trimestrielle &mdash; {target_label}</b>.
  </div>
  <div class="cards-row">{frise_cards}</div>
  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#94A3B8;"></div>Trimestre pass&eacute;</div>
    <div class="legend-item"><div class="legend-dot" style="background:linear-gradient(135deg,#0E86D4,#00B4D8);"></div>En cours</div>
    <div class="legend-item"><div class="legend-dot" style="background:linear-gradient(135deg,#F59E0B,#FBBF24);"></div>Prochaine attribution</div>
    <div class="legend-item"><div class="legend-dot" style="background:#E2E8F0;border:1px solid #CBD5E1;"></div>Trimestre futur</div>
  </div>
</body></html>"""

    # st.components.v1.html() → iframe isolé, hors parser Markdown.
    # height=290 : voir décomposition ci-dessus. scrolling=False : pas de
    # double scrollbar verticale.
    components.html(html_content, height=290, scrolling=False)


def export_excel_button(df: pd.DataFrame, filename="export.xlsx", sheet_name="Donnees", label="📥 Exporter en Excel", key=None):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        wb = writer.book; ws = writer.sheets[sheet_name]
        hfmt = wb.add_format({"bold": True, "bg_color": "#0E86D4", "font_color": "#FFFFFF", "border": 1, "text_wrap": True, "valign": "vcenter", "font_name": "Arial", "font_size": 10})
        for i, v in enumerate(df.columns):
            ws.write(0, i, v, hfmt)
            max_len = max(len(str(v)), df.iloc[:, i].astype(str).str.len().max() if len(df) > 0 else 0)
            ws.set_column(i, i, min(max_len + 4, 40))
    st.download_button(label=label, data=buffer.getvalue(), file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=key)


# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════

def render_sidebar(active_page: str = "dashboard"):
    import base64 as _b64
    from data_manager import load_data, get_kpi
    from auth import get_current_user, logout

    if "utilisateur" not in st.session_state:
        st.session_state["utilisateur"] = "Systeme"

    with st.sidebar:
        logo_b64 = ""
        if os.path.exists(LOGO_PATH):
            with open(LOGO_PATH, "rb") as f:
                logo_b64 = _b64.b64encode(f.read()).decode()
        st.markdown(f"""<div class="sidebar-brand">
            <img src="data:image/png;base64,{logo_b64}" alt="RTE">
            <div><div class="sidebar-brand-text">Guichet Unique</div>
            <div class="sidebar-brand-sub">Demandes d'Etudes</div></div>
        </div>""", unsafe_allow_html=True)

        user = get_current_user()
        if user:
            email = user["email"]
            admin_tag = " · admin" if user.get("is_admin") else ""
            st.markdown(f"""<div class="sidebar-user-pill">
                <div class="sidebar-user-dot"></div>
                <div class="sidebar-user-email">{email}{admin_tag}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Se deconnecter", key="btn_logout", use_container_width=True):
                logout(); st.rerun()
        else:
            st.markdown("""<div class="sidebar-user-pill" style="border-color: rgba(245,158,11,0.3);">
                <div class="sidebar-user-dot" style="background: #F59E0B;"></div>
                <div class="sidebar-user-email">Non connecte</div>
            </div>""", unsafe_allow_html=True)

        df = load_data(); kpi = get_kpi(df)
        st.markdown(f"""<div class="sidebar-stats">
            <div class="sidebar-stat"><div class="sidebar-stat-val" style="color:#F59E0B !important;">{kpi['soumises']}</div><div class="sidebar-stat-lbl">En attente</div></div>
            <div class="sidebar-stat"><div class="sidebar-stat-val" style="color:#38BDF8 !important;">{kpi['attribuees']}</div><div class="sidebar-stat-lbl">Attribuees</div></div>
            <div class="sidebar-stat"><div class="sidebar-stat-val" style="color:#4ADE80 !important;">{kpi['commandees']}</div><div class="sidebar-stat-lbl">Commandees</div></div>
            <div class="sidebar-stat"><div class="sidebar-stat-val" style="color:#FFFFFF !important;">{kpi['total']}</div><div class="sidebar-stat-lbl">Total</div></div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="sidebar-nav-label">Navigation</div>', unsafe_allow_html=True)
        nav_items = [
            ("dashboard", "🏠  Tableau de bord"), ("nouvelle", "➕  Nouvelle demande"),
            ("demandes", "📋  Mes demandes"), ("attribution", "🔒  Attribution"),
            ("import", "🔒  Import commandes"), ("donnees", "📊  Donnees"),
            ("suivi", "📈  Suivi & analyses"), ("modop", "📖  ModOp"),
        ]
        for key, label in nav_items:
            st.page_link(PAGE_PATHS[key], label=label, disabled=(key == active_page))

        from config import APP_VERSION
        st.markdown(f'<div class="sidebar-footer">Guichet Unique v{APP_VERSION}<br>RTE</div>', unsafe_allow_html=True)
