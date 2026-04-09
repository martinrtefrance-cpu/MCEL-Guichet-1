"""
1_Nouvelle_Demande.py — Formulaire de création de demande d'étude.

v18 : Visibilité conditionnelle LA / LS / Mixte.
  - Type_Projet contrôle l'affichage des sections techniques et jalons.
  - Suppression des champs absents du fichier Excel de référence.
"""
import streamlit as st
import sys, os, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data_manager import (
    ajouter_demande, TENSIONS, TYPES_PROJET, TYPOLOGIES_PROJET,
    TYPES_LIAISON_LS, GIE_LIST,
    get_eotp_list, lookup_eotp, get_attribution_calendar,
    valider_brouillon, get_champs_requis_brouillon,
)
from ui_components import (
    inject_css, render_header, section_header, info_box,
    render_sidebar, notify_success, PLACEHOLDER, clean_select,
)
from auth import require_auth

st.set_page_config(page_title="Nouvelle Demande", page_icon="➕", layout="wide",
                   initial_sidebar_state="expanded")
inject_css()
render_sidebar(active_page="nouvelle")
user = require_auth()
render_header("Créer une nouvelle demande d'étude")

# ── Légende des modes de champs ───────────────────────────────────────
st.markdown("""
<div style="display:flex;gap:1rem;margin-bottom:0.8rem;flex-wrap:wrap;">
  <span style="background:#EFF6FF;color:#1D4ED8;padding:3px 10px;border-radius:12px;font-size:0.8rem;border:1px solid #BFDBFE;">
    🔵 Obligatoire brouillon
  </span>
  <span style="background:#FFF7ED;color:#C2410C;padding:3px 10px;border-radius:12px;font-size:0.8rem;border:1px solid #FED7AA;">
    🟠 Obligatoire à la soumission (manager)
  </span>
  <span style="background:#F0FDF4;color:#166534;padding:3px 10px;border-radius:12px;font-size:0.8rem;border:1px solid #BBF7D0;">
    🔒 Rempli automatiquement
  </span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# MODES SPÉCIAUX
# ══════════════════════════════════════════════════════════════════════
col_m1, col_m2 = st.columns(2)
with col_m1:
    mode_urgent = st.toggle(
        "⚡ Demande urgente — hors cycle trimestriel",
        value=st.session_state.get("mode_urgent", False),
        key="mode_urgent",
    )
with col_m2:
    mode_sans_eotp = st.toggle(
        "🔓 Créer sans EOTP (saisie manuelle)",
        value=st.session_state.get("mode_sans_eotp", False),
        key="mode_sans_eotp",
    )

if mode_urgent and mode_sans_eotp:
    st.markdown("""<div style="background:#FEF3C7;border-left:4px solid #F59E0B;
        border-radius:0 10px 10px 0;padding:0.75rem 1rem;margin:0.5rem 0;font-size:0.84rem;color:#92400E;">
        ⚡🔓 <b>Mode Urgent + Sans EOTP</b> — Saisie manuelle, hors cycle.
        Une <b>justification obligatoire</b> est requise.</div>""", unsafe_allow_html=True)
elif mode_urgent:
    st.markdown("""<div style="background:#FEF3C7;border-left:4px solid #F59E0B;
        border-radius:0 10px 10px 0;padding:0.75rem 1rem;margin:0.5rem 0;font-size:0.84rem;color:#92400E;">
        ⚡ <b>Demande urgente</b> — Traitée <b>hors cycle d'attribution standard</b>.
        Justification obligatoire.</div>""", unsafe_allow_html=True)
elif mode_sans_eotp:
    st.markdown("""<div style="background:#EFF6FF;border-left:4px solid #3B82F6;
        border-radius:0 10px 10px 0;padding:0.75rem 1rem;margin:0.5rem 0;font-size:0.84rem;color:#1D4ED8;">
        🔓 <b>Mode sans EOTP</b> — Renseignez manuellement le projet et le manager.
        Justification obligatoire.</div>""", unsafe_allow_html=True)
else:
    st.markdown("""<div style="background:#F0FDF4;border-left:4px solid #22C55E;
        border-radius:0 10px 10px 0;padding:0.75rem 1rem;margin:0.5rem 0;font-size:0.84rem;color:#15803D;">
        ✅ <b>Mode standard</b> — EOTP obligatoire, attribution sur le cycle trimestriel.</div>""",
        unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 1 — EOTP (point d'entrée obligatoire)
# ══════════════════════════════════════════════════════════════════════
eotp_found = False
eotp_projet = ""
eotp_manager = ""
eotp_tension = ""
eotp_centre = ""

if not mode_sans_eotp:
    st.markdown("""<div style="background:linear-gradient(135deg,#0E86D4,#00B4D8);
        border-radius:14px;padding:1.2rem 1.8rem;margin:0 0 1.2rem;
        box-shadow:0 4px 20px rgba(14,134,212,0.2);">
        <div style="color:#FFFFFF;font-weight:700;font-size:1rem;">🔍 Étape 1 — EOTP <span style="font-size:0.8rem;opacity:0.85">(point d'entrée obligatoire)</span></div>
        <div style="color:rgba(255,255,255,0.85);font-size:0.82rem;">
        Sélectionnez votre EOTP de niveau 2. Nom du projet et manager seront remplis automatiquement.</div>
    </div>""", unsafe_allow_html=True)

    eotp_list = get_eotp_list()
    eotp2 = st.selectbox("EOTP de niveau 2 🔵 *", [PLACEHOLDER] + eotp_list, key="eotp_select")
    if eotp2 and eotp2 != PLACEHOLDER:
        result = lookup_eotp(eotp2)
        if result["found"]:
            eotp_found = True
            eotp_projet  = result["projet"]
            eotp_manager = result["manager"]
            eotp_tension = result.get("tension", "")
            eotp_centre  = result.get("centre", "")
            st.success(f"✅ EOTP trouvé — **{eotp_projet}** · Manager : **{eotp_manager}**")
        else:
            st.error("❌ EOTP non trouvé dans la base de données.")
    else:
        eotp2 = ""
else:
    eotp2 = ""
    eotp_found = True

# ══════════════════════════════════════════════════════════════════════
# ÉTAPE 2 — JUSTIFICATION (urgence ou sans EOTP)
# ══════════════════════════════════════════════════════════════════════
justification_val = ""
if mode_urgent or mode_sans_eotp:
    if mode_urgent and mode_sans_eotp:
        label_just = "Justification (urgence + absence EOTP) 🔵 *"
    elif mode_urgent:
        label_just = "Justification de l'urgence 🔵 *"
    else:
        label_just = "Justification (absence EOTP) 🔵 *"
    justification_val = st.text_area(label_just, key="justification_urgence_eotp",
        placeholder="Décrivez la raison de cette demande spéciale...", height=80)

# ══════════════════════════════════════════════════════════════════════
# TYPE DE PROJET — contrôle la visibilité des sections
# ══════════════════════════════════════════════════════════════════════
st.markdown("""<div style="background:linear-gradient(135deg,#7C3AED,#A78BFA);
    border-radius:14px;padding:1rem 1.5rem;margin:0 0 1rem;
    box-shadow:0 4px 20px rgba(124,58,237,0.2);">
    <div style="color:#FFFFFF;font-weight:700;font-size:1rem;">📐 Type de projet</div>
    <div style="color:rgba(255,255,255,0.85);font-size:0.82rem;">
    Détermine les sections techniques et jalons à renseigner.</div>
</div>""", unsafe_allow_html=True)

type_projet = st.selectbox(
    "Type de projet 🔵 *",
    [PLACEHOLDER] + TYPES_PROJET,
    key="type_projet_select",
    help="LA = Lignes Aériennes · LS = Liaisons Souterraines · Mixte = les deux.",
)

# Résoudre le type sélectionné (pour logique conditionnelle)
tp = clean_select(type_projet) if type_projet != PLACEHOLDER else ""
show_la = tp in ("LA", "Mixte")
show_ls = tp in ("LS", "Mixte")

if tp:
    labels = []
    if show_la:
        labels.append("🗼 LA (Lignes Aériennes)")
    if show_ls:
        labels.append("🔌 LS (Liaisons Souterraines)")
    st.markdown(
        f'<div style="font-size:0.82rem;color:#6D28D9;margin:-0.5rem 0 0.5rem;">'
        f'Sections actives : {" + ".join(labels)}</div>',
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════
# FORMULAIRE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════
cal         = get_attribution_calendar()
available_q = cal["available_labels"]
target_label = cal["target_label"]

with st.form("form_nouvelle_demande", clear_on_submit=False):

    # ── Section : Informations Générales ─────────────────────────────
    with st.expander("📋 Informations Générales", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            if mode_sans_eotp:
                projet_val = st.text_input("Nom de l'ouvrage / projet 🔵 *", key="projet_manuel")
            else:
                st.text_input("Nom de l'ouvrage / projet 🔒", value=eotp_projet, disabled=True)
                projet_val = eotp_projet
        with c2:
            if mode_sans_eotp:
                manager_val = st.text_input("Manager de projet 🔒", key="manager_manuel",
                    help="Renseigné automatiquement depuis l'EOTP en mode standard.")
            else:
                st.text_input("Manager de projet 🔒", value=eotp_manager, disabled=True)
                manager_val = eotp_manager

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if mode_urgent:
                st.markdown(
                    '<div style="font-size:0.82rem;color:#92400E;background:#FEF3C7;'
                    'border-radius:8px;padding:0.4rem 0.7rem;margin-top:1.5rem;">'
                    '⚡ Hors cycle</div>', unsafe_allow_html=True)
                trimestre = "URGENT"
            else:
                st.markdown(
                    f'<div style="font-size:0.72rem;color:#92400E;background:#FFFBEB;'
                    f'border:1px solid #FDE68A;border-radius:6px;padding:0.3rem 0.6rem;'
                    f'margin-bottom:0.3rem;">📅 Prochaine : <b>{target_label}</b></div>',
                    unsafe_allow_html=True)
                trimestre = st.selectbox(
                    "Trimestre d'attribution 🔵 *",
                    [PLACEHOLDER] + available_q,
                    index=1,
                )
        with c2:
            date_fiche = st.date_input("Date fiche ATP", value=datetime.date.today())
        with c3:
            n_fiche = st.text_input("N° Fiche ATP 🔒", disabled=True,
                help="Généré automatiquement à la création.")
        with c4:
            centre_di = st.text_input("Centre DI 🔵 *", value=eotp_centre)

        c1, c2, c3 = st.columns(3)
        with c1:
            ruo = st.text_input("RUO 🔵 *")
        with c2:
            eotp2_display = eotp2 if (eotp2 and eotp2 != PLACEHOLDER) else ""
            st.text_input("EOTP2 🔒", value=eotp2_display, disabled=True)
        with c3:
            tension_default = eotp_tension
            tension_idx = (TENSIONS.index(tension_default) + 1) if tension_default in TENSIONS else 0
            tension = st.selectbox("Tension 🔵 *", [PLACEHOLDER] + TENSIONS, index=tension_idx)

        resume = st.text_area("Résumé du projet 🔵 *", height=100,
            placeholder="Décrivez brièvement l'objet et le contexte du projet...")

        # ── Contacts ──────────────────────────────────────────────────
        st.markdown("**Contacts** — *champs obligatoires à la soumission*")
        c1, c2, c3 = st.columns(3)
        with c1:
            tel_manager = st.text_input("Téléphone du manager 🟠",
                help="Obligatoire lors de la soumission par le manager.")
        with c2:
            charge = st.text_input("Chargé d'études 🟠")
        with c3:
            tel_charge = st.text_input("Tél. chargé d'études 🟠")

        # ── Nombre de lots ────────────────────────────────────────────
        st.markdown("---")
        st.markdown("**🗂️ Gestion des lots**")
        nbre_lots = st.radio(
            "Nombre de lots d'études 🟠",
            options=["1", "2"], horizontal=True,
            help="Obligatoire à la soumission. Si 2 lots, deux entreprises peuvent être attribuées.",
        )
        if nbre_lots == "2":
            st.info("ℹ️ 2 lots — deux entreprises d'études pourront être désignées (Lot 1 et Lot 2).")

    # ── Section : Données Techniques LA ──────────────────────────────
    if show_la:
        with st.expander("🗼 Données Techniques — Lignes Aériennes (LA)", expanded=True):
            info_box("🔵 Champs obligatoires pour le brouillon : Typologie, Longueur, Pylônes, LIDAR. "
                     "🟠 Géotechnique et Conventions requis à la soumission.")

            c1, c2, c3 = st.columns(3)
            with c1:
                la_typo = st.selectbox("Typologie LA 🔵 *", [PLACEHOLDER] + TYPOLOGIES_PROJET)
            with c2:
                la_longueur = st.number_input("Longueur liaison (km) 🔵 *",
                    min_value=0.0, value=0.0, step=0.1, key="la_long")
            with c3:
                la_pylones = st.number_input("Nb pylônes à traiter 🔵 *",
                    min_value=0, value=0, step=1, key="la_pyl")

            c1, c2, c3 = st.columns(3)
            with c1:
                la_lidar = st.selectbox("Besoin LIDAR 🔵 *", [PLACEHOLDER, "Oui", "Non"])
            with c2:
                la_geotech = st.checkbox("Géotechnique existante 🟠", key="la_geotech")
            with c3:
                la_conv = st.number_input("Nbre conventions estimé 🟠",
                    min_value=0, value=0, step=1, key="la_conv")

    # ── Section : Données Techniques LS ──────────────────────────────
    if show_ls:
        with st.expander("🔌 Données Techniques — Liaisons Souterraines (LS)", expanded=True):
            info_box("🔵 Obligatoires brouillon : Typologie, Type liaison, Linéaires tracé/détails, "
                     "Répartition milieu (%), Franchissement. "
                     "🟠 Linéaire faisabilité + domaine public/privé requis à la soumission.")

            c1, c2 = st.columns(2)
            with c1:
                ls_typo = st.selectbox("Typologie LS 🔵 *", [PLACEHOLDER] + TYPOLOGIES_PROJET)
            with c2:
                ls_type_liaison = st.selectbox("Type de liaison 🔵 *",
                    [PLACEHOLDER] + TYPES_LIAISON_LS)

            c1, c2, c3 = st.columns(3)
            with c1:
                ls_fais = st.number_input("Linéaire études de faisabilité (km) 🟠",
                    min_value=0.0, value=0.0, step=0.1, key="ls_fais",
                    help="Obligatoire à la soumission.")
            with c2:
                ls_trace = st.number_input("Linéaire études de tracé (km) 🔵 *",
                    min_value=0.0, value=0.0, step=0.1, key="ls_trace")
            with c3:
                ls_det = st.number_input("Linéaire études de détails (km) 🔵 *",
                    min_value=0.0, value=0.0, step=0.1, key="ls_det")

            st.markdown("**Répartition du milieu (%) 🔵** — *La somme doit être ≤ 100*")
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: ls_pct_rural = st.number_input("% Rural", min_value=0, max_value=100, value=0, key="ls_rural")
            with c2: ls_pct_urbain = st.number_input("% Urbain", min_value=0, max_value=100, value=0, key="ls_urbain")
            with c3: ls_pct_ud = st.number_input("% Urbain dense", min_value=0, max_value=100, value=0, key="ls_ud")
            with c4: ls_pct_poste = st.number_input("% Poste", min_value=0, max_value=100, value=0, key="ls_poste")
            with c5: ls_pct_gal = st.number_input("% Galerie", min_value=0, max_value=100, value=0, key="ls_gal")

            total_pct = ls_pct_rural + ls_pct_urbain + ls_pct_ud + ls_pct_poste + ls_pct_gal
            if total_pct > 0:
                color = "#22C55E" if total_pct <= 100 else "#EF4444"
                st.markdown(
                    f'<div style="font-size:0.82rem;color:{color};margin-top:-0.5rem;">'
                    f'Somme répartition : <b>{total_pct}%</b>'
                    + (" ✅" if total_pct <= 100 else " ⚠️ Dépasse 100%")
                    + '</div>', unsafe_allow_html=True)

            ls_franchissement = st.selectbox(
                "Franchissement complexe ? (Autoroute, Départementale…) 🔵 *",
                [PLACEHOLDER, "Oui", "Non"])

            st.markdown("**Domaine 🟠** — *Obligatoire à la soumission*")
            c1, c2 = st.columns(2)
            with c1: ls_pub = st.number_input("% domaine public estimé 🟠", min_value=0, max_value=100, value=0, key="ls_pub")
            with c2: ls_priv = st.number_input("% domaine privé 🟠", min_value=0, max_value=100, value=0, key="ls_priv")

    # ── Section : Jalons ─────────────────────────────────────────────
    with st.expander("📅 Jalons"):
        if show_la:
            st.markdown("**Jalons LA (commande) 🔵/🟠**")
            c1, c2 = st.columns(2)
            with c1:
                j_la_fin = st.date_input("Fin souhaitée études détails (LA) 🔵 *",
                    value=None, key="j_la_fin")
                j_la_fais = st.date_input("Fin faisabilité (DCT) (LA) 🟠",
                    value=None, key="j_la_fais")
                j_consult = st.date_input("Date consultation (envoi CCTP) 🟠",
                    value=None, key="j_consult")
            with c2:
                j_la_deb = st.date_input("Début souhaité études détails (LA) 🟠",
                    value=None, key="j_la_deb")
                j_notif = st.date_input("Date notification commande 🟠",
                    value=None, key="j_notif")

        if show_ls:
            st.markdown("**Jalons LS 🔵/🟠**")
            c1, c2 = st.columns(2)
            with c1:
                j_ls_fin = st.date_input("Fin étude de détail (LS) 🔵 *",
                    value=None, key="j_ls_fin")
                j_ls_fais = st.date_input("Fin faisabilité (LS) 🟠",
                    value=None, key="j_ls_fais")
            with c2:
                j_ls_trace = st.date_input("Fin études de tracé (LS) 🟠",
                    value=None, key="j_ls_trace")

        if not show_la and not show_ls:
            info_box("⬆️ Sélectionnez un type de projet pour afficher les jalons correspondants.")

    # ── Section : Montants ────────────────────────────────────────────
    with st.expander("💰 Montants estimés"):
        if show_la and show_ls:
            info_box("🔵 Les montants LA et LS sont obligatoires pour le brouillon.")
            c1, c2, c3 = st.columns(3)
            with c1:
                montant_la = st.number_input("Montant LA (k€) 🔵 *", min_value=0.0, value=0.0, step=1.0)
            with c2:
                montant_ls = st.number_input("Montant LS (k€) 🔵 *", min_value=0.0, value=0.0, step=1.0)
            with c3:
                montant_total = montant_la + montant_ls
                st.metric("Montant Total (k€) 🔒", f"{montant_total:.1f}")
        elif show_la:
            info_box("🔵 Le montant LA est obligatoire pour le brouillon.")
            c1, c2 = st.columns(2)
            with c1:
                montant_la = st.number_input("Montant LA (k€) 🔵 *", min_value=0.0, value=0.0, step=1.0)
            with c2:
                montant_ls = 0.0
                montant_total = montant_la
                st.metric("Montant Total (k€) 🔒", f"{montant_total:.1f}")
        elif show_ls:
            info_box("🔵 Le montant LS est obligatoire pour le brouillon.")
            c1, c2 = st.columns(2)
            with c1:
                montant_ls = st.number_input("Montant LS (k€) 🔵 *", min_value=0.0, value=0.0, step=1.0)
            with c2:
                montant_la = 0.0
                montant_total = montant_ls
                st.metric("Montant Total (k€) 🔒", f"{montant_total:.1f}")
        else:
            montant_la = 0.0
            montant_ls = 0.0
            montant_total = 0.0
            info_box("⬆️ Sélectionnez un type de projet pour afficher les montants.")

    # ── Section : Préférences d'attribution ──────────────────────────
    with st.expander("🎯 Préférences d'attribution — À compléter à la soumission 🟠"):
        info_box("🟠 Ces champs sont obligatoires lors de la soumission de la demande par le manager.")
        c1, c2, c3 = st.columns(3)
        with c1: pref1 = st.selectbox("Souhait GIE n°1 🟠", [PLACEHOLDER] + GIE_LIST)
        with c2: pref2 = st.selectbox("Souhait GIE n°2 🟠", [PLACEHOLDER] + GIE_LIST)
        with c3: pref3 = st.selectbox("Souhait GIE n°3 🟠", [PLACEHOLDER] + GIE_LIST)
        pref_justif = st.text_area("Justification du choix 🟠", key="pref_just",
            help="Obligatoire à la soumission.")

    # ── SOUMISSION ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div style="background:#EFF6FF;border-left:4px solid #3B82F6;border-radius:0 8px 8px 0;
        padding:0.6rem 1rem;margin-bottom:0.8rem;font-size:0.83rem;color:#1E40AF;">
    💡 <b>Enregistrement en brouillon</b> — Seuls les champs 🔵 sont obligatoires maintenant.
    Le manager complètera les champs 🟠 avant de soumettre la demande.
    </div>""", unsafe_allow_html=True)

    submitted = st.form_submit_button("💾 Enregistrer en brouillon",
                                      use_container_width=True, type="primary")

    if submitted:
        errors = []

        # Validation type de projet
        if not tp:
            errors.append("Type de projet obligatoire — sélectionnez LA, LS ou Mixte")

        # Validation EOTP (point d'entrée)
        if not mode_sans_eotp:
            if not eotp2:
                errors.append("EOTP obligatoire en mode standard — sélectionnez un EOTP")
            elif not eotp_found:
                errors.append("EOTP non trouvé dans la base de données")

        # Validation projet/manager en mode sans EOTP
        if mode_sans_eotp:
            projet_val  = st.session_state.get("projet_manuel", "")
            manager_val = st.session_state.get("manager_manuel", "")
            if not projet_val.strip():
                errors.append("Nom du projet obligatoire")
            if not manager_val.strip():
                errors.append("Manager de projet obligatoire")

        # Validation trimestre
        if not mode_urgent and (not trimestre or trimestre == PLACEHOLDER):
            errors.append("Trimestre d'attribution obligatoire")

        # Validation justification mode spécial
        if (mode_urgent or mode_sans_eotp) and not justification_val.strip():
            errors.append("Justification obligatoire en mode urgent ou sans EOTP")

        # Construction du dict de données pour validation brouillon
        # (uniquement les champs pertinents selon le type de projet)
        data_to_validate = {
            "Centre_DI":       centre_di,
            "RUO":             ruo,
            "Tension":         clean_select(tension),
            "Resume_Projet":   resume,
        }

        if show_la:
            data_to_validate.update({
                "LA_Typologie_Projet":     clean_select(la_typo),
                "LA_Longueur_Liaison_km":  str(la_longueur),
                "LA_Nb_Pylones":           str(la_pylones),
                "LA_Besoin_LIDAR":         clean_select(la_lidar),
                "Jalon_LA_Fin_Details":    str(j_la_fin) if j_la_fin else "",
                "Montant_LA_kE":           str(montant_la),
            })

        if show_ls:
            data_to_validate.update({
                "LS_Typologie_Projet":        clean_select(ls_typo),
                "LS_Type_Liaison":            clean_select(ls_type_liaison),
                "LS_Lineaire_Trace_km":       str(ls_trace),
                "LS_Lineaire_Details_km":     str(ls_det),
                "LS_Pct_Rural":               str(ls_pct_rural),
                "LS_Pct_Urbain":              str(ls_pct_urbain),
                "LS_Pct_Urbain_Dense":        str(ls_pct_ud),
                "LS_Pct_Poste":               str(ls_pct_poste),
                "LS_Pct_Galerie":             str(ls_pct_gal),
                "LS_Franchissement_Complexe": clean_select(ls_franchissement),
                "Jalon_LS_Detail_Fin":        str(j_ls_fin) if j_ls_fin else "",
                "Montant_LS_kE":              str(montant_ls),
            })

        # Validation brouillon type-aware
        if tp:
            champs_manquants = valider_brouillon(data_to_validate, tp)
            if champs_manquants:
                errors.append("Champs 🔵 obligatoires manquants : " + ", ".join(champs_manquants))

        # Vérification somme des pourcentages LS
        if show_ls and total_pct > 100:
            errors.append(f"La somme des pourcentages de milieu LS dépasse 100% (actuel : {total_pct}%)")

        if errors:
            for e in errors:
                st.error(f"⚠️ {e}")
        else:
            data = {
                "Trimestre_Attribution":  "URGENT" if mode_urgent else clean_select(trimestre),
                "Date_Fiche_ATP":         str(date_fiche) if date_fiche else "",
                "N_Fiche_ATP":            "",
                "Centre_DI":              centre_di,
                "RUO":                    ruo,
                "EOTP2":                  eotp2,
                "Tension":                clean_select(tension),
                "Nom_Ouvrage_Projet":     projet_val,
                "Manager_Projet":         manager_val,
                "Type_Projet":            tp,
                "Nbre_Lots_Etudes":       nbre_lots,
                "Resume_Projet":          resume,
                "Tel_Manager":            tel_manager,
                "Charge_Etudes":          charge,
                "Tel_Charge_Etudes":      tel_charge,
                "Urgente":                "Oui" if mode_urgent else "",
                "Sans_EOTP":              "Oui" if mode_sans_eotp else "",
                "Justification_Urgence_EOTP": justification_val,
                # Montants
                "Montant_LA_kE":          str(montant_la),
                "Montant_LS_kE":          str(montant_ls),
                "Montant_Total":          str(montant_total),
                # Préférences (facultatives au brouillon)
                "Pref_GIE_1":             clean_select(pref1),
                "Pref_GIE_2":             clean_select(pref2),
                "Pref_GIE_3":             clean_select(pref3),
                "Pref_Justification":     pref_justif,
            }

            # LA — uniquement si affiché
            if show_la:
                data.update({
                    "LA_Typologie_Projet":    clean_select(la_typo),
                    "LA_Longueur_Liaison_km": str(la_longueur),
                    "LA_Nb_Pylones":          str(la_pylones),
                    "LA_Besoin_LIDAR":        clean_select(la_lidar),
                    "LA_Geotech_Existante":   "Oui" if la_geotech else "Non",
                    "LA_Nbre_Conventions":    str(la_conv),
                    # Jalons LA
                    "Jalon_LA_Fin_Details":              str(j_la_fin)   if j_la_fin   else "",
                    "Jalon_LA_Fin_Faisabilite_DCT":      str(j_la_fais)  if j_la_fais  else "",
                    "Jalon_LA_Debut_Details":            str(j_la_deb)   if j_la_deb   else "",
                    "Jalon_Date_Consultation":           str(j_consult)  if j_consult  else "",
                    "Jalon_Date_Notification_Commande":  str(j_notif)    if j_notif    else "",
                })

            # LS — uniquement si affiché
            if show_ls:
                data.update({
                    "LS_Typologie_Projet":        clean_select(ls_typo),
                    "LS_Type_Liaison":            clean_select(ls_type_liaison),
                    "LS_Lineaire_Faisabilite_km": str(ls_fais),
                    "LS_Lineaire_Trace_km":       str(ls_trace),
                    "LS_Lineaire_Details_km":     str(ls_det),
                    "LS_Pct_Rural":               str(ls_pct_rural),
                    "LS_Pct_Urbain":              str(ls_pct_urbain),
                    "LS_Pct_Urbain_Dense":        str(ls_pct_ud),
                    "LS_Pct_Poste":               str(ls_pct_poste),
                    "LS_Pct_Galerie":             str(ls_pct_gal),
                    "LS_Franchissement_Complexe": clean_select(ls_franchissement),
                    "LS_Pct_Domaine_Public":      str(ls_pub),
                    "LS_Pct_Domaine_Prive":       str(ls_priv),
                    # Jalons LS
                    "Jalon_LS_Detail_Fin":              str(j_ls_fin)   if j_ls_fin   else "",
                    "Jalon_LS_Fin_Faisabilite":         str(j_ls_fais)  if j_ls_fais  else "",
                    "Jalon_LS_Fin_Trace_Preferentiel":  str(j_ls_trace) if j_ls_trace else "",
                })

            try:
                demande_id = ajouter_demande(data, user["email"])
                notify_success(f"Demande créée — ID : {demande_id}")
                st.success(
                    f"✅ Brouillon créé avec succès ! ID : **{demande_id}**\n\n"
                    "Le manager peut maintenant compléter les champs 🟠 et soumettre "
                    "la demande depuis **Mes Demandes**."
                )
            except Exception as e:
                st.error(f"❌ Erreur : {e}")
