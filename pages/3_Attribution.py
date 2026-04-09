"""
3_Attribution.py — Attribution avec authentification et confirmation en 2 étapes.

v18.1 :
  - Affichage complet et structuré des données MP (lecture seule)
  - Système de relance des managers par email (brouillons incomplets)
  - Historique des relances (date, destinataire, contexte)
  - Indicateur de nécessité de relance
"""
import streamlit as st
import pandas as pd
import sys, os, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data_manager import (
    load_data, attribuer_demande, GIE_LIST, TYPES_PROJET,
    valider_soumission, get_champs_requis_brouillon, get_champs_requis_soumission,
    enregistrer_relance, get_relance_historique,
    COLONNES_TECH_LA, COLONNES_TECH_LS,
    COLONNES_JALONS_LA, COLONNES_JALONS_LS,
)
from ui_components import (
    inject_css, render_header, section_header, status_badge,
    info_box, render_sidebar, export_excel_button, notify_success,
    PLACEHOLDER,
)
from auth import require_auth, check_admin_access
from email_service import send_relance_email

st.set_page_config(page_title="Attribution", page_icon="🎯", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()
render_sidebar(active_page="attribution")

user = require_auth()
render_header("Attribution des demandes aux entreprises d'études")
if not check_admin_access():
    st.stop()

df = load_data()


# ══════════════════════════════════════════════════════════════════════
# HELPERS — Affichage structuré des données MP
# ══════════════════════════════════════════════════════════════════════
def _val(row, key):
    """Retourne la valeur formatée d'un champ, ou '—' si vide."""
    v = row.get(key, "")
    if pd.isna(v) or str(v).strip() in ("", "None", "nan", "0.0", "0"):
        return "—"
    return str(v).strip()


def _has(row, key):
    """Vérifie si un champ a une valeur significative."""
    return _val(row, key) != "—"


def _render_field_table(fields: list, row):
    """Affiche un groupe de champs en tableau HTML lecture seule.
    fields = [(col_name, label), ...]
    """
    html = '<table style="width:100%;border-collapse:collapse;font-size:0.84rem;margin:0.3rem 0 0.6rem;">'
    for i, (col, label) in enumerate(fields):
        v = _val(row, col)
        bg = "#F8FAFC" if i % 2 == 0 else "#FFFFFF"
        color = "#1E293B" if v != "—" else "#94A3B8"
        html += (
            f'<tr style="background:{bg};">'
            f'<td style="padding:6px 12px;font-weight:600;color:#475569;width:45%;'
            f'border-bottom:1px solid #F1F5F9;">{label}</td>'
            f'<td style="padding:6px 12px;color:{color};border-bottom:1px solid #F1F5F9;">{v}</td>'
            f'</tr>'
        )
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)


