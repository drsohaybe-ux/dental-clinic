"""Download, normalize, and cache Algerian National Nomenclature dataset."""

import json
import os
import re
import urllib.request
import uuid

RAW_URL = "https://raw.githubusercontent.com/mahmoudBens/Nomenclature-des-medicaments-en-algerie/master/medicament.json"

DENTAL_DCIS = [
    "AMOXICILLINE", "CLAVULANIQUE", "METRONIDAZOLE", "SPIRAMYCINE", "CLINDAMYCINE",
    "AZITHROMYCINE", "CLARITHROMYCINE", "CEFALEXINE", "DOXYCYCLINE", "CIPROFLOXACINE",
    "ERYTHROMYCINE", "PENICILLINE", "PARACETAMOL", "IBUPROFENE", "KETOPROFENE",
    "DICLOFENAC", "NAPROXENE", "ACECLOFENAC", "TRAMADOL", "CODEINE",
    "ACIDE ACETYLSALICYLIQUE", "PREDNISOLONE", "PREDNISONE", "DEXAMETHASONE",
    "BETAMETHASONE", "TRIAMCINOLONE", "ARTICAINE", "LIDOCAINE", "MEPIVACAINE",
    "PRILOCAINE", "BUPIVACAINE", "CHLORHEXIDINE", "HEXETIDINE", "BENZYDAMINE",
    "MICONAZOLE", "NYSTATINE", "FLUCONAZOLE", "ACICLOVIR", "VALACICLOVIR",
    "FLUOR", "FLUORURE", "HYDROGENE PEROXYDE", "POVIDONE IODEE"
]

DENTAL_BRANDS = [
    "AUGMENTIN", "AMOXIL", "CLAMOXYL", "BIRODOGYL", "RODOGYL", "DOLIPRANE",
    "ALGIDOL", "CATAFLAM", "HEXTRIL", "ELUDRIL", "SOLUPRED", "SEPTANEST",
    "ALPHACAINE", "PYRALVEX", "EFFERALGAN", "VOLTARENE", "CURAM", "PANADOL",
    "PERFALGAN", "CLAMID", "AMOCLAN", "XYLOCAINE", "UNICAINE", "SCANDICAINE",
    "UBISTESIN", "ADRECAINE", "BETADINE", "ALODONT", "PAROEX", "KENACORT",
    "ORABASE", "DENTOPHENOL", "PULPODENT", "APRONAX", "SURGAM", "CELESTENE"
]


def map_forme(f: str | None) -> str:
    if not f:
        return "tablet"
    u = f.upper()
    if any(k in u for k in ["COMP", "CPR", "COMPRIME"]):
        return "tablet"
    if any(k in u for k in ["GLE", "GELULE", "CAPS", "GLES"]):
        return "capsule"
    if "SIROP" in u:
        return "syrup"
    if any(k in u for k in ["SUSP", "SUSPENSION", "PDRE. P. SUSP"]):
        return "suspension"
    if any(k in u for k in ["INJ", "PERF", "SOL. INJ", "SOL.INJ"]):
        return "injection"
    if any(k in u for k in ["BAIN DE BOUCHE", "COLLUTOIRE", "BUCCO", "SOL. BUCCALE"]):
        return "mouthwash"
    if "GEL" in u:
        return "gel"
    if "CREME" in u:
        return "cream"
    if any(k in u for k in ["POMM", "POMMADE"]):
        return "topical"
    if "PATE" in u:
        return "paste"
    if "VERNIS" in u:
        return "varnish"
    if any(k in u for k in ["GTT", "GOUTTE", "COLLY"]):
        return "drops"
    if any(k in u for k in ["SPRAY", "PULV", "AEROSOL", "AER"]):
        return "spray"
    return "other"


