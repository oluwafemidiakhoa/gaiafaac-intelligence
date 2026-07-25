# Data-source policy

Milestone 3 accepts manually reviewed local CSV files. It does not scrape,
download, parse PDF, or parse Excel sources.

Every accepted file is registered with:

- source organization and optional URL;
- original filename and storage path;
- SHA-256 checksum;
- MIME type, publication date, import timestamp, and version;
- processing and review status;
- reporting-period lineage.

The registered path points to the unmodified source supplied to the command. The
file must remain in controlled durable storage for later review. Registration
deduplicates exact file content by SHA-256 and rejects attempts to attach the
same document to a second reporting period.

Source registration or automated validation does not establish factual
verification. Only explicit approval by an active reviewer or administrator
sets imported records to `human_verified`, and even approved records remain
unpublished in Milestone 3.
