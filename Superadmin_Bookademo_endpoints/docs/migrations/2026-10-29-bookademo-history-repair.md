# Superadmin Book a Demo migration history repair

## Cause and scope

The reported database revision is `d4e5f6a7b801`, but this checkout originally
contained only the `a1b2c3d4e5f6 -> c0a1d2e3f401 -> f7a8b9c0d1e2` history.
The original notification revision and its missing ancestors were restored
unchanged from `../Superadmin_Notification_Endpoints/alembic/versions`.
The shared `a1b2c3d4e5f6` and `c0a1d2e3f401` files match that checkout exactly.

## Repair

1. Restore the seven original migrations for the ticket, demo, contact and
   notification history, including their original branch merge.
2. Add merge revision `f8b9c0d1e2f3` with parents
   `d4e5f6a7b801` and `f7a8b9c0d1e2`. Its upgrade and downgrade perform no DDL.
3. Keep all previously existing migration files unchanged. Do not stamp the
   database or edit `alembic_version` to bypass missing revisions.

For a database already at `d4e5f6a7b801`, Alembic should execute only
`f7a8b9c0d1e2` and the new merge. The booking migration adds only missing
booking columns and the preferred-time index; restored ancestors are not replayed.
An older database can execute the restored ancestors, including their original
column drops and backfills. Review that path separately before upgrading it.

## Verification and application

- Verify revision resolution with `alembic show d4e5f6a7b801`.
- Verify one head with `alembic heads` and inspect `alembic history`.
- Confirm the planned upgrade from the reported revision contains only the
  booking migration and the new merge, without opening a database connection.
- Before applying, confirm the actual current revision with `alembic current`.
- Apply with `alembic upgrade head`, then confirm `alembic current` reports
  `f8b9c0d1e2f3`. No database migration was executed as part of this source repair.

## Rollback

Before application, rollback consists of reverting the restored files and new
merge; this source repair itself does not change the database.
Do not run a generic downgrade to undo this repair: the pre-existing booking
migration's downgrade drops columns also required by the notification ancestry.
If database changes must be reversed, use a reviewed corrective migration or a
verified pre-upgrade backup. The merge revision itself changes no schema or data.
