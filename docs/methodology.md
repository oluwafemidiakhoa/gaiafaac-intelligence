# Ledger methodology

## Exact values

Money remains `Decimal` in Python and `NUMERIC` in PostgreSQL. Proof payloads serialize
money as exact strings. Missing remains `null`; no Phase 1 service annualizes, imputes,
or converts missing values to zero.

## Canonical JSON

`gaia-canonical-json-v1` applies these rules:

1. recursively sort object keys;
2. normalize strings and keys to Unicode NFC;
3. preserve list order;
4. serialize finite Decimal values as exact strings, preserving scale;
5. normalize timezone-aware datetimes to UTC with `Z`;
6. serialize dates as ISO 8601;
7. reject binary floats, naive datetimes, non-finite decimals, and unsupported types;
8. emit UTF-8 JSON without insignificant whitespace, then calculate SHA-256.

## Reconciliation

For FAAC claims with gross, deductions, and net present:

```text
delta = gross - deductions - net
reconciled = abs(delta) <= NGN 0.01
```

If any term is missing, reconciliation is `not_applicable`; it is not false or zero.
