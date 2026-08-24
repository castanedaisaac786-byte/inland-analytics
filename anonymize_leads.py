"""Anonymize the leads export. Writes the public file; keeps the crosswalk local."""
import pandas as pd
import re

leads = pd.read_csv("data/_leads_raw.csv")     # gitignored
leads = leads[~leads["Name"].astype(str).str.contains(
    "test lead|Sample Lead", case=False, na=False)]

# lead name -> existing customer_id from part3's anonymized log. Fill these in.
BOOKED = {
    "Adam Netzley":                       "C09",   # 7/20, $250
    "Terrynce Rucker I":          "C11",   # 7/21, $170
    "Christina (Cecilio) Landig": "C12",   # 7/22, $130
    "Santiago A. Olmos":          "C17",   # 7/24, $200
    "Juana Chiapas":              "C21",   # 7/26, $120
    "Maritza Rodriguez":          "C24",   # 7/29, $140
    "Nanette Barranco":           "C27",   # 8/1,  $130
    "Emmanuel Rodriguez":         "C33",   # 8/9,  $180
}

def _ids(label):
    """Pull ad IDs out of Meta's label soup. Multiple ids -> pipe-joined."""
    found = re.findall(r"ad_id\.(\d+)", str(label))
    return "|".join(dict.fromkeys(found))   # dedupe, keep order

out, cross, n = [], [], 0
for _, r in leads.iterrows():
    cid = BOOKED.get(str(r["Name"]).strip())
    if cid is None:
        n += 1
        cid = f"L{n:03d}"
    cross.append({"lead_id": cid, "name": r["Name"]})
    out.append({
        "lead_id":   cid,
        "date":      r["Created"],
        "channel":   r["Channel"],
        "ad_id":     _ids(r.get("Labels", "")),
        "n_ad_ids":  len(re.findall(r"ad_id\.(\d+)", str(r.get("Labels", "")))),
        "converted": int(cid.startswith("C")),
        "outcome":   "",   # booked / quoted_no_book / never_answered /
                           # price_objection / out_of_area
    })

pd.DataFrame(out).to_csv("data/leads_anonymized.csv", index=False)
pd.DataFrame(cross).to_csv("data/_leads_crosswalk.csv", index=False)
print(f"{len(out)} leads | {sum(o['converted'] for o in out)} converted")
