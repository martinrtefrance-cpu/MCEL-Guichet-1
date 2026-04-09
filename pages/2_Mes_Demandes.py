"""
2_Mes_Demandes.py — Consulter, modifier, soumettre ses demandes.

v18 : Visibilité conditionnelle LA / LS / Mixte.
  - Type_Projet contrôle l'affichage des sections techniques et jalons.
  - Suppression des champs absents du fichier Excel de référence.
  - Validation type-aware à la soumission.
"""
import streamlit as st
import pandas as pd
import datetime
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data_manager import (
    load_user_data, modifier_demande, soumettre_demande, annuler_demande,
    STATUTS, GIE_LIST, TRIMESTRES, TENSIONS, TYPES_PROJET, TYPOLOGIES_PROJET,
    TYPES_LIAISON_LS,
    valider_soumission,
)
from ui_components import (
    inject_css, render_header, section_header, status_badge,
    info_box, render_sidebar, export_excel_button, notify_success,
    PLACEHOLDER, clean_select, show_success_alert,
)
from auth import require_auth

st.set_page_config(page_title="Mes Demandes", page_icon="📋", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()
render_sidebar(active_page="demandes")
user = require_auth()
render_header("Gérer vos demandes d'études")

_soumise_id = None
if st.session_state.get("demande_soumise_id"):
    _soumise_id = st.session_state.pop("demande_soumise_id")
    show_success_alert("Demande soumise avec succès !",
                       f"La demande {_soumise_id} a été transmise pour attribution.")
    st.markdown("""<script>
        window.parent.document.querySelector('section.main').scrollTo({top:0,behavior:'smooth'});
    </script>""", unsafe_allow_html=True)

df = load_user_data(user["email"], user.get("is_admin", False))

if len(df) == 0:
    info_box("Aucune demande enregistrée.")
    st.stop()

# ── Filtres ───────────────────────────────────────────────────────────
section_header("Filtres", "🔍")
c1, c2, c3 = st.columns(3)
with c1:
    filtre_statut = st.multiselect("Statut", STATUTS, default=["Brouillon", "Soumise"])
with c2:
    filtre_trim = st.multiselect("Trimestre", TRIMESTRES)
with c3:
    filtre_manager = st.text_input("Manager de projet", "")

mask = pd.Series([True] * len(df), index=df.index)
if filtre_statut:
    mask &= df["Statut"].isin(filtre_statut)
if filtre_trim:
    mask &= df["Trimestre_Attribution"].isin(filtre_trim)
if filtre_manager:
    mask &= df["Manager_Projet"].str.contains(filtre_manager, case=False, na=False)

filtered = df[mask].copy()

if len(filtered) == 0:
    st.info("Aucune demande ne correspond aux filtres.")
    st.stop()

# ── Liste ─────────────────────────────────────────────────────────────
section_header(f"Demandes ({len(filtered)})", "📄")
display_cols = ["Nom_Ouvrage_Projet", "Statut", "Manager_Projet",
                "Trimestre_Attribution", "EOTP2", "Type_Projet", "Tension",
                "Attribution_Finale", "Date_Creation", "ID_Demande"]
display_cols = [c for c in display_cols if c in filtered.columns]

html = '<table style="width:100%;border-collapse:collapse;font-size:0.85rem;"><tr>'
nice = {"Nom_Ouvrage_Projet": "Projet", "Statut": "Statut", "Manager_Projet": "Manager",
        "Trimestre_Attribution": "Trimestre", "EOTP2": "EOTP2", "Type_Projet": "Type",
        "Tension": "Tension", "Attribution_Finale": "GIE attribué",
        "Date_Creation": "Créé le", "ID_Demande": "ID"}
for c in display_cols:
    html += f'<th style="background:#1B2A4A;color:#FFFFFF;padding:8px 10px;text-align:left;">{nice.get(c,c)}</th>'
html += '</tr>'
for _, row in filtered.iterrows():
    html += '<tr style="border-bottom:1px solid #E0E0E0;">'
    for c in display_cols:
        v = str(row.get(c, ""))
        if c == "Statut":
            v = status_badge(v)
        elif c == "Nom_Ouvrage_Projet":
            v = f'<b style="color:#0E86D4;">{v}</b>'
        elif c == "ID_Demande":
            v = f'<code style="color:#94A3B8;font-size:0.75rem;">{v}</code>'
        elif c == "Attribution_Finale":
            if v and v not in ("", "nan", "None"):
                v = f'<span style="color:#2563EB;font-weight:600;">🏢 {v}</span>'
            else:
                v = '<span style="color:#CBD5E1;font-size:0.8rem;">—</span>'
        html += f'<td style="padding:6px 10px;color:#1E293B;background:#FFFFFF;">{v}</td>'
    html += '</tr>'
html += '</table>'
st.markdown(html, unsafe_allow_html=True)
export_excel_button(filtered[display_cols], "mes_demandes.xlsx", "Demandes", key="export_demandes")

# ── Detail / Modification ─────────────────────────────────────────────
st.markdown("---")
section_header("Modifier / Soumettre une demande", "✏️")

demande_labels = [
    f"{row.get('Nom_Ouvrage_Projet', 'Sans nom')} — {row['ID_Demande']}"
    for _, row in filtered.iterrows()
]
selected_label = st.selectbox("Sélectionnez une demande", [PLACEHOLDER] + demande_labels)

if selected_label and selected_label != PLACEHOLDER:
    selected_id = selected_label.split(" — ")[-1]
    row = df[df["ID_Demande"] == selected_id].iloc[0]
    statut = row["Statut"]
    is_locked = statut in ("Attribuée", "Commandée")

    if is_locked:
        st.warning(f"🔒 Cette demande est **{statut}** et ne peut plus être modifiée.")

    # ── Résoudre le type de projet pour cette demande ─────────────
    current_type = str(row.get("Type_Projet", "")).strip()
    show_la_row = current_type in ("LA", "Mixte")
    show_ls_row = current_type in ("LS", "Mixte")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**Projet :** {row.get('Nom_Ouvrage_Projet', '')}")
    with col2:
        st.markdown(f"**Statut :** {status_badge(statut)}", unsafe_allow_html=True)
    with col3:
        st.markdown(f"**Dernière modif :** {row.get('Derniere_Modification', '')}")

    # ── GIE attribué (affiché uniquement si défini) ──────────────────
    gie_attribue = str(row.get("Attribution_Finale", "")).strip()
    if gie_attribue and gie_attribue not in ("", "nan", "None"):
        st.markdown(
            f'<div style="background:#EFF6FF;border-left:4px solid #2563EB;'
            f'border-radius:0 10px 10px 0;padding:0.5rem 1rem;margin:0.4rem 0;'
            f'font-size:0.85rem;color:#1D4ED8;">'
            f'🏢 <b>GIE attribué :</b> {gie_attribue}'
            f'{"  ·  📅 " + str(row.get("Date_Attribution", "")) if pd.notna(row.get("Date_Attribution")) and str(row.get("Date_Attribution", "")).strip() else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )

    if not is_locked:
        with st.form("form_modifier"):
            # ── Informations Générales ────────────────────────────────
            section_header("Informations Générales 🔵", "📋")
            c1, c2 = st.columns(2)
            with c1:
                new_nom = st.text_input("Nom du projet 🔵", value=str(row.get("Nom_Ouvrage_Projet", "")))
                new_trim = st.selectbox(
                    "Trimestre 🔵",
                    [PLACEHOLDER] + TRIMESTRES,
                    index=(TRIMESTRES.index(row["Trimestre_Attribution"]) + 1)
                          if row.get("Trimestre_Attribution") in TRIMESTRES else 0,
                )
                new_tension = st.selectbox(
                    "Tension 🔵",
                    [PLACEHOLDER] + TENSIONS,
                    index=(TENSIONS.index(row["Tension"]) + 1)
                          if row.get("Tension") in TENSIONS else 0,
                )
                new_centre_di = st.text_input("Centre DI 🔵", value=str(row.get("Centre_DI", "")))
                new_ruo = st.text_input("RUO 🔵", value=str(row.get("RUO", "")))
            with c2:
                new_resume = st.text_area("Résumé 🔵", value=str(row.get("Resume_Projet", "")), height=120)
                new_manager = st.text_input("Manager de projet", value=str(row.get("Manager_Projet", "")))

            # ── Type de projet ─────────────────────────────────────────
            st.markdown("---")
            section_header("Type de projet", "📐")
            type_opts = [PLACEHOLDER] + TYPES_PROJET
            type_idx = (type_opts.index(current_type) if current_type in TYPES_PROJET else 0)
            new_type_projet = st.selectbox(
                "Type de projet 🔵 *", type_opts, index=type_idx,
                help="LA = Lignes Aériennes · LS = Liaisons Souterraines · Mixte = les deux.",
            )
            new_tp = clean_select(new_type_projet) if new_type_projet != PLACEHOLDER else ""
            new_show_la = new_tp in ("LA", "Mixte")
            new_show_ls = new_tp in ("LS", "Mixte")

            if new_tp:
                labels_tp = []
                if new_show_la:
                    labels_tp.append("🗼 LA")
                if new_show_ls:
                    labels_tp.append("🔌 LS")
                st.markdown(
                    f'<div style="font-size:0.82rem;color:#6D28D9;margin-bottom:0.5rem;">'
                    f'Sections actives : {" + ".join(labels_tp)}</div>',
                    unsafe_allow_html=True,
                )

            # ── Contacts (soumission) ─────────────────────────────────
            section_header("Contacts 🟠", "📞")
            info_box("Ces champs sont obligatoires pour soumettre la demande.")
            c1, c2, c3 = st.columns(3)
            with c1:
                new_tel_manager = st.text_input("Tél. manager 🟠",
                    value=str(row.get("Tel_Manager", "")))
            with c2:
                new_charge = st.text_input("Chargé d'études 🟠",
                    value=str(row.get("Charge_Etudes", "")))
            with c3:
                new_tel_charge = st.text_input("Tél. chargé d'études 🟠",
                    value=str(row.get("Tel_Charge_Etudes", "")))

            # ── Lots (soumission) ─────────────────────────────────────
            lots_opts = ["1", "2"]
            lots_idx = lots_opts.index(str(row.get("Nbre_Lots_Etudes", "1")).strip()) \
                       if str(row.get("Nbre_Lots_Etudes", "1")).strip() in lots_opts else 0
            new_nbre_lots = st.radio("Nombre de lots d'études 🟠", options=lots_opts,
                                     index=lots_idx, horizontal=True)

            # ── Données Techniques LA ─────────────────────────────────
            if new_show_la:
                section_header("Données Techniques — LA", "🗼")
                c1, c2, c3 = st.columns(3)
                with c1:
                    la_typo_opts = [PLACEHOLDER] + TYPOLOGIES_PROJET
                    la_typo_idx = (la_typo_opts.index(row.get("LA_Typologie_Projet", PLACEHOLDER))
                                   if row.get("LA_Typologie_Projet") in TYPOLOGIES_PROJET else 0)
                    new_la_typo = st.selectbox("Typologie LA 🔵", la_typo_opts, index=la_typo_idx)
                with c2:
                    new_la_long = st.number_input("Longueur liaison LA (km) 🔵",
                        min_value=0.0, step=0.1,
                        value=float(row.get("LA_Longueur_Liaison_km") or 0))
                with c3:
                    new_la_pyl = st.number_input("Nb pylônes 🔵",
                        min_value=0, step=1,
                        value=int(float(row.get("LA_Nb_Pylones") or 0)))

                c1, c2, c3 = st.columns(3)
                with c1:
                    la_lidar_opts = [PLACEHOLDER, "Oui", "Non"]
                    la_lidar_idx = (la_lidar_opts.index(row.get("LA_Besoin_LIDAR", PLACEHOLDER))
                                    if row.get("LA_Besoin_LIDAR") in ["Oui", "Non"] else 0)
                    new_la_lidar = st.selectbox("Besoin LIDAR 🔵", la_lidar_opts, index=la_lidar_idx)
                with c2:
                    _geo_val = str(row.get("LA_Geotech_Existante", "")).strip().lower()
                    new_la_geotech = st.checkbox("Géotechnique existante 🟠",
                        value=(_geo_val in ("oui", "true", "1")), key="m_la_geotech")
                with c3:
                    _conv_raw = row.get("LA_Nbre_Conventions", 0)
                    try:
                        _conv_default = int(float(_conv_raw)) if _conv_raw and str(_conv_raw).strip() else 0
                    except (ValueError, TypeError):
                        _conv_default = 0
                    new_la_conv = st.number_input("Nbre conventions estimé 🟠",
                        min_value=0, value=_conv_default, step=1, key="m_la_conv")

            # ── Données Techniques LS ─────────────────────────────────
            if new_show_ls:
                section_header("Données Techniques — LS", "🔌")
                c1, c2 = st.columns(2)
                with c1:
                    ls_typo_opts = [PLACEHOLDER] + TYPOLOGIES_PROJET
                    ls_typo_idx = (ls_typo_opts.index(row.get("LS_Typologie_Projet", PLACEHOLDER))
                                   if row.get("LS_Typologie_Projet") in TYPOLOGIES_PROJET else 0)
                    new_ls_typo = st.selectbox("Typologie LS 🔵", ls_typo_opts, index=ls_typo_idx)
                with c2:
                    ls_liaison_opts = [PLACEHOLDER] + TYPES_LIAISON_LS
                    ls_liaison_idx = (ls_liaison_opts.index(row.get("LS_Type_Liaison", PLACEHOLDER))
                                      if row.get("LS_Type_Liaison") in TYPES_LIAISON_LS else 0)
                    new_ls_liaison = st.selectbox("Type de liaison 🔵", ls_liaison_opts, index=ls_liaison_idx)

                c1, c2, c3 = st.columns(3)
                with c1:
                    new_ls_fais = st.number_input("Linéaire faisabilité LS (km) 🟠",
                        min_value=0.0, step=0.1,
                        value=float(row.get("LS_Lineaire_Faisabilite_km") or 0))
                with c2:
                    new_ls_trace = st.number_input("Linéaire tracé LS (km) 🔵",
                        min_value=0.0, step=0.1,
                        value=float(row.get("LS_Lineaire_Trace_km") or 0))
                with c3:
                    new_ls_det = st.number_input("Linéaire détails LS (km) 🔵",
                        min_value=0.0, step=0.1,
                        value=float(row.get("LS_Lineaire_Details_km") or 0))

                st.markdown("**Répartition milieu (%) 🔵**")
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1: new_ls_rural = st.number_input("% Rural", min_value=0, max_value=100, value=int(float(row.get("LS_Pct_Rural") or 0)))
                with c2: new_ls_urb   = st.number_input("% Urbain", min_value=0, max_value=100, value=int(float(row.get("LS_Pct_Urbain") or 0)))
                with c3: new_ls_ud    = st.number_input("% Urb. dense", min_value=0, max_value=100, value=int(float(row.get("LS_Pct_Urbain_Dense") or 0)))
                with c4: new_ls_poste = st.number_input("% Poste", min_value=0, max_value=100, value=int(float(row.get("LS_Pct_Poste") or 0)))
                with c5: new_ls_gal   = st.number_input("% Galerie", min_value=0, max_value=100, value=int(float(row.get("LS_Pct_Galerie") or 0)))

                c1, c2 = st.columns(2)
                with c1:
                    franch_opts = [PLACEHOLDER, "Oui", "Non"]
                    franch_idx = (franch_opts.index(row.get("LS_Franchissement_Complexe", PLACEHOLDER))
                                  if row.get("LS_Franchissement_Complexe") in ["Oui", "Non"] else 0)
                    new_ls_franch = st.selectbox("Franchissement complexe 🔵", franch_opts, index=franch_idx)
                with c2:
                    st.markdown("**Domaine 🟠**")
                    c2a, c2b = st.columns(2)
                    with c2a:
                        new_ls_pub = st.number_input("% domaine public 🟠", min_value=0, max_value=100,
                            value=int(float(row.get("LS_Pct_Domaine_Public") or 0)))
                    with c2b:
                        new_ls_priv = st.number_input("% domaine privé 🟠", min_value=0, max_value=100,
                            value=int(float(row.get("LS_Pct_Domaine_Prive") or 0)))

            # ── Jalons ────────────────────────────────────────────────
            section_header("Jalons", "📅")

            def _parse_date(v):
                try:
                    return datetime.date.fromisoformat(str(v)[:10])
                except Exception:
                    return None

            if new_show_la:
                st.markdown("**Jalons LA (commande) 🔵/🟠**")
                c1, c2 = st.columns(2)
                with c1:
                    new_j_la_fin = st.date_input("LA — Fin souhaitée études détails 🔵",
                        value=_parse_date(row.get("Jalon_LA_Fin_Details")), key="m_j_la_fin")
                    new_j_la_fais = st.date_input("LA — Fin faisabilité (DCT) 🟠",
                        value=_parse_date(row.get("Jalon_LA_Fin_Faisabilite_DCT")), key="m_j_la_fais")
                    new_j_consult = st.date_input("Date consultation (CCTP) 🟠",
                        value=_parse_date(row.get("Jalon_Date_Consultation")), key="m_j_consult")
                with c2:
                    new_j_la_deb = st.date_input("LA — Début études détails 🟠",
                        value=_parse_date(row.get("Jalon_LA_Debut_Details")), key="m_j_la_deb")
                    new_j_notif = st.date_input("Date notification commande 🟠",
                        value=_parse_date(row.get("Jalon_Date_Notification_Commande")), key="m_j_notif")

            if new_show_ls:
                st.markdown("**Jalons LS 🔵/🟠**")
                c1, c2 = st.columns(2)
                with c1:
                    new_j_ls_fin = st.date_input("LS — Fin étude de détail 🔵",
                        value=_parse_date(row.get("Jalon_LS_Detail_Fin")), key="m_j_ls_fin")
                    new_j_ls_fais = st.date_input("LS — Fin faisabilité 🟠",
                        value=_parse_date(row.get("Jalon_LS_Fin_Faisabilite")), key="m_j_ls_fais")
                with c2:
                    new_j_ls_trace = st.date_input("LS — Fin tracé 🟠",
                        value=_parse_date(row.get("Jalon_LS_Fin_Trace_Preferentiel")), key="m_j_ls_trace")

            # ── Montants ──────────────────────────────────────────────
            section_header("Montants 🔵", "💰")
            if new_show_la and new_show_ls:
                c1, c2, c3 = st.columns(3)
                with c1:
                    new_montant_la = st.number_input("Montant LA (k€) 🔵",
                        min_value=0.0, step=1.0,
                        value=float(row.get("Montant_LA_kE") or 0))
                with c2:
                    new_montant_ls = st.number_input("Montant LS (k€) 🔵",
                        min_value=0.0, step=1.0,
                        value=float(row.get("Montant_LS_kE") or 0))
                with c3:
                    st.metric("Montant Total (k€)", f"{new_montant_la + new_montant_ls:.1f}")
            elif new_show_la:
                c1, c2 = st.columns(2)
                with c1:
                    new_montant_la = st.number_input("Montant LA (k€) 🔵",
                        min_value=0.0, step=1.0,
                        value=float(row.get("Montant_LA_kE") or 0))
                with c2:
                    new_montant_ls = 0.0
                    st.metric("Montant Total (k€)", f"{new_montant_la:.1f}")
            elif new_show_ls:
                c1, c2 = st.columns(2)
                with c1:
                    new_montant_ls = st.number_input("Montant LS (k€) 🔵",
                        min_value=0.0, step=1.0,
                        value=float(row.get("Montant_LS_kE") or 0))
                with c2:
                    new_montant_la = 0.0
                    st.metric("Montant Total (k€)", f"{new_montant_ls:.1f}")
            else:
                new_montant_la = 0.0
                new_montant_ls = 0.0
                info_box("⬆️ Sélectionnez un type de projet pour afficher les montants.")

            # ── Préférences GIE ───────────────────────────────────────
            section_header("Préférences d'attribution 🟠", "🎯")
            info_box("🟠 Ces champs sont obligatoires pour la soumission de la demande.")
            c1, c2, c3 = st.columns(3)
            with c1:
                new_pref1 = st.selectbox("GIE n°1 🟠", [PLACEHOLDER] + GIE_LIST,
                    index=(GIE_LIST.index(row["Pref_GIE_1"]) + 1)
                          if row.get("Pref_GIE_1") in GIE_LIST else 0)
            with c2:
                new_pref2 = st.selectbox("GIE n°2 🟠", [PLACEHOLDER] + GIE_LIST,
                    index=(GIE_LIST.index(row["Pref_GIE_2"]) + 1)
                          if row.get("Pref_GIE_2") in GIE_LIST else 0)
            with c3:
                new_pref3 = st.selectbox("GIE n°3 🟠", [PLACEHOLDER] + GIE_LIST,
                    index=(GIE_LIST.index(row["Pref_GIE_3"]) + 1)
                          if row.get("Pref_GIE_3") in GIE_LIST else 0)
            new_pref_justif = st.text_area("Justification préférence GIE 🟠",
                value=str(row.get("Pref_Justification", "")))

            # ── Règle des 3 mois ──────────────────────────────────────
            st.markdown("---")
            section_header("Soumission à l'attribution", "📤")
            date_creation_str = str(row.get("Date_Creation", ""))
            is_older_than_3m = False
            try:
                date_creation = datetime.datetime.strptime(date_creation_str[:10], "%Y-%m-%d")
                age_days = (datetime.datetime.now() - date_creation).days
                is_older_than_3m = age_days > 90
                if is_older_than_3m:
                    info_box(f"Cette demande date du <b>{date_creation_str[:10]}</b> "
                             "(plus de 3 mois). Soumission directe autorisée.")
                else:
                    info_box(f"Cette demande date du <b>{date_creation_str[:10]}</b> "
                             "(moins de 3 mois). Une justification est requise pour "
                             "une soumission hors attribution en masse.")
            except Exception:
                info_box("Date de création non disponible — justification requise par précaution.")

            hors_masse = False
            justif_hors_masse = ""
            if not is_older_than_3m:
                hors_masse = st.checkbox("Demande hors attribution en masse", key="hors_masse_cb")
                if hors_masse:
                    justif_hors_masse = st.text_area(
                        "Justification (obligatoire) *", key="justif_hors_masse",
                        placeholder="Expliquez pourquoi cette demande doit être soumise hors cycle..."
                    )

            # ── Boutons ───────────────────────────────────────────────
            st.markdown("---")
            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                save_btn = st.form_submit_button("💾 Sauvegarder",
                    use_container_width=True, type="primary")
            with bc2:
                submit_btn = st.form_submit_button("📤 Soumettre la demande",
                    use_container_width=True)
            with bc3:
                cancel_btn = st.form_submit_button("🗑️ Annuler la demande",
                    use_container_width=True)

            # ── Données consolidées pour sauvegarde / soumission ──────
            updated_data = {
                "Nom_Ouvrage_Projet":           new_nom,
                "Trimestre_Attribution":        clean_select(new_trim),
                "Tension":                      clean_select(new_tension),
                "Centre_DI":                    new_centre_di,
                "RUO":                          new_ruo,
                "Resume_Projet":                new_resume,
                "Manager_Projet":               new_manager,
                "Type_Projet":                  new_tp,
                "Nbre_Lots_Etudes":             new_nbre_lots,
                "Tel_Manager":                  new_tel_manager,
                "Charge_Etudes":                new_charge,
                "Tel_Charge_Etudes":            new_tel_charge,
                # Montants
                "Montant_LA_kE":        str(new_montant_la),
                "Montant_LS_kE":        str(new_montant_ls),
                "Montant_Total":        str(new_montant_la + new_montant_ls),
                # Préférences
                "Pref_GIE_1":           clean_select(new_pref1),
                "Pref_GIE_2":           clean_select(new_pref2),
                "Pref_GIE_3":           clean_select(new_pref3),
                "Pref_Justification":   new_pref_justif,
            }

            # LA — uniquement si affiché
            if new_show_la:
                updated_data.update({
                    "LA_Typologie_Projet":          clean_select(new_la_typo),
                    "LA_Longueur_Liaison_km":       str(new_la_long),
                    "LA_Nb_Pylones":                str(new_la_pyl),
                    "LA_Besoin_LIDAR":              clean_select(new_la_lidar),
                    "LA_Geotech_Existante":         "Oui" if new_la_geotech else "Non",
                    "LA_Nbre_Conventions":          str(new_la_conv),
                    "Jalon_LA_Fin_Details":              str(new_j_la_fin)   if new_j_la_fin   else "",
                    "Jalon_LA_Fin_Faisabilite_DCT":      str(new_j_la_fais)  if new_j_la_fais  else "",
                    "Jalon_LA_Debut_Details":            str(new_j_la_deb)   if new_j_la_deb   else "",
                    "Jalon_Date_Consultation":           str(new_j_consult)  if new_j_consult  else "",
                    "Jalon_Date_Notification_Commande":  str(new_j_notif)    if new_j_notif    else "",
                })

            # LS — uniquement si affiché
            if new_show_ls:
                updated_data.update({
                    "LS_Typologie_Projet":          clean_select(new_ls_typo),
                    "LS_Type_Liaison":              clean_select(new_ls_liaison),
                    "LS_Lineaire_Faisabilite_km":   str(new_ls_fais),
                    "LS_Lineaire_Trace_km":         str(new_ls_trace),
                    "LS_Lineaire_Details_km":       str(new_ls_det),
                    "LS_Pct_Rural":                 str(new_ls_rural),
                    "LS_Pct_Urbain":                str(new_ls_urb),
                    "LS_Pct_Urbain_Dense":          str(new_ls_ud),
                    "LS_Pct_Poste":                 str(new_ls_poste),
                    "LS_Pct_Galerie":               str(new_ls_gal),
                    "LS_Franchissement_Complexe":   clean_select(new_ls_franch),
                    "LS_Pct_Domaine_Public":        str(new_ls_pub),
                    "LS_Pct_Domaine_Prive":         str(new_ls_priv),
                    "Jalon_LS_Detail_Fin":               str(new_j_ls_fin)   if new_j_ls_fin   else "",
                    "Jalon_LS_Fin_Faisabilite":          str(new_j_ls_fais)  if new_j_ls_fais  else "",
                    "Jalon_LS_Fin_Trace_Preferentiel":   str(new_j_ls_trace) if new_j_ls_trace else "",
                })

            if save_btn:
                try:
                    modifier_demande(selected_id, updated_data, user["email"])
                    notify_success("Modifications sauvegardées !")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

            if submit_btn:
                submit_errors = []

                # Validation type de projet
                if not new_tp:
                    submit_errors.append("Type de projet obligatoire — sélectionnez LA, LS ou Mixte.")

                # Règle des 3 mois
                if not is_older_than_3m:
                    if not hors_masse:
                        submit_errors.append(
                            "Cette demande a moins de 3 mois. "
                            "Cochez 'Demande hors attribution en masse' pour la soumettre.")
                    elif not justif_hors_masse.strip():
                        submit_errors.append(
                            "La justification est obligatoire pour une demande hors attribution en masse.")

                # Validation complète soumission (brouillon + soumission) — type-aware
                if not submit_errors and new_tp:
                    champs_manquants = valider_soumission(updated_data, new_tp)
                    if champs_manquants:
                        submit_errors.append(
                            "Champs obligatoires pour la soumission encore manquants : "
                            + ", ".join(champs_manquants))

                if submit_errors:
                    for e in submit_errors:
                        st.error(f"⚠️ {e}")
                else:
                    try:
                        if not is_older_than_3m and hors_masse:
                            updated_data["Pref_Justification"] = justif_hors_masse
                        modifier_demande(selected_id, updated_data, user["email"])
                        soumettre_demande(selected_id, user["email"])
                        st.session_state["demande_soumise_id"] = selected_id
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")

            if cancel_btn:
                try:
                    annuler_demande(selected_id, user["email"])
                    st.toast("Demande annulée.", icon="🗑️")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

    else:
        # Vue lecture seule pour demandes verrouillées
        # Les onglets affichés dépendent du type de projet
        tab_names = ["Général"]
        if show_la_row:
            tab_names.append("Technique LA")
        if show_ls_row:
            tab_names.append("Technique LS")
        tab_names += ["Jalons", "Attribution"]
        tabs = st.tabs(tab_names)

        tab_idx = 0
        with tabs[tab_idx]:
            for col_name, label in [
                ("EOTP2", "EOTP2"), ("RUO", "RUO"), ("Centre_DI", "Centre DI"),
                ("Tension", "Tension"), ("Type_Projet", "Type"),
                ("Resume_Projet", "Résumé"), ("Manager_Projet", "Manager"),
                ("Tel_Manager", "Tél. Manager"), ("Charge_Etudes", "Chargé d'études"),
                ("Nbre_Lots_Etudes", "Lots"),
            ]:
                st.markdown(f"**{label} :** {row.get(col_name, '')}")
        tab_idx += 1

        if show_la_row:
            with tabs[tab_idx]:
                for col_name, label in [
                    ("LA_Typologie_Projet", "Typologie"), ("LA_Longueur_Liaison_km", "Longueur (km)"),
                    ("LA_Nb_Pylones", "Nb pylônes"), ("LA_Besoin_LIDAR", "LIDAR"),
                    ("LA_Geotech_Existante", "Géotechnique"), ("LA_Nbre_Conventions", "Conventions"),
                ]:
                    st.markdown(f"**{label} :** {row.get(col_name, '')}")
            tab_idx += 1

        if show_ls_row:
            with tabs[tab_idx]:
                for col_name, label in [
                    ("LS_Typologie_Projet", "Typologie"), ("LS_Type_Liaison", "Type liaison"),
                    ("LS_Lineaire_Faisabilite_km", "Linéaire faisabilité (km)"),
                    ("LS_Lineaire_Trace_km", "Linéaire tracé (km)"),
                    ("LS_Lineaire_Details_km", "Linéaire détails (km)"),
                    ("LS_Pct_Rural", "% Rural"), ("LS_Pct_Urbain", "% Urbain"),
                    ("LS_Pct_Urbain_Dense", "% Urb. dense"), ("LS_Pct_Poste", "% Poste"),
                    ("LS_Pct_Galerie", "% Galerie"), ("LS_Franchissement_Complexe", "Franchissement complexe"),
                    ("LS_Pct_Domaine_Public", "% domaine public"), ("LS_Pct_Domaine_Prive", "% domaine privé"),
                ]:
                    st.markdown(f"**{label} :** {row.get(col_name, '')}")
            tab_idx += 1

        with tabs[tab_idx]:
            if show_la_row:
                st.markdown("**Jalons LA**")
                for col_name, label in [
                    ("Jalon_LA_Fin_Details", "Fin études détails"),
                    ("Jalon_LA_Fin_Faisabilite_DCT", "Fin faisabilité (DCT)"),
                    ("Jalon_LA_Debut_Details", "Début études détails"),
                    ("Jalon_Date_Consultation", "Date consultation"),
                    ("Jalon_Date_Notification_Commande", "Date notification commande"),
                ]:
                    st.markdown(f"**{label} :** {row.get(col_name, '')}")
            if show_ls_row:
                st.markdown("**Jalons LS**")
                for col_name, label in [
                    ("Jalon_LS_Detail_Fin", "Fin étude de détail"),
                    ("Jalon_LS_Fin_Faisabilite", "Fin faisabilité"),
                    ("Jalon_LS_Fin_Trace_Preferentiel", "Fin tracé"),
                ]:
                    st.markdown(f"**{label} :** {row.get(col_name, '')}")
        tab_idx += 1

        with tabs[tab_idx]:
            st.markdown(f"**Entreprise :** {row.get('Attribution_Finale', '')}")
            st.markdown(f"**Date attribution :** {row.get('Date_Attribution', '')}")
            st.markdown(f"**Attribué par :** {row.get('Attribue_Par', '')}")

# ══════════════════════════════════════════════════════════════════════
# BANDEAU DE CONFIRMATION EN BAS DE PAGE (doublé)
# ══════════════════════════════════════════════════════════════════════
if _soumise_id:
    st.markdown("---")
    show_success_alert("Demande soumise avec succès !",
                       f"La demande {_soumise_id} a été transmise pour attribution.")
