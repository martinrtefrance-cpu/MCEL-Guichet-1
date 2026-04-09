"""
data_manager.py — Gestion centralisée de la base de données Excel avec verrouillage fichier.

v18 : Logique conditionnelle LA / LS / Mixte.
  - Type_Projet = "LA" | "LS" | "Mixte" contrôle la visibilité et la validation
  - Suppression des champs absents du fichier Excel de référence :
      LA : Nbre_Circuits, Rural, Urbain, Montagneux, Lineaire_Bois, Etat_Lieux_Drone, TEKLA, PLS_POLE
      LS : Nbre_Franchissement, Nbre_PSO, Nbre_Communes, Raccordement, Besoin_LIDAR
      Général : Depart, Arrivee, Pref_Niveau_Confiance
      Jalons : Fin_Recensement_Patrimoine, Fin_Geotech, LS_Detail_Debut, Fin_Conventionnement, APD, DI
      Geotech : Geo_G1_Commandees, Geo_G2_Commandees
  - Fonctions de validation type-aware : valider_brouillon(data, type_projet)
"""
import os
import pandas as pd
import datetime
import uuid
from filelock import FileLock

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_FILE = os.path.join(DATA_DIR, "guichet_unique_db.xlsx")
LOCK_FILE = DB_FILE + ".lock"
HISTORY_DIR = os.path.join(DATA_DIR, "historique")
SIEPR_FILE = os.path.join(DATA_DIR, "SIEPR.xlsx")

# ── Colonnes par section ──────────────────────────────────────────────
COLONNES_INFO_GENERALES = [
    "ID_Demande", "Statut", "Createur_Email", "Date_Creation", "Trimestre_Attribution",
    "Date_Fiche_ATP", "N_Fiche_ATP", "Centre_DI", "RUO", "EOTP2",
    "Nom_Ouvrage_Projet", "Type_Projet", "Tension",
    "Nbre_Lots_Etudes", "Resume_Projet", "Manager_Projet",
    "Tel_Manager", "Charge_Etudes", "Tel_Charge_Etudes",
    "Urgente", "Sans_EOTP", "Justification_Urgence_EOTP",
]

COLONNES_TECH_LA = [
    "LA_Typologie_Projet",
    "LA_Longueur_Liaison_km",
    "LA_Nb_Pylones",
    "LA_Geotech_Existante",
    "LA_Nbre_Conventions",
    "LA_Besoin_LIDAR",
]

COLONNES_TECH_LS = [
    "LS_Typologie_Projet",
    "LS_Type_Liaison",
    "LS_Lineaire_Faisabilite_km",
    "LS_Lineaire_Trace_km",
    "LS_Lineaire_Details_km",
    "LS_Pct_Rural",
    "LS_Pct_Urbain",
    "LS_Pct_Urbain_Dense",
    "LS_Pct_Poste",
    "LS_Pct_Galerie",
    "LS_Franchissement_Complexe",
    "LS_Pct_Domaine_Public",
    "LS_Pct_Domaine_Prive",
]

COLONNES_JALONS_LA = [
    "Jalon_Date_Consultation",
    "Jalon_Date_Notification_Commande",
    "Jalon_LA_Fin_Faisabilite_DCT",
    "Jalon_LA_Debut_Details",
    "Jalon_LA_Fin_Details",
]

COLONNES_JALONS_LS = [
    "Jalon_LS_Fin_Faisabilite",
    "Jalon_LS_Fin_Trace_Preferentiel",
    "Jalon_LS_Detail_Fin",
]

COLONNES_JALONS = COLONNES_JALONS_LA + COLONNES_JALONS_LS

COLONNES_MONTANT = ["Montant_LA_kE", "Montant_LS_kE", "Montant_Total"]

COLONNES_PREFERENCE = [
    "Pref_GIE_1", "Pref_GIE_2", "Pref_GIE_3",
    "Pref_Justification",
]

COLONNES_ATTRIBUTION = [
    "Attribution_Finale", "Date_Attribution", "Attribue_Par",
    "Attribution_Lot1", "Attribution_Lot2",
]

