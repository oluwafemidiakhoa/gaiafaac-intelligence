# OAGF source ingestion

## Purpose and governance boundary

The OAGF source-ingestion layer inventories and archives documents exposed by the official
Office of the Accountant-General of the Federation publication hub. Discovery is broader than
canonical fiscal publication. A synchronized document remains registered evidence; it is never
automatically extracted, approved, or published.

Only `https://oagf.gov.ng` is accepted by the collector. Missing or inaccessible official files
remain inaccessible. The collector does not substitute secondary sources.

## Live source inventory

Read-only inspection of the official hub on 2026-08-16 found nine exposed categories and sixteen
listing pages:

| Hub category           | Slug                     | Pages | Publication records |
| ---------------------- | ------------------------ | ----: | ------------------: |
| AGF's Speech           | `agfs-speech`            |     1 |                   0 |
| FAAC Report            | `faac-report`            |     7 |                  84 |
| Funds Releases to MDAs | `funds-releases-to-mdas` |     1 |                   0 |
| GIFMIS Reports         | `gifmis-reports`         |     1 |                   0 |
| IPPIS Reports          | `ippis-reports`          |     1 |                   0 |
| IPSAS Reports          | `ipsas-reports`          |     1 |                   1 |
| OAGF Annual Reports    | `oagf-annual-reports`    |     1 |                   5 |
| OAGF Journals          | `oagf-journals`          |     1 |                   0 |
| Treasury Circulars     | `treasury-circulars`     |     2 |                  23 |

The 113 records currently link to PDF files. Empty categories are retained in inventory output;
they are not interpreted as errors or deleted evidence. The WordPress taxonomy also exposes
category terms not linked from the public hub. PR1 follows the public hub as the authoritative
discovery root and records only its exposed categories.

OAGF listing dates are stored as `source_publication_date`: this is the date supplied by the
publisher's listing metadata. It is not silently reinterpreted as a FAAC meeting date,
disbursement date, or allocation-period month. The year and month rendered on the card are also
retained separately. Candidate FAAC output uses exact publication titles rather than constructing
a fiscal month from card metadata. The 2026-08-16 inventory contains one explicit upstream
conflict: the title `FAAC Report – Disbursement February, 2022` is paired with displayed card
metadata `February 2021`; PR1 preserves both and does not choose an interpretation.

## Architecture

The implementation separates four concerns:

- `discovery.py` follows hub category links and pagination, extracts source metadata, restricts
  requests to the official HTTPS host, and performs no accounting interpretation.
- `storage.py` provides an archive protocol and a local implementation. Originals use
  `<category>/<year>/<date>__<title>__<sha-prefix>.<ext>` and are never silently overwritten.
- `sync.py` compares URL observations and hashes, registers immutable `SourceDocument` rows,
  records source versions, classifies by auditable hub-category rules, and writes JSONL manifest
  events.
- the existing extraction, validation, approval, and publication layers remain disconnected from
  PR1 synchronization.

`oagf_sync_runs` records each real synchronization and its source-health counts.
`oagf_discovery_records` records every URL version and links archived content to the existing
`source_documents` table. The existing global SHA-256 uniqueness constraint deduplicates identical
bytes. A changed SHA-256 at the same URL creates a new version and links both the discovery record
and source document to the previous version.

A full synchronization fails closed if it discovers fewer than half the documents in an existing
baseline of at least ten. This prevents an upstream layout failure from being interpreted as a
mass deletion. Category, date, and limit-filtered runs are not compared with a full baseline.

## CLI

Run a live, read-only inventory with no database connection, downloads, archive writes, or manifest
changes:

```bash
gaiafaac-db sync-oagf-publications --dry-run
```

Filters are available through `--category`, `--since`, and `--limit`. `--download-only` makes the
PR1 archive intent explicit. `--extract` is present for the planned PR2 interface but fails closed
until governed extraction is implemented.

A real synchronization requires an upgraded database and configured `DATABASE_URL`:

```bash
alembic upgrade head
gaiafaac-db sync-oagf-publications --download-only
```

Local originals are stored under `data/oagf/archive/`. Manifest events are appended to
`data/oagf/manifest.jsonl`. Both are ignored by Git because source binaries and generated data must
not be committed. The `ArchiveStorage` protocol is the boundary for a future S3, R2, or Blob
implementation.

## Delivery sequence

The work remains split into coherent governed changes:

1. `agent/oagf-source-discovery`: discovery, archive, manifests, deduplication, and revisions.
2. `agent/oagf-faac-evidence`: full-document FAAC extraction, value lineage, validation, and the
   existing national reconciliation integration.
3. `agent/oagf-evidence-library`: source-health and evidence APIs plus integrated web experience.
4. `agent/oagf-scheduled-sync`: protected scheduled synchronization with no publication action.
5. `agent/oagf-source-families`: progressive structuring of useful non-FAAC evidence.
6. `agent/production-migration-reliability`: separate account-signup and deployment-migration fix.

Human approval and publication are explicitly outside synchronization. The first canonical
production publication still requires one real month, observed values and lineage shown before
approval, a separate administrator for publication, and a second explicit authorization before
the publish command.