def render_demande_detail(row):
    """Affiche toutes les données MP de la demande dans des onglets structurés."""
    tp = str(row.get("Type_Projet", "")).strip()
    show_la = tp in ("LA", "Mixte")
    show_ls = tp in ("LS", "Mixte")

    # Construire les onglets dynamiquement
    tab_names = ["📋 Général", "📞 Contacts"]
    if show_la:
        tab_names.append("🗼 Technique LA")
    if show_ls:
        tab_names.append("🔌 Technique LS")
    tab_names += ["📅 Jalons", "💰 Montants", "🎯 Préférences"]
    tabs = st.tabs(tab_names)
    tab_i = 0

    # ── Général ───────────────────────────────────────────────────────
    with tabs[tab_i]:
        _render_field_table([
            ("EOTP2", "EOTP2"),
            ("Nom_Ouvrage_Projet", "Nom de l'ouvrage / projet"),
            ("Centre_DI", "Centre DI"),
            ("RUO", "RUO"),
            ("Tension", "Tension"),
            ("Type_Projet", "Type de projet"),
            ("Nbre_Lots_Etudes", "Nombre de lots d'études"),
            ("Resume_Projet", "Résumé du projet"),
            ("Trimestre_Attribution", "Trimestre d'attribution"),
            ("Date_Fiche_ATP", "Date fiche ATP"),
            ("N_Fiche_ATP", "N° Fiche ATP"),
        ], row)
        if _has(row, "Urgente") and str(row.get("Urgente", "")) == "Oui":
            st.markdown("""<div style="background:#FEF3C7;border-left:3px solid #F59E0B;
                padding:0.4rem 0.8rem;border-radius:0 6px 6px 0;font-size:0.82rem;color:#92400E;">
                ⚡ Demande urgente</div>""", unsafe_allow_html=True)
        if _has(row, "Justification_Urgence_EOTP"):
            st.markdown(f"**Justification :** {_val(row, 'Justification_Urgence_EOTP')}")
    tab_i += 1

    # ── Contacts ──────────────────────────────────────────────────────
    with tabs[tab_i]:
        _render_field_table([
            ("Manager_Projet", "Manager de projet"),
            ("Tel_Manager", "Téléphone du manager"),
            ("Charge_Etudes", "Chargé d'études"),
            ("Tel_Charge_Etudes", "Tél. chargé d'études"),
            ("Createur_Email", "Créateur (email)"),
        ], row)
    tab_i += 1

    # ── Technique LA ──────────────────────────────────────────────────
    if show_la:
        with tabs[tab_i]:
            _render_field_table([
                ("LA_Typologie_Projet", "Typologie"),
                ("LA_Longueur_Liaison_km", "Longueur de liaison (km)"),
                ("LA_Nb_Pylones", "Nb pylônes à traiter"),
                ("LA_Geotech_Existante", "Géotechnique existante"),
                ("LA_Nbre_Conventions", "Nbre conventions estimé"),
                ("LA_Besoin_LIDAR", "Besoin de LIDAR"),
            ], row)
        tab_i += 1

    # ── Technique LS ──────────────────────────────────────────────────
    if show_ls:
        with tabs[tab_i]:
            _render_field_table([
                ("LS_Typologie_Projet", "Typologie"),
                ("LS_Type_Liaison", "Type de liaison"),
                ("LS_Lineaire_Faisabilite_km", "Linéaire faisabilité (km)"),
                ("LS_Lineaire_Trace_km", "Linéaire tracé (km)"),
                ("LS_Lineaire_Details_km", "Linéaire détails (km)"),
                ("LS_Pct_Rural", "% Rural"),
                ("LS_Pct_Urbain", "% Urbain"),
                ("LS_Pct_Urbain_Dense", "% Urbain dense"),
                ("LS_Pct_Poste", "% Poste"),
                ("LS_Pct_Galerie", "% Galerie"),
                ("LS_Franchissement_Complexe", "Franchissement complexe"),
                ("LS_Pct_Domaine_Public", "% domaine public estimé"),
                ("LS_Pct_Domaine_Prive", "% domaine privé"),
            ], row)
        tab_i += 1

    # ── Jalons ────────────────────────────────────────────────────────
    with tabs[tab_i]:
        if show_la:
            st.markdown("**Jalons LA (commande)**")
            _render_field_table([
                ("Jalon_Date_Consultation", "Date consultation (envoi CCTP)"),
                ("Jalon_Date_Notification_Commande", "Date notification commande"),
                ("Jalon_LA_Fin_Faisabilite_DCT", "Fin faisabilité (DCT)"),
                ("Jalon_LA_Debut_Details", "Début souhaité études détails"),
                ("Jalon_LA_Fin_Details", "Fin souhaitée études détails"),
            ], row)
        if show_ls:
            st.markdown("**Jalons LS**")
            _render_field_table([
                ("Jalon_LS_Fin_Faisabilite", "Fin faisabilité"),
                ("Jalon_LS_Fin_Trace_Preferentiel", "Fin études de tracé"),
                ("Jalon_LS_Detail_Fin", "Fin étude de détail"),
            ], row)
        if not show_la and not show_ls:
            st.info("Type de projet non défini — aucun jalon à afficher.")
    tab_i += 1

    # ── Montants ──────────────────────────────────────────────────────
    with tabs[tab_i]:
        fields_m = []
        if show_la:
            fields_m.append(("Montant_LA_kE", "Montant LA (k€)"))
        if show_ls:
            fields_m.append(("Montant_LS_kE", "Montant LS (k€)"))
        fields_m.append(("Montant_Total", "Montant Total (k€)"))
        _render_field_table(fields_m, row)
    tab_i += 1

    # ── Préférences ───────────────────────────────────────────────────
    with tabs[tab_i]:
        _render_field_table([
            ("Pref_GIE_1", "Souhait GIE n°1"),
            ("Pref_GIE_2", "Souhait GIE n°2"),
            ("Pref_GIE_3", "Souhait GIE n°3"),
            ("Pref_Justification", "Justification"),
        ], row)


