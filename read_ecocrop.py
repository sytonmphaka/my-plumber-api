# read_ecocrop.py
import pandas as pd
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "ecocrop_utf8.csv"




GROUPS_FILE = Path(__file__).parent / "data" / "groups.txt"


def load_crop_groups():
    """
    Reads groups.txt and returns:
    {
      "okra": "VEGETABLES",
      "maize": "CEREALS & PSEUDO-CEREALS",
      ...
    }
    """
    groups = {}
    current_group = None

    with open(GROUPS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Detect group headers (ALL CAPS words)
            if line.isupper():
                current_group = line
                continue

            # Ignore emoji-only titles like 🌾 FOOD CROPS
            if any(char.isalpha() for char in line) and current_group:
                crop_name = line.lower()
                groups[crop_name] = current_group

    return groups










def load_ecocrop_data():
    try:
        df = pd.read_csv(DATA_FILE, encoding="utf-8")
        print(f"CSV loaded successfully with utf-8! {len(df)} rows, {len(df.columns)} columns")
        return df
    except UnicodeDecodeError:
        print("UTF-8 failed, trying latin1 encoding...")
        df = pd.read_csv(DATA_FILE, encoding="latin1")
        print(f"CSV loaded successfully with latin1! {len(df)} rows, {len(df.columns)} columns")
        return df
    except FileNotFoundError:
        print(f"File not found: {DATA_FILE}")
    except Exception as e:
        print(f"Error reading CSV: {e}")

# --- New function: find crops by soil properties ---
from collections import defaultdict



def safe_str(value):
    if isinstance(value, str):
        return value.strip()
    return ""

def find_crops_by_soil(fertility: str, drainage: str, texture: str, df=None):

    if df is None:
        df = load_ecocrop_data()
    if df is None:
        return {}

    crop_groups = load_crop_groups()

    cols = ["FER", "FERR", "DRA", "DRAR", "TEXT", "TEXTR"]
    df = df.dropna(subset=cols, how="all").copy()

    for col in cols:
        df.loc[:, col] = df[col].fillna("").astype(str).str.lower().str.strip()

    fertility = fertility.lower().strip()
    drainage  = drainage.lower().strip()
    texture   = texture.lower().strip()

    filtered = df[
        (
            df["FER"].str.contains(fertility, regex=False) |
            df["FERR"].str.contains(fertility, regex=False)
        ) &
        (
            df["DRA"].str.contains(drainage, regex=False) |
            df["DRAR"].str.contains(drainage, regex=False)
        ) &
        (
            df["TEXT"].str.contains(texture, regex=False) |
            df["TEXTR"].str.contains(texture, regex=False)
        )
    ]

    grouped_results = defaultdict(list)

    for _, row in filtered.iterrows():
        common = safe_str(row.get("CommonEnglishName"))
        widely = safe_str(row.get("WidelyKnownAs"))
        scientific = safe_str(row.get("ScientificName"))

        if common:
            display_name = common
            key_name = common.lower()
        elif widely:
            display_name = widely
            key_name = widely.lower()
        elif scientific:
            display_name = scientific
            key_name = scientific.split()[0].lower()
        else:
            continue

        if common and widely:
            display_name = f"{common} (widely known as {widely})"

        group = crop_groups.get(key_name, "UNCLASSIFIED")
        grouped_results[group].append(display_name)

    return dict(grouped_results)
