"""
Log a completed job. Computes the total, appends the row, reruns everything.

    python3 log_job.py

Press Enter to accept a default shown in [brackets].
"""
import pandas as pd
import subprocess
import datetime as dt

JOB_LOG = "data/job_log.csv"
LEADS = "data/leads_anonymized.csv"

TIERS = ["Standard", "Deluxe", "Premium", "Interior",
         "Maintenance", "Ceramic Coating", "Pressure Wash", "Non-Detail"]
CHANNELS = ["Meta Ads", "D2D", "Referral", "Instagram (Organic)", "Facebook (Organic)"]


def ask(label, default="", options=None):
    if options:
        print(f"\n{label}")
        for i, o in enumerate(options, 1):
            print(f"  {i}. {o}")
        raw = input(f"  choose 1-{len(options)} [{default}]: ").strip()
        if not raw:
            return default
        return options[int(raw) - 1] if raw.isdigit() else raw
    raw = input(f"{label} [{default}]: ").strip()
    return raw or default


def money(label, default="0"):
    while True:
        raw = input(f"{label} [{default}]: ").strip() or default
        try:
            return float(raw.replace("$", "").replace(",", ""))
        except ValueError:
            print("  numbers only")


def main():
    d = pd.read_csv(JOB_LOG)
    print("=" * 50)
    print("LOG A JOB")
    print("=" * 50)

    customer = ask("Customer first name")
    city     = ask("City")
    date     = ask("Date", dt.date.today().strftime("%-m/%-d/%y"))
    tier     = ask("Package tier", "Standard", TIERS)
    service  = ask("Service description", f"{tier} Detail")
    vehicles = int(ask("Vehicles", "1"))
    channel  = ask("Acquisition channel", "Meta Ads", CHANNELS)

    creative, dest, attributed, arm = "", "", 0, ""
    if channel == "Meta Ads":
        print("\n--- ad attribution ---")
        ad = ask("Did an AD bring them in? y/n", "y").lower().startswith("y")
        if ad:
            creative   = ask("Creative name (e.g. Any time, Denise Reactions)")
            dest       = ask("Destination", "Instagram Ad")
            attributed = 1
            arm        = ask("Campaign arm", "A_MESSAGES")
        else:
            creative, dest = "NO AD", ask("Destination", "Instagram Organic DM")
            print("  -> logging as organic. Channel changed to Instagram (Organic).")
            channel = "Instagram (Organic)"

    job = money("\nJob value $")
    tip = money("Tip $")
    total = job + tip
    print(f"\n  TOTAL: ${total:,.2f}   (job ${job:,.2f} + tip ${tip:,.2f})")

    msgs = ask("Message thread length (blank if unknown)", "")
    lead = ask("Lead ID in leads_anonymized.csv (blank if none)", "")

    if not ask("\nSave? y/n", "y").lower().startswith("y"):
        return print("cancelled")

    row = {c: "" for c in d.columns}
    row.update({"date": date, "customer": customer, "city": city,
                "service": service, "package_tier": tier, "n_vehicles": vehicles,
                "channel": channel, "creative_hook": creative,
                "platform_destination": dest, "ad_attributed": attributed,
                "campaign_arm": arm, "job_value": job, "tip": tip,
                "logged_total": total,
                "is_detail_job": 0 if tier in ("Pressure Wash", "Non-Detail") else 1,
                "tracked_period": "tracked",
                "notes": f"Thread length {msgs}." if msgs else ""})
    pd.concat([d, pd.DataFrame([row])], ignore_index=True).to_csv(JOB_LOG, index=False)
    print(f"  job_log: {len(d)+1} rows")

    if lead:
        L = pd.read_csv(LEADS)
        k = L.lead_id == lead
        if k.any():
            L.loc[k, ["outcome", "converted"]] = ["booked", 1]
            if msgs:
                L.loc[k, "Message_count"] = int(msgs)
            L.to_csv(LEADS, index=False)
            print(f"  leads: {lead} -> booked")
        else:
            print(f"  WARNING: lead {lead} not found")

    print("\nrerunning pipeline...")
    subprocess.run(["python3", "refresh.py"], capture_output=True)
    subprocess.run(["python3", "check_drift.py"])


if __name__ == "__main__":
    main()
