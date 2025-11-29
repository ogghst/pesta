# Branch Versioning User Guide

**Last Updated:** November 29, 2025

## Overview

Branch versioning in BackCast allows you to work on changes in isolation before merging them into the main project. Each change order gets its own branch, and all modifications within that branch are tracked separately from the main project.

## Understanding Branches

### Main Branch

The **main** branch represents the current approved state of your project. All production data lives in the main branch.

### Change Order Branches

Each change order automatically creates a branch named `co-{identifier}`. This branch:
- Contains a copy of relevant project data
- Allows independent modifications
- Can be compared with main before merging
- Is automatically cleaned up after merging

## Branch Operations

### Switching Branches

1. Use the **Branch Selector** dropdown at the top of the project view
2. Select the branch you want to view
3. All data displayed will be filtered to that branch

### Viewing Branch Information

When a branch is selected:
- The branch name is displayed in the UI
- All tables and views show only data from that branch
- Reports can be generated for the selected branch

### Branch Status

Branches can have different statuses:
- **Active**: Branch is currently being worked on
- **Merged**: Branch has been merged into main
- **Locked**: Branch is locked and cannot be modified
- **Deleted**: Branch has been soft-deleted

## Branch Comparison

### Comparing Branches

To see differences between branches:

1. Select the branch you want to compare
2. Click **Compare with Main** or use the comparison view
3. Review the differences:
   - **Creates**: New items in the branch
   - **Updates**: Modified items
   - **Deletes**: Removed items
   - **Financial Impact**: Budget and revenue changes

### Understanding Differences

- **Green**: Items added in the branch
- **Yellow**: Items modified in the branch
- **Red**: Items deleted in the branch

## Branch Merging

### Merge Preview

Before merging, you can preview what will happen:

1. Click **Merge Branch** on a change order
2. Review the merge preview:
   - All changes that will be applied
   - Potential conflicts
   - Financial impact summary

### Resolving Conflicts

If conflicts are detected:

1. Review each conflict
2. Choose which version to keep:
   - **Branch Version**: Use the branch's version
   - **Main Version**: Keep the main version
   - **Manual**: Manually resolve the conflict
3. Confirm your choices
4. Proceed with the merge

### Merging Process

1. Click **Merge Branch**
2. Review the merge preview
3. Resolve any conflicts
4. Click **Confirm Merge**
5. Wait for the merge to complete

After merging:
- All branch changes are applied to main
- The branch is soft-deleted
- A notification is sent to relevant users

## Branch Management

### Branch Locking

Branches can be locked to prevent modifications:

1. Open the branch management view
2. Click **Lock Branch**
3. Provide a reason for locking
4. The branch is now read-only

To unlock:
1. Open the branch management view
2. Click **Unlock Branch**
3. Provide a reason for unlocking

### Branch Cloning

You can clone an existing branch:

1. Open the branch management view
2. Click **Clone Branch**
3. Provide a name for the new branch
4. The new branch contains a copy of all data from the source branch

### Branch Templates

Use branch templates to quickly create branches with predefined structures:

1. Open the branch management view
2. Click **Use Template**
3. Select a template
4. Customize as needed
5. Create the branch

## Branch Permissions

### Setting Permissions

Control who can modify branches:

1. Open the branch management view
2. Click **Permissions**
3. Set permissions for:
   - **Read**: Can view branch data
   - **Write**: Can modify branch data
   - **Merge**: Can merge the branch
   - **Admin**: Full control

### Permission Levels

- **Project Manager**: Full access to all branches
- **Team Member**: Access based on assigned permissions
- **Viewer**: Read-only access

## Branch Notifications

### Notification Types

You receive notifications for:
- Branch created
- Branch merged
- Branch locked/unlocked
- Merge conflicts detected
- Branch deleted

### Managing Notifications

1. Open the notifications panel
2. Review branch-related notifications
3. Click on a notification to view details
4. Mark as read when done

## Best Practices

1. **Keep Branches Focused**: Each branch should address a specific change
2. **Merge Regularly**: Don't let branches get too far out of sync with main
3. **Review Before Merging**: Always review changes before merging
4. **Document Changes**: Use clear descriptions for branch changes
5. **Lock When Needed**: Lock branches when they shouldn't be modified
6. **Clean Up**: Delete or merge old branches to keep the project organized

## Troubleshooting

### Branch Not Showing Data

- Ensure you've selected the correct branch
- Check that the branch hasn't been deleted
- Verify you have permissions to view the branch

### Merge Conflicts

- Review each conflict carefully
- Consider the impact of each choice
- When in doubt, consult with the project team

### Branch Locked

- Contact the person who locked the branch
- Check branch notifications for lock reason
- Request unlock if needed
