# Clinic Front-Desk Intelligence — Sprint 3G Operational Dashboard

Sprint 3G builds directly on the working Sprint 3E package. Sprint 3F Revenue at Risk / Revenue Recovered Intelligence is intentionally deferred until after the pilot deployment.

## What Sprint 3G adds

A new **Operational dashboard** is available from the main top bar. It is designed for clinic owners and supervisors to understand appointment operations without exposing financial estimates.

Operational KPIs include:
- Total appointments for a selected date range
- Completion rate
- No-show rate
- Cancellation rate
- Cancellation recovery rate from Sprint 3E
- Active waiting-list count
- Appointment flow: Pending, Confirmed, Checked-in, Completed, Cancelled, No-show
- Open workflow count
- Average booking lead time
- Current risk mix: LOW / MEDIUM / HIGH
- Recovered vs unrecovered cancelled slots
- Daily appointment activity trend
- Doctor-by-doctor operational comparison

The dashboard supports:
- Start date / end date
- All doctors or one doctor
- Up to 366 days per query

## New API

`GET /dashboard/operational?clinic_id=1&start_day=2026-09-01&end_day=2026-09-30`

Optional doctor filter:

`GET /dashboard/operational?clinic_id=1&start_day=2026-09-01&end_day=2026-09-30&doctor_id=1`

## Important metric definitions

- **Completion rate** = completed appointments / all appointments in the selected period.
- **No-show rate** = no-shows / (completed + no-show outcomes). Cancelled appointments are excluded from this attendance denominator.
- **Cancellation rate** = cancelled appointments / all appointments.
- **Cancellation recovery rate** = cancelled appointments with a `SLOT_RECOVERED` event / cancelled appointments.
- **Open workflow** = pending + confirmed + checked-in appointments.
- **Average booking lead** = average time between appointment creation and appointment start.

## Sprint 3F is deliberately NOT included

This package does not calculate:
- Revenue at risk
- Revenue recovered
- Financial loss estimates
- Financial recovery estimates

Those remain deferred for after pilot deployment, as requested.

## Database

Sprint 3G adds no tables or columns. Alembic remains:

`0003_waiting_list (head)`

No new migration is required.

## Version

`GET /health` returns:

`{"status":"ok","version":"3.0.0-alpha.5"}`

## Upgrade from Sprint 3E

1. Back up the current project folder.
2. Run `docker compose down`.
3. Do **not** run `docker compose down -v`.
4. Copy/replace this Sprint 3G package into the same existing project directory.
5. Run `docker compose up --build`.
6. Verify `http://127.0.0.1:8000/health` returns version `3.0.0-alpha.5`.
7. Run `docker compose exec backend alembic current`; expected: `0003_waiting_list (head)`.
8. Open `http://127.0.0.1:3000`.
9. Click **Operational dashboard**.

## Sprint 3G acceptance test

- Existing Sprint 3E clinic data is still visible.
- Operational dashboard opens from the main toolbar.
- A 30-day range loads without error.
- Changing the doctor filter recalculates metrics for that doctor.
- Completed appointments increase completion metrics.
- No-show appointments increase the no-show metric.
- Cancelled appointments increase the cancellation metric.
- A Sprint 3E recovered cancellation increases recovered cancelled slots and recovery rate.
- Active waiting-list entries appear in the active waiting-list metric.
- Revenue metrics are absent.
- The normal Schedule, Attention Queue, Waiting list, Administration, and appointment actions still work.

## Next

After Sprint 3G passes acceptance testing, proceed to **Sprint 4 — WhatsApp Automation and communication workflow**. Sprint 3F remains deferred until after deployment/pilot learning.