COLONNES_COMMANDE = [
    "Commande_Numero", "Commande_Date", "Commande_Montant",
    "Commande_Statut", "Commande_Import_Date",
]

COLONNES_HISTORIQUE = [
    "Derniere_Modification", "Modifie_Par",
    "Relance_Count", "Relance_Derniere_Date", "Relance_Historique",
]

ALL_COLUMNS = (
    COLONNES_INFO_GENERALES + COLONNES_TECH_LA + COLONNES_TECH_LS +
    COLONNES_JALONS + COLONNES_MONTANT +
    COLONNES_PREFERENCE + COLONNES_ATTRIBUTION +
    COLONNES_COMMANDE + COLONNES_HISTORIQUE
)

STATUTS = ["Brouillon", "Soumise", "Attribuée", "Commandée", "Annulée"]

STATUTS_COLORS = {
    "Brouillon": "#9E9E9E",
    "Soumise": "#FF9800",
    "Attribuée": "#2196F3",
    "Commandée": "#4CAF50",
    "Annulée": "#F44336",
}

# ══════════════════════════════════════════════════════════════════════
# CHAMPS REQUIS — découpés par section LA / LS pour gestion conditionnelle
#
# Source : nouvelles_données_techniques.xlsx
# Ligne "Données pour soumettre la demande d'étude" → brouillon + soumission
# Ligne "Données pour guichet non engageant" → brouillon uniquement
#
# EOTP2 est géré séparément (point d'entrée obligatoire).
# Les champs auto-remplis (Nom_Ouvrage_Projet, Manager_Projet) ne
# figurent pas ici car ils ne nécessitent pas de saisie utilisateur.
# ══════════════════════════════════════════════════════════════════════

# --- Champs communs (toujours requis quel que soit le type) ---
_BROUILLON_COMMUN: dict = {
    "Centre_DI":       "Centre DI",
    "RUO":             "RUO",
    "Tension":         "Tension",
    "Resume_Projet":   "Résumé du projet",
}

_BROUILLON_LA: dict = {
    "LA_Typologie_Projet":     "Typologie LA",
    "LA_Longueur_Liaison_km":  "Longueur liaison LA (km)",
    "LA_Nb_Pylones":           "Nombre de pylônes à traiter",
    "LA_Besoin_LIDAR":         "Besoin de LIDAR (LA)",
    "Jalon_LA_Fin_Details":    "Fin souhaitée études détails (LA)",
    "Montant_LA_kE":           "Montant LA (k€)",
}

_BROUILLON_LS: dict = {
    "LS_Typologie_Projet":        "Typologie LS",
    "LS_Type_Liaison":            "Type de liaison LS",
    "LS_Lineaire_Trace_km":       "Linéaire études de tracé LS (km)",
    "LS_Lineaire_Details_km":     "Linéaire études de détails LS (km)",
    "LS_Pct_Rural":               "% Rural (LS)",
    "LS_Pct_Urbain":              "% Urbain (LS)",
    "LS_Pct_Urbain_Dense":        "% Urbain dense (LS)",
    "LS_Pct_Poste":               "% Poste (LS)",
    "LS_Pct_Galerie":             "% Galerie (LS)",
    "LS_Franchissement_Complexe": "Franchissement complexe (LS)",
    "Jalon_LS_Detail_Fin":        "Fin étude de détail (LS)",
    "Montant_LS_kE":              "Montant LS (k€)",
}

_SOUMISSION_COMMUN: dict = {
    "Nbre_Lots_Etudes":                 "Nombre de lots d'études",
    "Tel_Manager":                      "Téléphone du manager de projet",
    "Charge_Etudes":                    "Chargé d'études",
    "Tel_Charge_Etudes":                "Téléphone du chargé d'études",
    "Pref_GIE_1":                       "Souhait GIE n°1",
    "Pref_GIE_2":                       "Souhait GIE n°2",
    "Pref_GIE_3":                       "Souhait GIE n°3",
    "Pref_Justification":               "Justification préférence GIE",
}

