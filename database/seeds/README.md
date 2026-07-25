# Seed data

`demo_state_allocations.csv` is synthetic test material. Its values are not FAAC
figures, it uses a future 2099 reporting period, and every row carries the literal
label `DEMO DATA - NOT REAL FAAC DATA`.

The demo loader stores these records as pending, unpublished, and `is_demo=true`.
Database constraints prohibit publishing demo reporting periods and allocations.

The canonical state seed is maintained in Python so it can use stable identifiers
and idempotent updates:

```bash
gaiafaac-db seed-states
gaiafaac-db seed-demo
```
