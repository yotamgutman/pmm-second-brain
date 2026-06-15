---
tags: [engineering, jira]
ticket: AUTOSYNC-142
status: Done
---

# Jira Export — AUTOSYNC-142

**Title:** Build AutoSync core sync engine (Salesforce, HubSpot, NetSuite)
**Type:** Epic
**Status:** Done
**Resolved:** 2026-05-23
**Assignee:** Eng Team — Integrations Pod

## Description

Build the core AutoSync engine to replace manual CSV export/import for the three launch integrations: Salesforce, HubSpot, and NetSuite. Sync runs on a 15-minute interval per connected workspace, with conflict resolution via most-recent-write-wins and a visible sync log in the admin panel.

## Acceptance Criteria

- [x] OAuth connection flow for all three integrations
- [x] 15-minute sync interval, configurable per workspace (Enterprise only)
- [x] Sync log visible in admin panel
- [x] Conflict resolution: most-recent-write-wins

## Comments

**Eng Lead (2026-05-20):** QA passed for Salesforce and HubSpot. NetSuite passed standard load testing, but we should keep an eye on very high-volume batch syncs — e.g., end-of-month exports. Saw a handful of duplicate records in stress testing above 5,000 records/sync window. Not blocking for launch given low likelihood, but let's open a follow-up.

**PM (2026-05-21):** Agreed, not a launch blocker. Opening AUTOSYNC-158 to track the NetSuite duplicate-entry edge case separately. Targeting next sprint.

**Eng Lead (2026-05-23):** Shipped to all Business/Enterprise workspaces. Closing this epic; follow-up tracked in AUTOSYNC-158.

## Linked Tickets

- AUTOSYNC-158 — NetSuite duplicate-entry edge case under high-volume sync (Open, targeted for next sprint)

## Related

- [[autosync-spec]]
- [[slack-export-launch-thread]]
