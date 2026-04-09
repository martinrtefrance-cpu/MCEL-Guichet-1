"""
4_Import_Commandes.py — Importer une extraction Excel pour rapprocher les commandes.
"""
import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data_manager import load_data, importer_commandes
from ui_components import (
    inject_css, render_header, section_header, info_box,
    render_sidebar, export_excel_button, notify_success, PLACEHOLDER,
)
from auth import require_auth, check_admin_access

st.set_page_config(page_title="Import Commandes", page_icon="📦", layout="wide", initial_sidebar_state="expanded")
inject_css()
render_sidebar(active_page="import")
user = require_auth()
render_header("Import des commandes — Rapprochement automatique")

# Protection admin — même mécanisme que la page Attribution
if not check_admin_access():
    st.stop()

info_box(
    "📥 Importez ici l'extraction Excel provenant de votre système de commandes. "
    "L'outil rapprochera automatiquement les commandes avec les demandes existantes "
    "en utilisant le code <b>EOTP2</b> comme clé de rapprochement."
)

# ── Upload ────────────────────────────────────────────────────────────
section_header("1. Charger le fichier", "📁")
uploaded = st.file_uploader(
    "Glissez ou sélectionnez votre fichier Excel de commandes",
    type=["xlsx", "xls", "csv"],
    help="Formats acceptés : .xlsx, .xls, .csv"
)

if uploaded:
    try:
        if uploaded.name.endswith(".csv"):
            df_import = pd.read_csv(uploaded, dtype=str)
        else:
            df_import = pd.read_excel(uploaded, dtype=str)

        st.success(f"✅ Fichier chargé : **{uploaded.name}** — {len(df_import)} lignes, {len(df_import.columns)} colonnes")

        section_header("2. Aperçu des données importées", "👁️")
        st.dataframe(df_import.head(20), use_container_width=True, height=300)

        section_header("3. Mapper les colonnes", "🔗")
        info_box(
            "Indiquez quelle colonne de votre fichier correspond à chaque champ. "
            "Le champ <b>EOTP2</b> est obligatoire pour le rapprochement."
        )

        cols_import = [PLACEHOLDER] + list(df_import.columns)

        c1, c2 = st.columns(2)
        with c1:
            col_eotp = st.selectbox("Colonne EOTP2 (clé de rapprochement) *", cols_import, key="map_eotp")
            col_num = st.selectbox("Colonne N° de commande", cols_import, key="map_num")
        with c2:
            col_date = st.selectbox("Colonne Date de commande", cols_import, key="map_date")
            col_montant = st.selectbox("Colonne Montant de commande", cols_import, key="map_montant")

        if not col_eotp or col_eotp == PLACEHOLDER:
            st.warning("⚠️ Sélectionnez au minimum la colonne EOTP2 pour procéder.")
            st.stop()

        col_mapping = {"EOTP2": col_eotp}
        if col_num:
            col_mapping["Commande_Numero"] = col_num
        if col_date:
            col_mapping["Commande_Date"] = col_date
        if col_montant:
            col_mapping["Commande_Montant"] = col_montant

        section_header("4. Pré-vérification", "🔍")
        db = load_data()
        eotp_import = set(df_import[col_eotp].dropna().unique())
        eotp_db = set(db["EOTP2"].dropna().unique())
        matched = eotp_import & eotp_db
        unmatched = eotp_import - eotp_db

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Lignes importées", len(df_import))
        with c2:
            st.metric("Rapprochements possibles", len(matched))
        with c3:
            st.metric("Non trouvées", len(unmatched))

        if unmatched:
            with st.expander(f"📋 {len(unmatched)} EOTP2 non trouvées dans la base"):
                for e in sorted(unmatched):
                    st.text(f"  • {e}")

        # ── Import ────────────────────────────────────────────────────
        section_header("5. Lancer l'import", "🚀")
        st.warning(
            f"**{len(matched)}** demandes seront mises à jour et passeront au statut **Commandée**. "
            "Cette action est enregistrée dans l'historique."
        )

        if st.button("📦 Lancer le rapprochement", type="primary", use_container_width=True):
            stats = importer_commandes(df_import, col_mapping, user["email"])
            notify_success(
                f"Import terminé — {stats['matched']} demandes mises à jour, "
                f"{stats['unmatched']} non rapprochées."
            )
            st.success(
                f"✅ Import terminé ! **{stats['matched']}** demandes mises à jour, "
                f"**{stats['unmatched']}** non rapprochées."
            )

    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
else:
    # État actuel des commandes + export
    section_header("État actuel des commandes", "📊")
    db = load_data()
    commandees = db[db["Statut"] == "Commandée"]
    attribuees = db[db["Statut"] == "Attribuée"]

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Demandes commandées", len(commandees))
    with c2:
        st.metric("Attribuées (en attente de commande)", len(attribuees))

    if len(commandees) > 0:
        cmd_cols = ["ID_Demande", "Nom_Ouvrage_Projet", "Attribution_Finale",
                    "Commande_Numero", "Commande_Date", "Commande_Montant"]
        cmd_cols = [c for c in cmd_cols if c in commandees.columns]
        st.dataframe(commandees[cmd_cols].head(20), use_container_width=True)
        export_excel_button(commandees[cmd_cols], "commandes.xlsx", "Commandes", key="export_cmd")