# ══════════════════════════════════════════════════════════════════════
# HELPER — Relance email
# ══════════════════════════════════════════════════════════════════════
def _resolve_manager_email(row):
    """Détermine l'email du manager à partir du nom ou des champs disponibles."""
    manager_name = str(row.get("Manager_Projet", "")).strip()
    createur = str(row.get("Createur_Email", "")).strip()
    if createur and "@" in createur:
        return createur, manager_name
    parts = manager_name.split()
    if len(parts) >= 2:
        email = f"{parts[0].lower()}.{parts[-1].lower()}@rte-france.com"
        return email, manager_name
    return "", manager_name


# ══════════════════════════════════════════════════════════════════════
# VUE PRINCIPALE
# ══════════════════════════════════════════════════════════════════════
soumises = df[df["Statut"] == "Soumise"].copy()
brouillons = df[df["Statut"] == "Brouillon"].copy()

if len(soumises) == 0 and len(brouillons) == 0:
    info_box("✅ Aucune demande en attente d'attribution ou en brouillon.")
    attribuees = df[df["Statut"] == "Attribuée"].sort_values("Date_Attribution", ascending=False).head(10)
    if len(attribuees) > 0:
        section_header("Dernières attributions", "📜")
        for _, row in attribuees.iterrows():
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            with c1:
                st.markdown(f"**{row.get('Nom_Ouvrage_Projet', 'N/A')}**")
            with c2:
                st.markdown(f"🏢 {row.get('Attribution_Finale', 'N/A')}")
            with c3:
                st.markdown(f"📅 {row.get('Date_Attribution', 'N/A')}")
            with c4:
                st.markdown(status_badge("Attribuée"), unsafe_allow_html=True)
    st.stop()


