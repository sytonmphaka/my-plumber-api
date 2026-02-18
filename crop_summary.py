import pandas as pd
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "ecocrop_utf8.csv"

_df_cache = None


def safe(value, default=""):
    if pd.isna(value) or value == "NA":
        return default
    return value


def find_row_by_common_name(df, search_name):
    search_name = search_name.lower().strip()

    for _, row in df.iterrows():
        comnames = safe(row["COMNAME"]).lower().split(",")
        comnames = [n.strip() for n in comnames]

        if search_name in comnames:
            return row

    return None


def generate_crop_paragraph(row, crop_name):
    crop_name = crop_name.title()

    life_cycle = safe(row["LISPA"])
    photo = safe(row["PHOTO"])

    # Temperature
    temp_opt = f'{safe(row["TOPMN"])}–{safe(row["TOPMX"])}°C'
    temp_tol = f'{safe(row["TMIN"])}–{safe(row["TMAX"])}°C'

    # Rainfall
    rain_opt = f'{safe(row["ROPMN"])}–{safe(row["ROPMX"])} mm'
    rain_tol = f'{safe(row["RMIN"])}–{safe(row["RMAX"])} mm'

    # Soil
    ph_opt = f'{safe(row["PHOPMN"])}–{safe(row["PHOPMX"])}'
    ph_tol = f'{safe(row["PHMIN"])}–{safe(row["PHMAX"])}'
    soil_depth = safe(row["DEP"])
    soil_texture = safe(row["TEXT"])
    soil_texture_tol = safe(row["TEXTR"])
    fertility = safe(row["FER"])
    drainage = safe(row["DRA"])

    # Salinity
    salinity = safe(row["SAL"])

    # Growth duration
    grow_min = safe(row["GMIN"])
    grow_max = safe(row["GMAX"])

    photo_text = photo.lower() if photo else ""

    paragraph = (
        f"The {crop_name} crop grows best in warm tropical to subtropical climates "
        f"with full sunlight and open fields, preferring optimal temperatures of "
        f"{temp_opt} but tolerating {temp_tol}, and performs well under annual "
        f"rainfall of about {rain_opt}, although it can survive in areas receiving "
        f"{rain_tol} if flooding is avoided. "
        f"It thrives in {drainage} soils with {fertility} fertility, requiring "
        f"{soil_depth} soil depth and growing best in {soil_texture} soils, "
        f"while tolerating {soil_texture_tol} textures. "
        f"{crop_name} prefers slightly acidic to neutral soils (pH {ph_opt}) but "
        f"can tolerate a wider pH range of {ph_tol}, does not tolerate {salinity} "
        f"salinity or waterlogged soils, and grows as a {photo_text} {life_cycle} "
        f"crop, reaching harvest maturity within {grow_min}–{grow_max} days, "
        f"making it suitable for rain-fed farming in tropical regions such as Malawi."
    )

    return paragraph


def get_crop_summary(common_name):
    global _df_cache

    if _df_cache is None:
        _df_cache = pd.read_csv(DATA_FILE)

    row = find_row_by_common_name(_df_cache, common_name)

    if row is None:
        return "Crop not found. Please try another common name."

    return generate_crop_paragraph(row, common_name)


if __name__ == "__main__":
    print(get_crop_summary("okra"))
