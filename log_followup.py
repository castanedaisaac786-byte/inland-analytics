import pandas as pd, sys
p="data/leads_anonymized.csv"; d=pd.read_csv(p)
d["last_contact"] = d["last_contact"].astype("object")
d["outcome"] = d["outcome"].astype("object")
lid, out = sys.argv[1], sys.argv[2]
k = d.lead_id==lid
if not k.any(): sys.exit(f"{lid} not found")
d.loc[k,"n_followups"] = d.loc[k,"n_followups"].fillna(0) + 1
if out=="booked":
    d.loc[k,["outcome","converted","booked_after_followup"]] = ["booked",1,1]
d.loc[k,"last_contact"] = pd.Timestamp.today().strftime("%Y-%m-%d")
d.to_csv(p,index=False)
print(d[k][["lead_id","followup_arm","n_followups","outcome"]].to_string(index=False))
