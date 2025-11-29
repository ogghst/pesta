# Version History User Guide

**Last Updated:** November 29, 2025

## Overview

Version history in BackCast tracks all changes made to project entities over time. Every modification creates a new version, allowing you to see what changed, when it changed, and who made the change.

## Understanding Versions

### What is Versioning?

Versioning automatically tracks:
- **What** changed (the data modifications)
- **When** it changed (timestamp)
- **Who** made the change (user)
- **Why** it changed (if documented)

### Version Numbers

Versions are numbered sequentially:
- Version 1: Initial creation
- Version 2: First modification
- Version 3: Second modification
- And so on...

### Version Status

Each version has a status:
- **Active**: Current version in use
- **Deleted**: Version was soft-deleted
- **Merged**: Version was merged from a branch
- **Archived**: Old version archived for storage

## Viewing Version History

### Accessing Version History

1. Navigate to any entity (Project, WBE, Cost Element, etc.)
2. Click **Version History** button or link
3. View the version history panel

### Version History Display

The version history shows:
- **Version Number**: Sequential version identifier
- **Status**: Current status of the version
- **Created At**: When the version was created
- **Created By**: User who created the version
- **Changes**: Summary of what changed

### Viewing Version Details

1. Click on a version in the history
2. View detailed information:
   - All field values at that version
   - Changes from previous version
   - User comments (if any)

## Comparing Versions

### Comparing Two Versions

1. Open the version history
2. Select two versions to compare
3. Click **Compare Versions**
4. Review the differences:
   - **Changed Fields**: Fields that differ
   - **Old Values**: Values in the older version
   - **New Values**: Values in the newer version

### Understanding Differences

- **Green**: New or increased values
- **Red**: Deleted or decreased values
- **Yellow**: Modified values

## Version Rollback

### Rolling Back to a Previous Version

1. Open the version history
2. Select the version you want to roll back to
3. Click **Rollback to This Version**
4. Confirm the rollback
5. A new version is created with the old values

**Note**: Rollback creates a new version, it doesn't delete existing versions. This preserves the full history.

### When to Rollback

Use rollback when:
- An error was made in recent changes
- You need to revert to a known good state
- You want to undo a specific modification

## Version Archival

### Archived Versions

Old versions are automatically archived after a retention period (typically 1 year). Archived versions:
- Are still accessible
- Can be restored if needed
- Don't appear in regular version lists by default

### Viewing Archived Versions

1. Open the version history
2. Enable **Show Archived** option
3. Archived versions will appear in the list

### Restoring Archived Versions

1. Find the archived version
2. Click **Restore**
3. The version is restored to active status

## Version History in Branches

### Branch-Specific Versions

Each branch maintains its own version history:
- Versions in branches are separate from main
- Branch versions are numbered independently
- When merged, branch versions are preserved

### Viewing Branch Versions

1. Select a branch
2. Open version history for any entity
3. View versions specific to that branch

## Best Practices

1. **Review History Regularly**: Check version history to understand changes
2. **Use Descriptive Comments**: Add comments when making significant changes
3. **Compare Before Modifying**: Compare versions to understand impact
4. **Don't Delete Versions**: Preserve history by using soft-delete instead
5. **Archive Old Versions**: Let the system archive old versions automatically

## Examples

### Example: Tracking Project Name Changes

1. Project created: Version 1, name = "Project Alpha"
2. Name changed: Version 2, name = "Project Alpha v2"
3. Name changed again: Version 3, name = "Project Beta"

Version history shows all three names with timestamps.

### Example: Rolling Back Budget Changes

1. Budget modified incorrectly: Version 5
2. Open version history
3. Select Version 4 (previous correct version)
4. Rollback to Version 4
5. New Version 6 is created with Version 4's budget values

### Example: Comparing Cost Element Versions

1. Open cost element version history
2. Select Version 2 and Version 5
3. Compare to see:
   - Budget changes
   - Schedule changes
   - Department changes
   - All modifications between versions

## Troubleshooting

### Version History Not Showing

- Ensure the entity has been modified at least once
- Check that you have permissions to view history
- Verify the entity hasn't been hard-deleted

### Can't Rollback

- Ensure you have write permissions
- Check that the version isn't archived
- Verify the entity isn't locked

### Missing Versions

- Check if archived versions are hidden
- Verify soft-deleted versions aren't filtered out
- Contact administrator if versions seem missing
