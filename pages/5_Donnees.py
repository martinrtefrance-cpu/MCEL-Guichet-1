"""
5_Donnees.py — Vue complète des données + bouton relance manager par email.
"""
import streamlit as st
import pandas as pd
import io
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data_manager import (
    load_user_data, STATUTS, TRIMESTRES,
    COLONNES_INFO_GENERALES, COLONNES_TECH_LA, COLONNES_TECH_LS,
    COLONNES_JALONS, COLONNES_MONTANT,
    COLONNES_PREFERENCE, COLONNES_ATTRIBUTION,
    COLONNES_COMMANDE, COLONNES_HISTORIQUE,
)
from ui_components import (
    inject_css, render_header, section_header, info_box,
    render_sidebar, export_excel_button, notify_success, notify_error,
    status_badge,
)
from auth import require_auth
from email_service import send_relance_email

st.set_page_config(page_title="Données", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
inject_css()
render_sidebar(active_page="donnees")
user = require_auth()
render_header("Données complètes — Consultation et export")

df = load_user_data(user["email"], user.get("is_admin", False))

if len(df) == 0:
    info_box("Aucune donnée disponible.")
    st.stop()

# ── Filtres ───────────────────────────────────────────────────────────
section_header("Filtres", "🔍")
c1, c2, c3, c4 = st.columns(4)
with c1:
    f_statut = st.multiselect("Statut", STATUTS)
with c2:
    f_trim = st.multiselect("Trimestre", TRIMESTRES)
with c3:
    f_manager = st.text_input("Manager")
with c4:
    f_projet = st.text_input("Nom du projet")

mask = pd.Series([True] * len(df), index=df.index)
if f_statut:
    mask &= df["Statut"].isin(f_statut)
if f_trim:
    mask &= df["Trimestre_Attribution"].isin(f_trim)
if f_manager:
    mask &= df["Manager_Projet"].str.contains(f_manager, case=False, na=False)
if f_projet:
    mask &= df["Nom_Ouvrage_Projet"].str.contains(f_projet, case=False, na=False)

filtered = df[mask].copy()
st.markdown(f"**{len(filtered)}** demande(s) trouvée(s)")

# ── Sélection des colonnes ───────────────────────────────────────────
section_header("Sélection des colonnes", "📋")

col_groups = {
    "📋 Informations générales": COLONNES_INFO_GENERALES,
    "🗼 Technique LA": COLONNES_TECH_LA,
    "🔌 Technique LS": COLONNES_TECH_LS,
    "📅 Jalons": COLONNES_JALONS,
    "💰 Montants": COLONNES_MONTANT,
    "🎯 Préférences": COLONNES_PREFERENCE,
    "🏢 Attribution": COLONNES_ATTRIBUTION,
    "📦 Commandes": COLONNES_COMMANDE,
    "📜 Historique": COLONNES_HISTORIQUE,
}

selected_groups = st.multiselect(
    "Groupes de colonnes à afficher",
    list(col_groups.keys()),
    default=["📋 Informations générales", "🏢 Attribution", "💰 Montants"],
)

selected_cols = []
for g in selected_groups:
    selected_cols.extend(col_groups[g])
selected_cols = [c for c in selected_cols if c in filtered.columns]

if not selected_cols:
    st.info("Sélectionnez au moins un groupe de colonnes.")
    st.stop()

# ── Tableau interactif ────────────────────────────────────────────────
section_header("Données", "📊")

def color_statut(val):
    colors = {
        "Brouillon": "background-color: #E0E0E0", "Soumise": "background-color: #FFF3E0",
        "Attribuée": "background-color: #E3F2FD", "Commandée": "background-color: #E8F5E9",
        "Annulée": "background-color: #FFEBEE",
    }
    return colors.get(val, "")

display_df = filtered[selected_cols].copy()

# Coloration du statut — compatible pandas 2.1+ (applymap supprimé → map)
if "Statut" in display_df.columns:
    styled = display_df.style.map(color_statut, subset=["Statut"])
    st.dataframe(styled, use_container_width=True, height=500)
else:
    st.dataframe(display_df, use_container_width=True, height=500)

# ── Export ────────────────────────────────────────────────────────────
section_header("Export", "💾")
c1, c2 = st.columns(2)
with c1:
    export_excel_button(display_df, "guichet_unique_export.xlsx", "Demandes", key="export_donnees_xl")
with c2:
    csv_data = display_df.to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button(
        "📥 Télécharger en CSV", data=csv_data.encode("utf-8-sig"),
        file_name="guichet_unique_export.csv", mime="text/csv",
        use_container_width=True, key="export_donnees_csv",
    )

# ── Statistiques rapides ─────────────────────────────────────────────
section_header("Statistiques rapides", "📈")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Total affiché", len(display_df))
with c2:
    if "Montant_Total" in display_df.columns:
        try:
            total_montant = pd.to_numeric(display_df["Montant_Total"], errors="coerce").sum()
            st.metric("Montant total (k€)", f"{total_montant:,.1f}")
        except Exception:
            st.metric("Montant total (k€)", "N/A")
with c3:
    if "Statut" in display_df.columns:
        st.markdown("**Par statut :**")
        for s, count in display_df["Statut"].value_counts().items():
            st.markdown(f"- {s}: **{count}**")

# ══════════════════════════════════════════════════════════════════════
# RELANCE MANAGER — bouton d'envoi d'email pour les demandes sans commande
# ══════════════════════════════════════════════════════════════════════
section_header("Relance des managers", "📧")

# Demandes attribuées mais pas encore commandées = cibles de relance
relancables = filtered[
    (filtered["Statut"] == "Attribuée") &
    (filtered["Commande_Statut"].isna() | (filtered["Commande_Statut"] == ""))
].copy() if "Commande_Statut" in filtered.columns else filtered[
    filtered["Statut"] == "Attribuée"
].copy()

if len(relancables) == 0:
    info_box("Aucune demande à relancer — toutes les demandes attribuées ont une commande ou aucune n'est attribuée.")
else:
    st.markdown(f"**{len(relancables)}** demande(s) attribuée(s) sans commande :")

    for idx, row in relancables.iterrows():
        dem_id = str(row.get("ID_Demande", ""))
        projet = str(row.get("Nom_Ouvrage_Projet", "N/A"))
        manager_name = str(row.get("Manager_Projet", ""))
        tel_manager = str(row.get("Tel_Manager", ""))
        statut = str(row.get("Statut", ""))

        with st.container():
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                st.markdown(
                    f"**{projet}** · `{dem_id}`<br>"
                    f"<span style='color:#6B7280;font-size:0.85rem;'>Manager : {manager_name}</span>",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(status_badge(statut), unsafe_allow_html=True)
            with c3:
                # Bouton relance par demande
                btn_key = f"relance_{dem_id}"
                if st.button("📧 Relancer", key=btn_key):
                    # Construire un email à partir du nom du manager
                    # Logique simple : prénom.nom@rte-france.com
                    parts = manager_name.strip().split()
                    if len(parts) >= 2:
                        to_email = f"{parts[0].lower()}.{parts[-1].lower()}@rte-france.com"
                    elif tel_manager and "@" in str(tel_manager):
                        to_email = str(tel_manager)
                    else:
                        to_email = ""

                    if not to_email:
                        notify_error(f"Impossible de déterminer l'email pour {manager_name}")
                    else:
                        demande_dict = row.to_dict()
                        result = send_relance_email(to_email, demande_dict, manager_name)
                        if result["success"]:
                            if result.get("simulated"):
                                st.info(result["message"])
                            else:
                                notify_success(f"Email envoyé à {to_email}")
                        else:
                            notify_error(result["message"])

            st.markdown("<hr style='margin:0.3rem 0;border:none;border-top:1px solid #E6EDF3;'>", unsafe_allow_html=True)