_SOUMISSION_LA: dict = {
    "LA_Geotech_Existante":             "Géotechnique existante (LA)",
    "LA_Nbre_Conventions":              "Nombre de conventions estimé (LA)",
    "Jalon_Date_Consultation":          "Date consultation (envoi CCTP)",
    "Jalon_Date_Notification_Commande": "Date notification commande",
    "Jalon_LA_Fin_Faisabilite_DCT":     "Fin études de faisabilité LA (DCT)",
    "Jalon_LA_Debut_Details":           "Début souhaité études détails (LA)",
}

_SOUMISSION_LS: dict = {
    "LS_Lineaire_Faisabilite_km":       "Linéaire études de faisabilité LS (km)",
    "LS_Pct_Domaine_Public":            "% domaine public estimé (LS)",
    "LS_Pct_Domaine_Prive":             "% domaine privé (LS)",
    "Jalon_LS_Fin_Faisabilite":         "Fin études de faisabilité (LS)",
    "Jalon_LS_Fin_Trace_Preferentiel":  "Fin études de tracé (LS)",
}


def get_champs_requis_brouillon(type_projet: str = "Mixte") -> dict:
    """Retourne les champs brouillon requis selon le type de projet."""
    champs = dict(_BROUILLON_COMMUN)
    if type_projet in ("LA", "Mixte"):
        champs.update(_BROUILLON_LA)
    if type_projet in ("LS", "Mixte"):
        champs.update(_BROUILLON_LS)
    return champs


def get_champs_requis_soumission(type_projet: str = "Mixte") -> dict:
    """Retourne les champs soumission requis selon le type de projet."""
    champs = dict(_SOUMISSION_COMMUN)
    if type_projet in ("LA", "Mixte"):
        champs.update(_SOUMISSION_LA)
    if type_projet in ("LS", "Mixte"):
        champs.update(_SOUMISSION_LS)
    return champs


# --- Rétro-compatibilité ---
CHAMPS_REQUIS_BROUILLON = get_champs_requis_brouillon("Mixte")
CHAMPS_REQUIS_SOUMISSION = get_champs_requis_soumission("Mixte")


# Champs numériques dont la valeur 0 est acceptable
_CHAMPS_ZERO_OK = {
    "LS_Pct_Rural", "LS_Pct_Urbain", "LS_Pct_Urbain_Dense",
    "LS_Pct_Poste", "LS_Pct_Galerie",
    "Montant_LA_kE", "Montant_LS_kE",
}

# Champs numériques qui doivent être > 0 pour être valides
_CHAMPS_NUMERIQUES_POSITIFS = {
    "LA_Longueur_Liaison_km", "LA_Nb_Pylones",
    "LS_Lineaire_Trace_km", "LS_Lineaire_Details_km",
}


def valider_champs(data: dict, champs: dict) -> list:
    """Vérifie que les champs requis sont renseignés. Retourne les libellés manquants."""
    manquants = []
    for key, label in champs.items():
        val = str(data.get(key, "")).strip()
        if not val or val in ("", "None", "—"):
            manquants.append(label)
        elif key in _CHAMPS_NUMERIQUES_POSITIFS:
            try:
                if float(val) <= 0:
                    manquants.append(label)
            except ValueError:
                manquants.append(label)
    return manquants


def valider_brouillon(data: dict, type_projet: str = "Mixte") -> list:
    """Retourne les libellés des champs brouillon manquants."""
    champs = get_champs_requis_brouillon(type_projet)
    return valider_champs(data, champs)


def valider_soumission(data: dict, type_projet: str = "Mixte") -> list:
    """Valide l'ensemble brouillon + soumission. Retourne les libellés manquants."""
    tous = {**get_champs_requis_brouillon(type_projet),
            **get_champs_requis_soumission(type_projet)}
    return valider_champs(data, tous)


