# Messaging Drift Check

Found **2** potential mismatch(es) between external messaging and internal reality.

## 🔴 High severity
**External claim:** Keeping your data in sync is simple: export your data from FlowPilot as a CSV file, then import it into your other tools whenever you need an update.
**Internal reality:** AutoSync shipped on May 26, 2026 and automatically syncs data with Salesforce, HubSpot, and NetSuite every 15 minutes — manual CSV export/import is no longer the primary sync method for Business and Enterprise customers.
**Source:** `product/autosync-spec.md`

## 🟡 Medium severity
**External claim:** Full control over when and how your data moves between systems.
**Internal reality:** With AutoSync, sync timing is automated on a 15-minute interval rather than fully manual; the 'full control' framing is outdated for customers on AutoSync.
**Source:** `product/autosync-spec.md`


---
**Sources:** `external/current-landing-page.md`, `product/autosync-spec.md`, `engineering/jira-export-autosync.md`
