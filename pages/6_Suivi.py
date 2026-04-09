"""
6_Suivi.py — Tableau de suivi avancé et indicateurs.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data_manager import load_user_data, get_kpi, STATUTS_COLORS, GIE_LIST
from ui_components import inject_css, render_header, section_header, status_badge, info_box, render_sidebar, export_excel_button
from auth import require_auth

st.set_page_config(page_title="Suivi", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
inject_css()
render_sidebar(active_page="suivi")
user = require_auth()
render_header("Suivi avancé — Indicateurs et analyses")

df = load_user_data(user["email"], user.get("is_admin", False))

if len(df) == 0:
    info_box("Aucune donnée disponible pour le suivi.")
    st.stop()

kpi = get_kpi(df)

# ── Entonnoir de conversion ──────────────────────────────────────────
section_header("Entonnoir de conversion", "🔄")

funnel_data = pd.DataFrame({
    "Étape": ["Total", "Soumises", "Attribuées", "Commandées"],
    "Nombre": [
        kpi["total"],
        kpi["soumises"] + kpi["attribuees"] + kpi["commandees"],
        kpi["attribuees"] + kpi["commandees"],
        kpi["commandees"],
    ]
})

fig_funnel = go.Figure(go.Funnel(
    y=funnel_data["Étape"],
    x=funnel_data["Nombre"],
    marker=dict(color=["#005F83", "#FF9800", "#2196F3", "#4CAF50"]),
    textposition="inside",
    textinfo="value+percent initial",
    connector=dict(line=dict(color="#E0E0E0")),
))
fig_funnel.update_layout(
    margin=dict(t=10, b=10, l=10, r=10),
    font=dict(family="Source Sans 3", size=14),
    height=300,
)
st.plotly_chart(fig_funnel, use_container_width=True)

# ── Montants par statut ──────────────────────────────────────────────
section_header("Montants par statut", "💰")

df["_montant"] = pd.to_numeric(df["Montant_Total"], errors="coerce").fillna(0)

montant_statut = df.groupby("Statut")["_montant"].sum().reset_index()
montant_statut.columns = ["Statut", "Montant (k€)"]

fig_montant = px.bar(
    montant_statut, x="Statut", y="Montant (k€)",
    color="Statut", color_discrete_map=STATUTS_COLORS,
    text_auto=True,
)
fig_montant.update_layout(
    margin=dict(t=10, b=10), font=dict(family="Source Sans 3"),
    showlegend=False, height=320,
)
st.plotly_chart(fig_montant, use_container_width=True)

# ── Répartition par tension ──────────────────────────────────────────
section_header("Répartition par tension", "⚡")

c1, c2 = st.columns(2)
with c1:
    tension_counts = df[df["Tension"] != ""]["Tension"].value_counts().reset_index()
    tension_counts.columns = ["Tension", "Nombre"]
    if len(tension_counts) > 0:
        fig_tension = px.pie(tension_counts, values="Nombre", names="Tension", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Set2)
        fig_tension.update_layout(margin=dict(t=10, b=10), font=dict(family="Source Sans 3"), height=300)
        st.plotly_chart(fig_tension, use_container_width=True)
    else:
        st.info("Pas de données par tension.")

with c2:
    # Par type de projet
    type_counts = df[df["Type_Projet"] != ""]["Type_Projet"].value_counts().reset_index()
    type_counts.columns = ["Type", "Nombre"]
    if len(type_counts) > 0:
        fig_type = px.bar(type_counts, x="Type", y="Nombre",
                          color_discrete_sequence=["#00B2E3"])
        fig_type.update_layout(margin=dict(t=10, b=10), font=dict(family="Source Sans 3"),
                               xaxis_title="", height=300)
        st.plotly_chart(fig_type, use_container_width=True)
    else:
        st.info("Pas de données par type.")

# ── Charge par GIE ───────────────────────────────────────────────────
section_header("Charge par entreprise d'études (GIE)", "🏢")

attribuees = df[df["Statut"].isin(["Attribuée", "Commandée"])]
if len(attribuees) > 0 and (attribuees["Attribution_Finale"] != "").any():
    gie_stats = attribuees.groupby("Attribution_Finale").agg(
        Nombre=("ID_Demande", "count"),
        Montant_Total=("_montant", "sum"),
    ).reset_index()

    c1, c2 = st.columns(2)
    with c1:
        fig_gie = px.bar(gie_stats, x="Attribution_Finale", y="Nombre",
                         color_discrete_sequence=["#005F83"], text_auto=True)
        fig_gie.update_layout(margin=dict(t=10, b=10), font=dict(family="Source Sans 3"),
                              xaxis_title="", yaxis_title="Nb demandes", height=300)
        st.plotly_chart(fig_gie, use_container_width=True)
    with c2:
        fig_gie_m = px.bar(gie_stats, x="Attribution_Finale", y="Montant_Total",
                           color_discrete_sequence=["#00B2E3"], text_auto=True)
        fig_gie_m.update_layout(margin=dict(t=10, b=10), font=dict(family="Source Sans 3"),
                                xaxis_title="", yaxis_title="Montant (k€)", height=300)
        st.plotly_chart(fig_gie_m, use_container_width=True)
else:
    st.info("Aucune attribution pour le moment.")

# ── Timeline des demandes ────────────────────────────────────────────
section_header("Activité récente", "🕐")
df_sorted = df.sort_values("Date_Creation", ascending=False).head(20)
for _, row in df_sorted.iterrows():
    c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
    with c1:
        st.markdown(f"<code style='color:#005F83;'>{row.get('ID_Demande','')[:15]}</code>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"{row.get('Nom_Ouvrage_Projet', 'N/A')}")
    with c3:
        st.markdown(status_badge(row.get("Statut", "")), unsafe_allow_html=True)
    with c4:
        st.caption(str(row.get("Date_Creation", ""))[:16])

# Export activité récente
activity_cols = ["ID_Demande", "Nom_Ouvrage_Projet", "Statut", "Date_Creation",
                 "Manager_Projet", "Trimestre_Attribution"]
activity_cols = [c for c in activity_cols if c in df_sorted.columns]
export_excel_button(df_sorted[activity_cols], "activite_recente.xlsx", "Activité", key="export_suivi")