# ──────────────────────────────────────────────────────────────────────
# CALENDRIER D'ATTRIBUTION
# ──────────────────────────────────────────────────────────────────────
import datetime as _dt


def get_attribution_calendar(n_future: int = 6) -> dict:
    now = _dt.datetime.now()
    cy, cm = now.year, now.month
    cq = (cm - 1) // 3 + 1
    q_end_month = {1: 3, 2: 6, 3: 9, 4: 12}
    q_months = {1: "Jan–Mar", 2: "Avr–Juin", 3: "Juil–Sep", 4: "Oct–Déc"}
    quarters = []
    for offset in range(-1, n_future - 1):
        q, y = cq + offset, cy
        while q > 4: q -= 4; y += 1
        while q < 1: q += 4; y -= 1
        quarters.append((y, q))
    days_left = (_dt.date(cy, q_end_month[cq], 28) - now.date()).days
    target = quarters[3] if days_left < 30 else quarters[2]
    ty, tq = target
    target_label = f"T{tq} {ty}"
    target_idx = quarters.index(target)
    available_labels = [f"T{q} {y}" for y, q in quarters[target_idx:]]
    return {
        "quarters": quarters, "current": (cy, cq), "target": target,
        "target_label": target_label, "available_labels": available_labels,
        "q_months": q_months,
    }


TRIMESTRES = get_attribution_calendar()["available_labels"]
TENSIONS = ["400 kV", "225 kV", "150 kV", "90 kV", "63 kV", "Autre"]
TYPES_PROJET = ["LA", "LS", "Mixte"]
TYPOLOGIES_PROJET = ["Création", "Renouvellement", "Renforcement", "Modification", "Dépose"]
TYPES_LIAISON_LS = ["Câble souterrain", "Câble sous-marin", "Câble en galerie", "Autre"]
GIE_LIST = [
    "GIE 1 - Nom Entreprise A",
    "GIE 2 - Nom Entreprise B",
    "GIE 3 - Nom Entreprise C",
    "GIE 4 - Nom Entreprise D",
    "GIE 5 - Nom Entreprise E",
]


def ensure_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=ALL_COLUMNS)
        df.to_excel(DB_FILE, index=False, engine="openpyxl")
    return DB_FILE


def load_data() -> pd.DataFrame:
    ensure_db()
    lock = FileLock(LOCK_FILE, timeout=10)
    with lock:
        df = pd.read_excel(DB_FILE, engine="openpyxl", dtype=str)
    for col in ALL_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df


def load_user_data(user_email: str, is_admin: bool = False) -> pd.DataFrame:
    df = load_data()
    if is_admin or not user_email:
        return df
    return df[df["Createur_Email"].str.lower() == user_email.lower()].copy()


def save_data(df: pd.DataFrame):
    ensure_db()
    lock = FileLock(LOCK_FILE, timeout=10)
    with lock:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = os.path.join(HISTORY_DIR, f"backup_{timestamp}.xlsx")
        if os.path.exists(DB_FILE):
            import shutil
            shutil.copy2(DB_FILE, backup)
        df.to_excel(DB_FILE, index=False, engine="openpyxl")
    backups = sorted([f for f in os.listdir(HISTORY_DIR) if f.startswith("backup_")])
    while len(backups) > 50:
        os.remove(os.path.join(HISTORY_DIR, backups.pop(0)))


def generate_id() -> str:
    return f"DEM-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


def ajouter_demande(data: dict, utilisateur: str = "Système") -> str:
    df = load_data()
    demande_id = generate_id()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    row = {col: "" for col in ALL_COLUMNS}
    row.update(data)
    row["ID_Demande"] = demande_id
    row["Statut"] = "Brouillon"
    row["Createur_Email"] = utilisateur
    row["Date_Creation"] = now
    row["Derniere_Modification"] = now
    row["Modifie_Par"] = utilisateur
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_data(df)
    return demande_id


