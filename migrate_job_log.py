"""
One-time migration: add attribution columns to data/job_log.csv
================================================================
Adds creative_hook, platform_destination, and ad_attributed IN PLACE,
keyed on customer name. Every existing column is preserved, so analysis.py,
refresh.py, and Part 3 continue to work unchanged.

Attribution comes from the Notes column of the source tracker, where the
ad each customer replied to was recorded at time of booking.

Run once:  python3 migrate_job_log.py
"""
import pandas as pd
import shutil
import pathlib

PATH = "data/job_log.csv"

# customer -> (creative_hook, platform_destination, ad_attributed)
ATTRIBUTION = {
    "John":              ("Patrick Ads",      "Instagram Ad",           1),
    "Christopher":       ("NO AD",            "Instagram Organic DM",   0),
    "Adam":              ("Denise Reactions", "Instagram Ad",           1),
    "Michelle":          ("Unspecified",      "Facebook Ad",            1),
    "Terrynce":          ("Pet Hair Removal", "Instagram Ad",           1),
    "Christina":         ("Denise Reactions", "Instagram Ad",           1),
    "Adrian Ponce":      ("Pet Hair Removal", "Instagram Ad",           1),
    "BH":                ("Save 2007 Chevy",  "Instagram Ad",           1),
    "Maritza":           ("Save 2007 Chevy",  "Instagram Ad",           1),
    "Favi":              ("Pet Hair Removal", "Instagram Ad",           1),
    "James":             ("NO AD",            "Instagram Organic DM",   0),
    "Santiago":          ("Save 2007 Chevy",  "Instagram Ad",           1),
    "Juana":             ("Save 2007 Chevy",  "Instagram Ad",           1),
    "Miguel":            ("NO AD",            "Instagram Organic DM",   0),
    "Duene":             ("NO AD",            "Instagram Organic Feed", 0),
    "Nanette":           ("Unspecified",      "Facebook Ad",            1),
    "Jasmine":           ("Unspecified",      "Facebook Ad",            1),
    "Hassan":            ("NO AD",            "Instagram Organic DM",   0),
    "Emmanuel":          ("August Broad",     "Instagram Ad",           1),
    "David":             ("",                 "Instagram Organic",      0),
    "Patrick":           ("",                 "Facebook Organic",       0),
    "Happy":             ("",                 "Instagram Organic",      0),
}


def main():
    path = pathlib.Path(PATH)
    if not path.exists():
        raise SystemExit(f"{PATH} not found — run from the repo root.")

    shutil.copy(path, str(path) + ".bak")
    df = pd.read_csv(path)

    # Find the customer column whatever it's called.
    cust_col = next((c for c in df.columns
                     if c.strip().lower() in ("customer", "customer_name", "name")), None)
    if cust_col is None:
        raise SystemExit(f"No customer column found. Columns: {list(df.columns)}")

    key = df[cust_col].astype(str).str.strip()
    df["creative_hook"] = key.map(lambda k: ATTRIBUTION.get(k, ("", "", 0))[0])
    df["platform_destination"] = key.map(lambda k: ATTRIBUTION.get(k, ("", "", 0))[1])
    df["ad_attributed"] = key.map(lambda k: ATTRIBUTION.get(k, ("", "", 0))[2]).astype(int)
    if "campaign_arm" not in df.columns:
        df["campaign_arm"] = ""

    df.to_csv(path, index=False)

    matched = key.isin(ATTRIBUTION).sum()
    print(f"Backed up to {path}.bak")
    print(f"Matched {matched} of {len(df)} rows to an attribution record.")
    print(f"Ad-attributed bookings: {int(df.ad_attributed.sum())}")
    unmatched = sorted(set(key[~key.isin(ATTRIBUTION)]))
    if unmatched:
        print(f"Unmatched (left blank, expected for D2D/Referral): {unmatched}")


if __name__ == "__main__":
    main()
