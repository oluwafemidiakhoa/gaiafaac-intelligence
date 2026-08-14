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

## Evidence Coverage

`gaia-evidence-coverage-v1` gives each of the seven ledger domains equal weight.
Verified contributes `1`, partial contributes `0.5`, and every other workflow state
contributes `0`. Coverage is the contribution sum divided by seven and is stored as an
exact four-decimal fraction. Thus three verified, two partial, and two unavailable
domains produce `(3 + 2 × 0.5) / 7 = 0.5714` or `57.14%`.

Coverage measures retained evidence availability, not fiscal performance. An
unavailable domain contributes no evidence coverage; it never represents zero money.

## Revisions and materiality

When a new content-versioned claim supersedes an earlier claim for the same
jurisdiction, fiscal period, and metric:

```text
value_delta = revised exact value - previous exact value
value_change_percent = value_delta / abs(previous exact value) × 100
```

The percentage is unavailable when the previous value is zero or either value is
missing. `gaia` methodology `1.1.0` marks an absolute change of at least 5% as
material. This label describes revision size only; it does not imply cause or
misconduct.

## Evidence conflicts

A conflict must be explicitly recorded between at least two retained claims for the
same jurisdiction, domain, period, and metric with different explicit values. Gaia
preserves every participant and reports the conflict as unresolved. It never chooses
a value merely because one source was ingested later.