def modifier_demande(demande_id: str, data: dict, utilisateur: str = "Système"):
    df = load_data()
    mask = df["ID_Demande"] == demande_id
    if mask.sum() == 0:
        raise ValueError(f"Demande {demande_id} introuvable.")
    statut = df.loc[mask, "Statut"].values[0]
    if statut in ("Attribuée", "Commandée"):
        raise PermissionError(f"La demande {demande_id} est '{statut}' et ne peut plus être modifiée.")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    for key, val in data.items():
        if key in ALL_COLUMNS:
            df.loc[mask, key] = val
    df.loc[mask, "Derniere_Modification"] = now
    df.loc[mask, "Modifie_Par"] = utilisateur
    save_data(df)


def soumettre_demande(demande_id: str, utilisateur: str = "Système"):
    df = load_data()
    mask = df["ID_Demande"] == demande_id
    if mask.sum() == 0:
        raise ValueError(f"Demande {demande_id} introuvable.")
    df.loc[mask, "Statut"] = "Soumise"
    df.loc[mask, "Derniere_Modification"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    df.loc[mask, "Modifie_Par"] = utilisateur
    save_data(df)


def attribuer_demande(demande_id: str, gie: str, utilisateur: str = "Système",
                      gie_lot2: str = "") -> None:
    df = load_data()
    mask = df["ID_Demande"] == demande_id
    if mask.sum() == 0:
        raise ValueError(f"Demande {demande_id} introuvable.")
    nbre_lots = str(df.loc[mask, "Nbre_Lots_Etudes"].iloc[0]).strip()
    if nbre_lots == "2" and not gie_lot2:
        raise ValueError("2 lots demandés : l'attribution du Lot 2 est obligatoire.")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    df.loc[mask, "Statut"] = "Attribuée"
    df.loc[mask, "Date_Attribution"] = now
    df.loc[mask, "Attribue_Par"] = utilisateur
    df.loc[mask, "Derniere_Modification"] = now
    df.loc[mask, "Modifie_Par"] = utilisateur
    if nbre_lots == "2" and gie_lot2:
        df.loc[mask, "Attribution_Lot1"] = gie
        df.loc[mask, "Attribution_Lot2"] = gie_lot2
        df.loc[mask, "Attribution_Finale"] = f"Lot1: {gie} | Lot2: {gie_lot2}"
    else:
        df.loc[mask, "Attribution_Lot1"] = gie
        df.loc[mask, "Attribution_Lot2"] = ""
        df.loc[mask, "Attribution_Finale"] = gie
    save_data(df)


def annuler_demande(demande_id: str, utilisateur: str = "Système"):
    df = load_data()
    mask = df["ID_Demande"] == demande_id
    if mask.sum() == 0:
        raise ValueError(f"Demande {demande_id} introuvable.")
    df.loc[mask, "Statut"] = "Annulée"
    df.loc[mask, "Derniere_Modification"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    df.loc[mask, "Modifie_Par"] = utilisateur
    save_data(df)


def importer_commandes(df_commandes: pd.DataFrame, col_mapping: dict, utilisateur: str = "Système") -> dict:
    df = load_data()
    stats = {"matched": 0, "unmatched": 0, "errors": []}
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    for _, row in df_commandes.iterrows():
        eotp = str(row.get(col_mapping.get("EOTP2", ""), "")).strip()
        if not eotp:
            stats["unmatched"] += 1
            continue
        mask = df["EOTP2"] == eotp
        if mask.sum() == 0:
            stats["unmatched"] += 1
            continue
        df.loc[mask, "Statut"] = "Commandée"
        for field in ("Commande_Numero", "Commande_Date", "Commande_Montant"):
            if field in col_mapping:
                df.loc[mask, field] = str(row.get(col_mapping[field], ""))
        df.loc[mask, "Commande_Statut"] = "Confirmée"
        df.loc[mask, "Commande_Import_Date"] = now
        df.loc[mask, "Derniere_Modification"] = now
        df.loc[mask, "Modifie_Par"] = utilisateur
        stats["matched"] += 1
    save_data(df)
    return stats


def get_kpi(df: pd.DataFrame) -> dict:
    total = len(df)
    if total == 0:
        return {"total": 0, "brouillon": 0, "soumises": 0,
                "attribuees": 0, "commandees": 0, "annulees": 0,
                "taux_attribution": 0, "taux_commande": 0}
    return {
        "total": total,
        "brouillon": len(df[df["Statut"] == "Brouillon"]),
        "soumises": len(df[df["Statut"] == "Soumise"]),
        "attribuees": len(df[df["Statut"] == "Attribuée"]),
        "commandees": len(df[df["Statut"] == "Commandée"]),
        "annulees": len(df[df["Statut"] == "Annulée"]),
        "taux_attribution": round(
            len(df[df["Statut"].isin(["Attribuée", "Commandée"])]) / total * 100, 1),
        "taux_commande": round(len(df[df["Statut"] == "Commandée"]) / total * 100, 1),
    }


# ══════════════════════════════════════════════════════════════════════
# RELANCES — Historique des relances manager
# ══════════════════════════════════════════════════════════════════════
import json as _json


def enregistrer_relance(demande_id: str, utilisateur: str = "Système",
                        destinataire: str = "", contexte: str = "") -> None:
    """Enregistre une relance dans l'historique de la demande."""
    df = load_data()
    mask = df["ID_Demande"] == demande_id
    if mask.sum() == 0:
        raise ValueError(f"Demande {demande_id} introuvable.")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Incrémenter le compteur
    count_raw = df.loc[mask, "Relance_Count"].iloc[0]
    try:
        count = int(float(count_raw)) if pd.notna(count_raw) and str(count_raw).strip() else 0
    except (ValueError, TypeError):
        count = 0
    count += 1

    # Lire l'historique existant
    hist_raw = df.loc[mask, "Relance_Historique"].iloc[0]
    try:
        historique = _json.loads(str(hist_raw)) if pd.notna(hist_raw) and str(hist_raw).strip() else []
    except (_json.JSONDecodeError, ValueError):
        historique = []

    historique.append({
        "date": now,
        "par": utilisateur,
        "destinataire": destinataire,
        "contexte": contexte,
    })

    df.loc[mask, "Relance_Count"] = str(count)
    df.loc[mask, "Relance_Derniere_Date"] = now
    df.loc[mask, "Relance_Historique"] = _json.dumps(historique, ensure_ascii=False)
    save_data(df)


def get_relance_historique(row) -> list:
    """Parse l'historique de relances d'une row pandas. Retourne une liste de dicts."""
    hist_raw = row.get("Relance_Historique", "")
    try:
        return _json.loads(str(hist_raw)) if pd.notna(hist_raw) and str(hist_raw).strip() else []
    except (_json.JSONDecodeError, ValueError):
        return []


# ══════════════════════════════════════════════════════════════════════
# SIEPR — Référentiel EOTP
# ══════════════════════════════════════════════════════════════════════
_siepr_cache = None


def load_siepr() -> pd.DataFrame:
    global _siepr_cache
    if _siepr_cache is not None:
        return _siepr_cache
    if not os.path.exists(SIEPR_FILE):
        return pd.DataFrame()
    _siepr_cache = pd.read_excel(SIEPR_FILE, dtype=str)
    return _siepr_cache


def get_eotp_list() -> list:
    df = load_siepr()
    if df.empty:
        return []
    return sorted(df["EOTP de niveau 2"].dropna().unique().tolist())


def lookup_eotp(eotp: str) -> dict:
    df = load_siepr()
    if df.empty or not eotp:
        return {"found": False}
    match = df[df["EOTP de niveau 2"] == eotp]
    if match.empty:
        return {"found": False}
    row = match.iloc[0]
    return {
        "found": True,
        "manager": str(row.get("Manager de Projet", "")),
        "projet": str(row.get("Nom projet", "")),
        "tension": str(row.get("Tension", "")),
        "domaine": str(row.get("Domaine technique", "")),
        "centre": str(row.get("Centre du commanditaire", "")),
    }
