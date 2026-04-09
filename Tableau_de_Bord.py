"""
Tableau_de_Bord.py — Page principale : Dashboard KPI + vue d'ensemble.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from data_manager import load_data, get_kpi, STATUTS_COLORS
from ui_components import (
    inject_css, render_header, render_kpi_cards, render_taux_cards,
    section_header, status_badge, info_box, render_sidebar, export_excel_button,
    render_frise_attribution,  # composant frise — rendu via st.components.v1.html()
)

st.set_page_config(
    page_title="Guichet Unique RTE", page_icon="⚡",
    layout="wide", initial_sidebar_state="expanded",
)
inject_css()
render_sidebar(active_page="dashboard")
render_header("Tableau de bord — Vue d'ensemble des demandes d'études")

df = load_data()
kpi = get_kpi(df)

render_kpi_cards(kpi)
render_taux_cards(kpi)

# ══════════════════════════════════════════════════════════════════════
# FRISE D'ATTRIBUTION TRIMESTRIELLE
# ══════════════════════════════════════════════════════════════════════
# Le rendu HTML de la frise est délégué à render_frise_attribution()
# dans ui_components.py, qui utilise st.components.v1.html() pour
# garantir que le HTML est interprété comme visuel et non affiché brut.
# (Voir ui_components.py pour l'explication complète du bug corrigé.)
render_frise_attribution()



if len(df) == 0:
    info_box(
        "🚀 <b>Bienvenue dans le Guichet Unique !</b><br>"
        "Aucune demande n'a encore été enregistrée. "
        "Cliquez sur <b>➕ Nouvelle Demande</b> dans le menu de gauche pour commencer."
    )
    st.stop()

# ── Graphiques ────────────────────────────────────────────────────────
section_header("Répartition des demandes", "📊")

col1, col2 = st.columns(2)

with col1:
    statut_counts = df["Statut"].value_counts().reset_index()
    statut_counts.columns = ["Statut", "Nombre"]
    fig_pie = px.pie(
        statut_counts, values="Nombre", names="Statut",
        color="Statut", color_discrete_map=STATUTS_COLORS, hole=0.45,
    )
    fig_pie.update_layout(
        paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF',
        margin=dict(t=30, b=0, l=0, r=0),
        font=dict(family="Source Sans 3"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        height=320,
    )
    fig_pie.update_traces(textposition='inside', textinfo='value+label')
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    if df["Trimestre_Attribution"].notna().any() and (df["Trimestre_Attribution"] != "").any():
        trim_counts = df[df["Trimestre_Attribution"] != ""]["Trimestre_Attribution"].value_counts().sort_index().reset_index()
        trim_counts.columns = ["Trimestre", "Nombre"]
        fig_bar = px.bar(trim_counts, x="Trimestre", y="Nombre", color_discrete_sequence=["#00B2E3"])
        fig_bar.update_layout(
            paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF',
            margin=dict(t=30, b=0, l=0, r=0),
            font=dict(family="Source Sans 3"),
            xaxis_title="", yaxis_title="Nombre de demandes", height=320,
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Pas encore de données par trimestre.")

# ── Attribution par GIE ───────────────────────────────────────────────
section_header("Attributions par entreprise d'études", "🏢")

attribuees = df[df["Statut"].isin(["Attribuée", "Commandée"])]
if len(attribuees) > 0 and (attribuees["Attribution_Finale"] != "").any():
    gie_counts = attribuees["Attribution_Finale"].value_counts().reset_index()
    gie_counts.columns = ["Entreprise", "Nombre"]
    fig_gie = px.bar(gie_counts, x="Entreprise", y="Nombre", color_discrete_sequence=["#005F83"])
    fig_gie.update_layout(
        paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF',
        margin=dict(t=10, b=0, l=0, r=0),
        font=dict(family="Source Sans 3"),
        xaxis_title="", yaxis_title="Nombre", height=280,
    )
    st.plotly_chart(fig_gie, use_container_width=True)
else:
    st.info("Aucune attribution réalisée pour le moment.")

# ── Montants par trimestre et entreprise ──────────────────────────────
section_header("Montants estimés par trimestre et entreprise", "💰")

df["_montant"] = pd.to_numeric(df["Montant_Total"], errors="coerce").fillna(0)
df_with_trim = df[
    (df["Trimestre_Attribution"].notna()) & (df["Trimestre_Attribution"] != "")
].copy()

if len(df_with_trim) > 0 and df_with_trim["_montant"].sum() > 0:
    # Remplacer les entreprises vides par "Non attribuée" pour la lisibilité
    df_with_trim["_entreprise"] = df_with_trim["Attribution_Finale"].apply(
        lambda x: x if pd.notna(x) and str(x).strip() else "Non attribuée"
    )
    # Agréger par trimestre + entreprise
    chart_data = df_with_trim.groupby(
        ["Trimestre_Attribution", "_entreprise"], as_index=False
    )["_montant"].sum()
    chart_data.columns = ["Trimestre", "Entreprise", "Montant (k€)"]

    # Couleurs : une par entreprise, gris pour "Non attribuée"
    entreprises = sorted(chart_data["Entreprise"].unique())
    palette = ["#005F83", "#00B2E3", "#FF9800", "#4CAF50", "#9C27B0", "#E91E63"]
    color_map = {}
    color_idx = 0
    for ent in entreprises:
        if ent == "Non attribuée":
            color_map[ent] = "#BDBDBD"
        else:
            color_map[ent] = palette[color_idx % len(palette)]
            color_idx += 1

    fig_montant = px.bar(
        chart_data, x="Trimestre", y="Montant (k€)", color="Entreprise",
        color_discrete_map=color_map, barmode="group",
    )
    fig_montant.update_layout(
        paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF',
        margin=dict(t=10, b=0, l=0, r=0),
        font=dict(family="Source Sans 3"),
        xaxis_title="", yaxis_title="Montant (k€)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        height=360,
    )
    st.plotly_chart(fig_montant, use_container_width=True)
else:
    st.info("Pas encore de données de montants par trimestre.")

# Nettoyage colonne temporaire
df.drop(columns=["_montant"], inplace=True, errors="ignore")

# ── Dernières demandes + export Excel ─────────────────────────────────
section_header("Dernières demandes", "🕐")

recent = df.sort_values("Date_Creation", ascending=False).head(10)
display_cols = ["ID_Demande", "Statut", "Nom_Ouvrage_Projet", "Manager_Projet",
                "Trimestre_Attribution", "Tension", "Date_Creation"]
display_cols = [c for c in display_cols if c in recent.columns]

nice_names = {
    "ID_Demande": "ID", "Statut": "Statut", "Nom_Ouvrage_Projet": "Projet",
    "Manager_Projet": "Manager", "Trimestre_Attribution": "Trimestre",
    "Tension": "Tension", "Date_Creation": "Créé le",
}

# HTML table
html = '<table style="width:100%; border-collapse: collapse; font-size: 0.85rem;">'
html += '<tr>'
for c in display_cols:
    html += f'<th style="background:#005F83; color:white; padding:8px 12px; text-align:left;">{nice_names.get(c,c)}</th>'
html += '</tr>'
for _, row in recent.iterrows():
    html += '<tr style="border-bottom: 1px solid #E0E0E0;">'
    for c in display_cols:
        val = str(row.get(c, ""))
        if c == "Statut":
            val = status_badge(val)
        if c == "ID_Demande":
            val = f'<code style="color:#005F83; font-weight:600;">{val}</code>'
        html += f'<td style="padding:8px 12px;">{val}</td>'
    html += '</tr>'
html += '</table>'
st.markdown(html, unsafe_allow_html=True)

# Bouton export Excel
export_df = recent[display_cols].copy()
export_df.columns = [nice_names.get(c, c) for c in display_cols]
export_excel_button(export_df, "dernieres_demandes.xlsx", "Dernières demandes", key="export_dashboard")
