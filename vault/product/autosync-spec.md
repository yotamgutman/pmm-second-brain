---
tags: [product, spec]
status: shipped
---

# AutoSync — Product Spec

## Problem

Since launch, FlowPilot customers have moved data between FlowPilot and their CRM/ERP systems via manual CSV export and import. Customer feedback consistently flags this as the single biggest friction point in onboarding and day-to-day workflow — see [[brightline-logistics]] for a representative example.

## What AutoSync Does

AutoSync replaces manual CSV export/import with a continuous, automated sync between FlowPilot and connected systems.

- **Sync interval:** every 15 minutes
- **Supported integrations at launch:** Salesforce, HubSpot, NetSuite
- **Conflict resolution:** most-recent-write-wins, with a sync log visible in the admin panel
- **Setup:** one-time OAuth connection per integration, no CSV mapping required

## Rollout

AutoSync shipped on May 26, 2026 to all Business and Enterprise plan customers. See [[jira-export-autosync]] for the engineering ticket and [[slack-export-launch-thread]] for the internal launch announcement.

## Known Issues

A duplicate-entry edge case has been observed with the NetSuite integration during high-volume sync windows — see [[hearth-and-co]] for a customer report. Tracked separately (AUTOSYNC-158), fix targeted for next sprint. Not considered launch-blocking.

## Related

- [[feature-history]]
- [[roadmap]]
- [[win-loss-notes]]
