# Data Backup Information

## Backup Location
`data/backups/20251117_160805/`

## Backup Date
2025-11-17 16:08:05

## Backup Contents

### Core Data Files
- `portfolio_state.json` - Current portfolio state (cash, positions, costs)
- `equity_history.jsonl` - Historical equity records
- `discussion_actions.jsonl` - Agent conversation logs
- `filled_orders.jsonl` - Executed orders history
- `pending_orders.jsonl` - Pending orders (if any)

### Memory Directory
- `memory/` - Complete memory directory including:
  - `daily/` - Daily memory files
  - `index/` - Memory index files

## Backup Purpose
This backup was created before starting the system optimization work to ensure data safety and allow rollback if needed.

## Backup Script
Created using `scripts/backup_data.ps1`

## Manifest
The backup includes a `manifest.json` file with:
- Timestamp
- Date
- List of backed up files
- Backup directory location

## Restore Instructions
To restore from this backup:

1. Stop the running system
2. Copy files from `data/backups/20251117_160805/` to `data/logs/`
3. Verify file integrity
4. Restart the system

## Important Notes
- This backup was taken before optimization branch work
- Main branch data remains untouched
- Optimization branch uses separate test data
- Backup can be used to restore if needed