def clean_str(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()


def parse_dose_unit(d: str | None) -> tuple[str | None, str | None]:
    if not d:
        return None, None
    s = clean_str(d)
    m_compound = re.match(r"^([\d.,]+)\s*[A-Za-z%]+\s*/\s*([\d.,]+)\s*([A-Za-z%]+)", s)
    if m_compound:
        return f"{m_compound.group(1)}/{m_compound.group(2)}".replace(",", "."), m_compound.group(3).lower()
    m = re.match(r"^([\d.,]+(?:/[\d.,]+)?)\s*([A-Za-z/%]+(?:/[A-Za-z]+)?)", s)
    if m:
        return m.group(1).replace(",", "."), m.group(2).lower()
    if len(s) <= 50:
        return s, None
    return None, None


def check_dental(brand: str | None, dci: str | None, forme: str | None) -> bool:
    brand_u = clean_str(brand).upper()
    dci_u = clean_str(dci).upper()
    forme_u = clean_str(forme).upper()
    if any(b in brand_u for b in DENTAL_BRANDS):
        return True
    if any(d in dci_u for d in DENTAL_DCIS):
        return True
    if any(k in forme_u for k in ["BAIN DE BOUCHE", "COLLUTOIRE", "GINGIVAL", "BUCCALE", "DENTAIRE"]):
        return True
    return False


def main():
    print("Fetching raw nomenclature from github...")
    raw_bytes = urllib.request.urlopen(RAW_URL).read().decode("utf-8")
    data = json.loads(raw_bytes)
    raw_records = data[1]["data"]
    print(f"Received {len(raw_records)} raw records")

    processed = []
    NAMESPACE = uuid.UUID("7b420042-45e0-47b2-84da-5fbf6ec25f20")

    for r in raw_records:
        reg_num = clean_str(r.get("NUM_ENREGISTREMENT"))
        code = clean_str(r.get("CODE"))
        brand = clean_str(r.get("NOM_DE_MARQUE"))
        dci = clean_str(r.get("DENOMINATION_COMMUNE_INTERNATIONALE"))
        raw_forme = clean_str(r.get("FORME"))
        raw_dosage = clean_str(r.get("DOSAGE"))
        cond = clean_str(r.get("COND"))
        lab = clean_str(r.get("LABORATOIRES_DETENTEUR_DE_LA_DECISION_DENREGISTREMENT"))
        country = clean_str(r.get("PAYS_DU_LABORATOIRE_DETENTEUR_DE_LA_DECISION_DENREGISTREMENT"))
        price = clean_str(r.get("PRIX_PORTE_SUR_LA_DECISION_DENREGISTREMENT"))
        remb = clean_str(r.get("REMBOURSEMENT"))

        unique_key = f"{reg_num}|{code}|{brand}|{raw_dosage}|{raw_forme}"
        item_id = str(uuid.uuid5(NAMESPACE, unique_key))
        dose, unit = parse_dose_unit(raw_dosage)
        std_form = map_forme(raw_forme)
        is_dent = check_dental(brand, dci, raw_forme)

        processed.append({
            "id": item_id,
            "registration_number": reg_num or None,
            "code": code or None,
            "brand_name": brand,
            "dci": dci,
            "form": raw_forme or None,
            "standard_form": std_form,
            "dosage": raw_dosage or None,
            "dose": dose,
            "unit": unit,
            "packaging": cond or None,
            "laboratory": lab or None,
            "country": country or None,
            "price": price or None,
            "reimbursement": remb or None,
            "is_dental": is_dent,
            "requires_prescription": True if (r.get("LISTE") in ["Liste I", "Liste II"] or is_dent) else False,
        })

    supplements = [
        {
            "registration_number": "ALG-DENT-001",
            "code": "DENT 01",
            "brand_name": "AMOXIL",
            "dci": "AMOXICILLINE",
            "form": "GELULE",
            "standard_form": "capsule",
            "dosage": "500MG",
            "dose": "500",
            "unit": "mg",
            "packaging": "B/24",
            "laboratory": "GLAXOSMITHKLINE",
            "country": "ALGERIE",
            "price": "PCSU 240,00 DA",
            "reimbursement": "OUI",
            "is_dental": True,
            "requires_prescription": True,
        },
        {
            "registration_number": "ALG-DENT-002",
            "code": "DENT 02",
            "brand_name": "AMOXIL",
            "dci": "AMOXICILLINE",
            "form": "COMP. DISPERS.",
            "standard_form": "tablet",
            "dosage": "1G",
            "dose": "1",
            "unit": "g",
            "packaging": "B/14",
            "laboratory": "GLAXOSMITHKLINE",
            "country": "ALGERIE",
            "price": "PCSU 480,00 DA",
            "reimbursement": "OUI",
            "is_dental": True,
            "requires_prescription": True,
        },
        {
            "registration_number": "ALG-DENT-003",
            "code": "DENT 03",
            "brand_name": "ALGIDOL",
            "dci": "PARACETAMOL / CODEINE PHOSPHATE",
            "form": "COMP. SEC.",
            "standard_form": "tablet",
            "dosage": "500MG/30MG",
            "dose": "500/30",
            "unit": "mg",
            "packaging": "B/16",
            "laboratory": "BIOPHARM",
            "country": "ALGERIE",
            "price": "PCSU 185,50 DA",
            "reimbursement": "OUI",
            "is_dental": True,
            "requires_prescription": True,
        },
        {
            "registration_number": "ALG-DENT-004",
            "code": "DENT 04",
            "brand_name": "HEXTRIL",
            "dci": "HEXETIDINE",
            "form": "SOL. P. BAIN DE BOUCHE",
            "standard_form": "mouthwash",
            "dosage": "0,1%",
            "dose": "0.1",
            "unit": "%",
            "packaging": "FL/200ML",
            "laboratory": "JOHNSON & JOHNSON",
            "country": "FRANCE",
            "price": "PCSU 310,00 DA",
            "reimbursement": "NON",
            "is_dental": True,
            "requires_prescription": False,
        },
        {
            "registration_number": "ALG-DENT-005",
            "code": "DENT 05",
            "brand_name": "ALPHACAINE SP",
            "dci": "ARTICAINE CHLORHYDRATE / ADRENALINE",
            "form": "SOL. INJ. DENTAIRE",
            "standard_form": "injection",
            "dosage": "4% / 1:100 000",
            "dose": "4%",
            "unit": "inj",
            "packaging": "B/50 CARTOUCHES DE 1.8ML",
            "laboratory": "DEXIS",
            "country": "FRANCE",
            "price": "PCSU 4200,00 DA",
            "reimbursement": "NON",
            "is_dental": True,
            "requires_prescription": True,
        },
        {
            "registration_number": "ALG-DENT-006",
            "code": "DENT 06",
            "brand_name": "ALPHACAINE N",
            "dci": "ARTICAINE CHLORHYDRATE / ADRENALINE",
            "form": "SOL. INJ. DENTAIRE",
            "standard_form": "injection",
            "dosage": "4% / 1:200 000",
            "dose": "4%",
            "unit": "inj",
            "packaging": "B/50 CARTOUCHES DE 1.8ML",
            "laboratory": "DEXIS",
            "country": "FRANCE",
            "price": "PCSU 4200,00 DA",
            "reimbursement": "NON",
            "is_dental": True,
            "requires_prescription": True,
        },
        {
            "registration_number": "ALG-DENT-007",
            "code": "DENT 07",
            "brand_name": "KENACORT ORABASE",
            "dci": "TRIAMCINOLONE ACETONIDE",
            "form": "PATE BUCCALE",
            "standard_form": "paste",
            "dosage": "0,1%",
            "dose": "0.1",
            "unit": "%",
            "packaging": "TUBE 5G",
            "laboratory": "BRISTOL-MYERS SQUIBB",
            "country": "FRANCE",
            "price": "PCSU 350,00 DA",
            "reimbursement": "NON",
            "is_dental": True,
            "requires_prescription": True,
        },
        {
            "registration_number": "ALG-DENT-008",
            "code": "DENT 08",
            "brand_name": "PULPODENT",
            "dci": "IODOFORME / OXYDE DE ZINC / EUGENOL",
            "form": "PATE DENTAIRE",
            "standard_form": "paste",
            "dosage": "PATE",
            "dose": None,
            "unit": None,
            "packaging": "FL/25G POUDRE + 15ML LIQUIDE",
            "laboratory": "VLADMIVA",
            "country": "RUSSIE",
            "price": "PCSU 2800,00 DA",
            "reimbursement": "NON",
            "is_dental": True,
            "requires_prescription": True,
        },
        {
            "registration_number": "ALG-DENT-009",
            "code": "DENT 09",
            "brand_name": "PYRALVEX",
            "dci": "EXTRAIT DE RHUBARBE / ACIDE SALICYLIQUE",
            "form": "SOL. BUCCALE",
            "standard_form": "gel",
            "dosage": "SOL. GINGIVALE",
            "dose": None,
            "unit": None,
            "packaging": "FL/10ML",
            "laboratory": "MEDA PHARMA",
            "country": "FRANCE",
            "price": "PCSU 420,00 DA",
            "reimbursement": "NON",
            "is_dental": True,
            "requires_prescription": False,
        },
    ]

    for s in supplements:
        unique_key = f"{s['registration_number']}|{s['brand_name']}|{s['dosage']}"
        s["id"] = str(uuid.uuid5(NAMESPACE, unique_key))
        processed.append(s)

    out_dir = os.path.join("backend", "app", "modules", "medication_catalog", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "algerian_nomenclature.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

    dental_count = sum(1 for p in processed if p["is_dental"])
    print(f"Successfully wrote {len(processed)} items to {out_file}")
    print(f"Dental items: {dental_count} ({dental_count / len(processed) * 100:.1f}%)")


if __name__ == "__main__":
    main()
