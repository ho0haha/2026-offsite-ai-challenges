# Challenge 5: Migration Planner

## Task

Compare `old_schema.py` and `new_schema.py` and write a complete database migration plan.

## Requirements

Save your output to `outputs/output5.md`. The output MUST contain ALL of the following:

1. **Step-by-step migration plan** — Ordered steps to migrate from old schema to new
2. **Rollback plan** — Steps to revert the migration if something goes wrong
3. **Backwards compatibility** — Mention whether the migration is "backwards compatible" (or "backward compatible") and explain why or why not
4. **Data migration** — Describe how existing data will be moved/transformed (e.g., how `shipping_address` text becomes structured address fields, how `product_name` maps to `product_id`)

## Validation Checks

The validator will check for:
- The word "step" (as in step-by-step plan)
- The word "rollback" or "revert"
- The phrase "backwards compatible" or "backward compatible"
- The word "data" and "migration" (data migration discussion)
- At least 200 words total
