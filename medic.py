# medic.py
import pandas as pd
import re

DATA_FILE = "data/pfaf_plants_merged_clean.csv"

# =========================================================
# Load data
# =========================================================
def load_plants():
    df = pd.read_csv(DATA_FILE, low_memory=False)
    df.columns = df.columns.str.strip()
    df = df.fillna("")
    return df

plants_df = load_plants()

# =========================================================
# Ratings → human language
# =========================================================
def edibility_description(r):
    try:
        r = float(r)
    except:
        return "of unknown edibility"

    if r <= 1:
        return "not commonly eaten and usually considered an emergency food"
    elif r <= 3:
        return "moderately edible"
    else:
        return "highly edible and an important food plant"

def medicinal_description(r):
    try:
        r = float(r)
    except:
        return "of uncertain medicinal value"

    if r <= 1:
        return "of limited medicinal use"
    elif r == 2:
        return "of moderate medicinal importance"
    else:
        return "highly valued for its medicinal properties"

# =========================================================
# Text cleaning utilities
# =========================================================
def strip_references(text):
    return re.sub(r"\[[^\]]*\]", "", text)

def normalize_spacing(text):
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s([.,])", r"\1", text)
    return text.strip()

def semicolon_to_sentence(text):
    if ";" not in text:
        return text
    parts = [p.strip() for p in text.split(";") if p.strip()]
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + ", and " + parts[-1]

# =========================================================
# Proper PFAF parsing
# =========================================================
def extract_edible_parts(text):
    match = re.search(r"Edible Parts:\s*(.*?)\s*(Edible Uses:|$)", text, re.I)
    return match.group(1).strip() if match else ""

def extract_edible_uses(text):
    match = re.search(r"Edible Uses:\s*(.*)", text, re.I)
    if not match:
        return ""
    uses = match.group(1)
    uses = re.sub(r"\bEdible Parts:.*", "", uses, flags=re.I)
    uses = re.sub(r"\bUses:.*", "", uses, flags=re.I)
    return uses.strip()

def clean_general_text(text):
    text = strip_references(text)
    remove_labels = [
        "Medicinal Properties:", "Other Uses:", "Propagation:",
        "Care Requirements:", "Uses:", "Edible :"
    ]
    for label in remove_labels:
        text = re.sub(rf"\b{re.escape(label)}\b", "", text, flags=re.I)
    text = re.sub(r"\b\d+\.\s*", "", text)
    return normalize_spacing(text)

# =========================================================
# Illness meaning map
# =========================================================
ILLNESS_MEANINGS = {
    "stomachic": "supports digestion and overall stomach health",
    "carminative": "may help reduce gas, bloating, and digestive discomfort",
    "antibacterial": "may help inhibit the growth of harmful bacteria",
    "antifungal": "may assist in managing fungal infections",
    "febrifuge": "has traditionally been used to help reduce fever",
    "antipyretic": "may help lower elevated body temperature",
    "diuretic": "supports urine flow and kidney function",
    "laxative": "may assist in relieving constipation",
    "astringent": "may help tighten tissues and reduce secretions",
    "expectorant": "may help clear mucus from the respiratory system",
    "tonic": "traditionally used to strengthen and support the body",
}

def illness_sentence(medicinal_props, illness):
    props = [p.strip().lower() for p in medicinal_props.split(";")]
    illness = illness.lower()
    if illness in props:
        return ILLNESS_MEANINGS.get(
            illness,
            f"has traditionally been used in relation to {illness}"
        )
    return ""

# =========================================================
# Convert plant row → JSON
# =========================================================
def plant_to_json(row):
    raw_edible = row.get("Edible Uses", "")
    edible_parts = semicolon_to_sentence(clean_general_text(extract_edible_parts(raw_edible)))
    edible_uses = clean_general_text(extract_edible_uses(raw_edible))
    medicinal_props = semicolon_to_sentence(clean_general_text(row.get("Medicinal Properties", "")))
    other_uses = semicolon_to_sentence(clean_general_text(row.get("Other Uses", "")))
    care = semicolon_to_sentence(clean_general_text(row.get("Care Requirements", "")))
    propagation = clean_general_text(row.get("Propagation", ""))

    return {
        "name": row.get("Common Name", ""),
        "scientific_name": row.get("Scientific Name", ""),
        "edibility_rating": row.get("Edibility Rating", ""),
        "edibility_description": edibility_description(row.get("Edibility Rating", "")),
        "edible_parts": edible_parts,
        "edible_uses": edible_uses,
        "medicinal_rating": row.get("Medicinal Rating", ""),
        "medicinal_description": medicinal_description(row.get("Medicinal Rating", "")),
        "medicinal_properties": medicinal_props,
        "other_uses": other_uses,
        "care": care,
        "propagation": propagation,
        "source_url": row.get("plant_url", "#")
    }

# =========================================================
# Convert illness row → JSON
# =========================================================
def illness_to_json(row, illness):
    plant_json = plant_to_json(row)
    illness_text = illness_sentence(plant_json["medicinal_properties"], illness)
    plant_json["illness_search"] = {
        "illness": illness,
        "description": illness_text
    }
    return plant_json

# =========================================================
# Search
# =========================================================
def search(query, search_type="plant"):
    query = query.lower()
    results = []

    if search_type == "plant":
        df = plants_df[
            plants_df["Common Name"].str.lower().str.contains(query) |
            plants_df["Common Names"].str.lower().str.contains(query) |
            plants_df["Scientific Name"].str.lower().str.contains(query)
        ]
        for _, row in df.iterrows():
            results.append(plant_to_json(row))

    elif search_type == "illness":
        df = plants_df[
            plants_df["Medicinal Properties"].str.lower().str.contains(query)
        ]
        for _, row in df.iterrows():
            results.append(illness_to_json(row, query))

    return results
