"""Anonymize the leads export. Writes the public file; keeps the crosswalk local."""
import pandas as pd

leads = pd.read_csv("data/_leads_raw.csv")     # gitignored

# lead name -> existing customer_id from part3's anonymized log. Fill these in.
BOOKED = {
    "Adam": "C__",
    "Terrynce Rucker I": "C__",
    "Christina (Cecilio) Landig": "C__",
    "Maritza Rodriguez": "C__",
    "Santiago A. Olmos": "C__",
    "Juana Chiapas": "C__",
    "Nanette Barranco": "C__",
    "Emmanuel Rodriguez": "C__",
}

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
        "ad_id":     str(r.get("Labels", "")),
        "converted": int(cid.startswith("C")),
        "outcome":   "",   # booked / quoted_no_book / never_answered /
                           # price_objection / out_of_area
    })

pd.DataFrame(out).to_csv("data/leads_anonymized.csv", index=False)
pd.DataFrame(cross).to_csv("data/_leads_crosswalk.csv", index=False)
print(f"{len(out)} leads | {sum(o['converted'] for o in out)} converted")