# ── SECTION 1 : Demandes soumises (en attente d'attribution) ─────────
if len(soumises) > 0:
    section_header(f"Demandes en attente d'attribution ({len(soumises)})", "⏳")

    info_box(
        "⚠️ <b>Attention :</b> L'attribution est <b>irréversible</b>. "
        "Une confirmation vous sera demandée avant toute attribution."
    )

    cols_display = ["Nom_Ouvrage_Projet", "Manager_Projet", "ID_Demande",
                    "Type_Projet", "Trimestre_Attribution", "Tension", "Montant_Total",
                    "Pref_GIE_1", "Pref_GIE_2", "Pref_GIE_3"]

    html = '<table style="width:100%;border-collapse:collapse;font-size:0.83rem;"><tr>'
    headers = {
        "Nom_Ouvrage_Projet": "Projet", "Manager_Projet": "Manager", "ID_Demande": "ID",
        "Type_Projet": "Type", "Trimestre_Attribution": "Trim.", "Tension": "Tension",
        "Montant_Total": "Montant (k€)",
        "Pref_GIE_1": "Préf. 1", "Pref_GIE_2": "Préf. 2", "Pref_GIE_3": "Préf. 3",
    }
    for c in cols_display:
        html += (f'<th style="background:#0E86D4;color:white;padding:6px 8px;'
                 f'text-align:left;white-space:nowrap;">{headers.get(c, c)}</th>')
    html += '</tr>'
    for _, row in soumises.iterrows():
        html += '<tr style="border-bottom:1px solid #E0E0E0;">'
        for c in cols_display:
            v = str(row.get(c, "") or "")
            if c == "Nom_Ouvrage_Projet":
                v = f'<b style="color:#0E86D4;">{v}</b>'
            elif c == "ID_Demande":
                v = f'<code style="color:#94A3B8;font-size:0.75rem;">{v}</code>'
            html += f'<td style="padding:5px 8px;">{v}</td>'
        html += '</tr>'
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)
    safe_cols = [c for c in cols_display if c in soumises.columns]
    export_excel_button(soumises[safe_cols], "demandes_en_attente.xlsx", "En attente",
                        key="export_attente")

    # ── Formulaire d'attribution ─────────────────────────────────────
    st.markdown("---")
    section_header("Attribuer une demande", "🎯")

    demande_labels = [
        f"{row.get('Nom_Ouvrage_Projet', 'Sans nom')} — {row['ID_Demande']}"
        for _, row in soumises.iterrows()
    ]

    selected_label = st.selectbox("Sélectionnez la demande à attribuer",
                                  [PLACEHOLDER] + demande_labels)

    if selected_label and selected_label != PLACEHOLDER:
        sel_id = selected_label.split(" — ")[-1]
        row = df[df["ID_Demande"] == sel_id].iloc[0]

        # ── Détail complet des données MP ────────────────────────────
        st.markdown("#### 📄 Données complètes renseignées par le manager")
        render_demande_detail(row)

        st.markdown("---")

        # ── Détection du nombre de lots ──────────────────────────────
        nbre_lots_dem = str(row.get("Nbre_Lots_Etudes", "1")).strip()
        is_multi_lot = (nbre_lots_dem == "2")

        if is_multi_lot:
            st.markdown("""<div style="background:#EFF6FF;border-left:4px solid #3B82F6;
                border-radius:0 10px 10px 0;padding:0.6rem 1rem;margin:0.5rem 0;
                font-size:0.84rem;color:#1D4ED8;">
                🗂️ <b>Demande 2 lots</b> — Sélectionnez une entreprise pour chaque lot.
                </div>""", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                gie_lot1 = st.selectbox("Entreprise d'étude — Lot 1 *",
                                        [PLACEHOLDER] + GIE_LIST, key="gie_lot1")
            with c2:
                gie_lot2 = st.selectbox("Entreprise d'étude — Lot 2 *",
                                        [PLACEHOLDER] + GIE_LIST, key="gie_lot2")
            gie_selected = gie_lot1
            gie_selected_lot2 = gie_lot2
            can_submit = (gie_lot1 != PLACEHOLDER and gie_lot2 != PLACEHOLDER)
        else:
            gie_selected = st.selectbox("Entreprise d'études (GIE) à attribuer",
                                        [PLACEHOLDER] + GIE_LIST, key="gie_attr")
            gie_selected_lot2 = ""
            can_submit = (gie_selected and gie_selected != PLACEHOLDER)

        if can_submit:
            confirm_key = f"confirm_{sel_id}_{gie_selected}"
            is_confirming = st.session_state.get(confirm_key, False)

            if not is_confirming:
                if st.button("🎯 Attribuer cette demande", type="primary",
                             use_container_width=True):
                    st.session_state[confirm_key] = True
                    st.rerun()
            else:
                lot_desc = (
                    f"Lot 1 : <b>{gie_selected}</b> / Lot 2 : <b>{gie_selected_lot2}</b>"
                    if is_multi_lot else f"<b>{gie_selected}</b>"
                )
                st.markdown(f"""
                <div class="confirm-box">
                    <h4>⚠️ Confirmation requise</h4>
                    <p>Attribution de <b>{sel_id}</b> → {lot_desc}<br>
                    Cette action est <b>irréversible</b>.</p>
                </div>""", unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Oui, confirmer l'attribution", type="primary",
                                 use_container_width=True):
                        try:
                            attribuer_demande(sel_id, gie_selected, user["email"],
                                              gie_lot2=gie_selected_lot2)
                            st.session_state.pop(confirm_key, None)
                            notify_success(f"Demande {sel_id} attribuée")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur : {e}")
                with c2:
                    if st.button("❌ Annuler", use_container_width=True):
                        st.session_state.pop(confirm_key, None)
                        st.rerun()

else:
    info_box("✅ Aucune demande soumise en attente d'attribution.")


# ══════════════════════════════════════════════════════════════════════
# SECTION 2 : Relance des managers — Brouillons incomplets
# ══════════════════════════════════════════════════════════════════════
st.markdown("---")
section_header("Relance des managers — Brouillons en attente de soumission", "📧")

if len(brouillons) == 0:
    info_box("Aucun brouillon en attente — tous les managers ont soumis leurs demandes.")
else:
    st.markdown(f"**{len(brouillons)}** brouillon(s) en attente de complétion par le manager.")

    for idx, row in brouillons.iterrows():
        dem_id = str(row.get("ID_Demande", ""))
        projet = str(row.get("Nom_Ouvrage_Projet", "N/A"))
        manager_name = str(row.get("Manager_Projet", "N/A"))
        tp = str(row.get("Type_Projet", "")).strip()
        tp_for_val = tp if tp in TYPES_PROJET else "Mixte"

        # Calcul de la complétude
        row_dict = row.to_dict()
        champs_manquants = valider_soumission(row_dict, tp_for_val)
        nb_total_b = len(get_champs_requis_brouillon(tp_for_val))
        nb_total_s = len(get_champs_requis_soumission(tp_for_val))
        nb_total = nb_total_b + nb_total_s
        nb_ok = nb_total - len(champs_manquants)
        pct = int(nb_ok / nb_total * 100) if nb_total > 0 else 0
        needs_relance = pct < 100

        # Historique relances
        relance_count_raw = row.get("Relance_Count", "")
        try:
            relance_count = int(float(relance_count_raw)) if pd.notna(relance_count_raw) and str(relance_count_raw).strip() else 0
        except (ValueError, TypeError):
            relance_count = 0
        derniere_relance = _val(row, "Relance_Derniere_Date")

        with st.container():
            # Indicateur de relance
            if needs_relance:
                badge_color = "#EF4444" if pct < 50 else "#F59E0B"
                badge_text = "⚠️ Relance nécessaire" if relance_count == 0 else f"📧 Relancé ×{relance_count}"
                badge_html = (
                    f'<span style="background:{badge_color}15;color:{badge_color};'
                    f'padding:2px 8px;border-radius:10px;font-size:0.75rem;'
                    f'border:1px solid {badge_color}40;">{badge_text}</span>'
                )
            else:
                badge_html = (
                    '<span style="background:#22C55E15;color:#22C55E;'
                    'padding:2px 8px;border-radius:10px;font-size:0.75rem;'
                    'border:1px solid #22C55E40;">✅ Complet</span>'
                )

            c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 1.5])
            with c1:
                st.markdown(
                    f'<b style="color:#0E86D4;">{projet}</b> · '
                    f'<code style="color:#94A3B8;font-size:0.75rem;">{dem_id}</code><br>'
                    f'<span style="color:#6B7280;font-size:0.83rem;">'
                    f'Manager : {manager_name} · Type : {tp or "Non défini"}</span>',
                    unsafe_allow_html=True,
                )
            with c2:
                # Barre de complétude
                bar_color = "#22C55E" if pct == 100 else ("#F59E0B" if pct >= 50 else "#EF4444")
                st.markdown(
                    f'<div style="font-size:0.78rem;color:#64748B;margin-bottom:2px;">'
                    f'Complétude : <b>{pct}%</b></div>'
                    f'<div style="background:#E2E8F0;border-radius:4px;height:6px;">'
                    f'<div style="background:{bar_color};border-radius:4px;height:6px;'
                    f'width:{pct}%;"></div></div>',
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(badge_html, unsafe_allow_html=True)
                if derniere_relance != "—":
                    st.markdown(
                        f'<span style="font-size:0.75rem;color:#94A3B8;">'
                        f'Dernière : {derniere_relance}</span>',
                        unsafe_allow_html=True,
                    )
            with c4:
                btn_key = f"relance_brouillon_{dem_id}"
                if st.button("📧 Relancer", key=btn_key, use_container_width=True):
                    to_email, mgr_name = _resolve_manager_email(row)
                    if not to_email:
                        st.error(f"Impossible de déterminer l'email pour {mgr_name}")
                    else:
                        demande_dict = row.to_dict()
                        # Adapter le contexte
                        demande_dict["_relance_contexte"] = "Complétion brouillon"
                        result = send_relance_email(to_email, demande_dict, mgr_name)
                        if result["success"]:
                            try:
                                enregistrer_relance(
                                    dem_id,
                                    utilisateur=user["email"],
                                    destinataire=to_email,
                                    contexte=f"Brouillon incomplet ({pct}%)",
                                )
                            except Exception:
                                pass  # ne pas bloquer si l'enregistrement échoue
                            if result.get("simulated"):
                                st.info(result["message"])
                            else:
                                notify_success(f"Email envoyé à {to_email}")
                            st.rerun()
                        else:
                            st.error(result["message"])

            # Détail des champs manquants (collapsed)
            if needs_relance and champs_manquants:
                with st.expander(f"Voir les {len(champs_manquants)} champ(s) manquant(s)", expanded=False):
                    for cm in champs_manquants:
                        st.markdown(f"- {cm}")

            # Historique des relances (si existant)
            historique = get_relance_historique(row)
            if historique:
                with st.expander(f"📜 Historique des relances ({len(historique)})", expanded=False):
                    hist_html = ('<table style="width:100%;border-collapse:collapse;'
                                 'font-size:0.8rem;"><tr>'
                                 '<th style="background:#F1F5F9;padding:4px 8px;text-align:left;">Date</th>'
                                 '<th style="background:#F1F5F9;padding:4px 8px;text-align:left;">Par</th>'
                                 '<th style="background:#F1F5F9;padding:4px 8px;text-align:left;">Destinataire</th>'
                                 '<th style="background:#F1F5F9;padding:4px 8px;text-align:left;">Contexte</th>'
                                 '</tr>')
                    for h in reversed(historique):
                        hist_html += (
                            f'<tr style="border-bottom:1px solid #F1F5F9;">'
                            f'<td style="padding:4px 8px;">{h.get("date", "—")}</td>'
                            f'<td style="padding:4px 8px;">{h.get("par", "—")}</td>'
                            f'<td style="padding:4px 8px;">{h.get("destinataire", "—")}</td>'
                            f'<td style="padding:4px 8px;">{h.get("contexte", "—")}</td>'
                            f'</tr>'
                        )
                    hist_html += '</table>'
                    st.markdown(hist_html, unsafe_allow_html=True)

            st.markdown(
                '<hr style="margin:0.3rem 0;border:none;border-top:1px solid #E6EDF3;">',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════
# SECTION 3 : Dernières attributions
# ══════════════════════════════════════════════════════════════════════
attribuees = df[df["Statut"] == "Attribuée"].sort_values("Date_Attribution", ascending=False).head(10)
if len(attribuees) > 0:
    st.markdown("---")
    section_header("Dernières attributions", "📜")
    for _, row in attribuees.iterrows():
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        with c1:
            st.markdown(f"**{row.get('Nom_Ouvrage_Projet', 'N/A')}**")
        with c2:
            st.markdown(f"🏢 {row.get('Attribution_Finale', 'N/A')}")
        with c3:
            st.markdown(f"📅 {row.get('Date_Attribution', 'N/A')}")
        with c4:
            st.markdown(status_badge("Attribuée"), unsafe_allow_html=True)
