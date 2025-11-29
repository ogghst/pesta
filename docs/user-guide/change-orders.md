# Change Orders User Guide

**Last Updated:** November 29, 2025

## Overview

Change Orders in BackCast allow you to manage modifications to project scope, budget, and schedule. Each change order operates in its own branch, enabling you to work on changes independently before merging them into the main project.

## Creating a Change Order

1. Navigate to your project detail page
2. Click on the **Change Orders** tab
3. Click the **Add Change Order** button
4. Fill in the required information:
   - **Title**: A brief description of the change
   - **Description**: Detailed explanation of the change
   - **Requesting Party**: Who requested the change (e.g., Customer, Internal)
   - **Effective Date**: When the change should take effect
5. Click **Create** to create the change order

When a change order is created, a new branch is automatically created for it. This branch allows you to make modifications without affecting the main project.

## Change Order Workflow

Change orders follow a workflow with the following statuses:

- **Design**: Initial creation, changes are being designed
- **Review**: Changes are under review
- **Approved**: Changes have been approved
- **Implemented**: Changes have been implemented
- **Merged**: Changes have been merged into the main branch
- **Cancelled**: Change order was cancelled

### Updating Workflow Status

1. Open the change order detail view
2. Use the status transition buttons to move through the workflow
3. The system will validate that transitions are allowed

## Working with Change Order Branches

### Viewing Branch Data

When you select a change order branch, all project data (WBEs, Cost Elements, etc.) will be filtered to show only data in that branch. This allows you to:

- See what changes have been made in the branch
- Modify data without affecting the main project
- Compare branch data with main branch

### Making Changes in a Branch

1. Select the change order branch from the branch selector
2. Navigate to the data you want to modify (e.g., WBEs, Cost Elements)
3. Make your changes as usual
4. All changes are automatically saved to the branch

### Branch Comparison

To see what has changed in a branch compared to main:

1. Select the change order branch
2. Click **Compare with Main** or use the branch comparison view
3. Review the differences:
   - **Creates**: New items added in the branch
   - **Updates**: Items modified in the branch
   - **Deletes**: Items removed in the branch
   - **Financial Impact**: Summary of budget and revenue changes

## Merging Change Orders

When a change order is ready to be merged into the main project:

1. Navigate to the change order detail view
2. Click **Merge Branch**
3. Review the merge preview:
   - See all changes that will be applied
   - Check for conflicts
4. Resolve any conflicts if present
5. Click **Confirm Merge**

After merging:
- All changes from the branch are applied to main
- The change order status is updated to "Merged"
- The branch is soft-deleted (can be restored if needed)

## Managing Change Orders

### Editing Change Orders

1. Open the change order detail view
2. Click **Edit**
3. Modify the fields as needed
4. Click **Save**

### Viewing Change Order History

Each change order maintains a version history. To view it:

1. Open the change order detail view
2. Click **Version History**
3. Review all versions and changes made over time

### Deleting Change Orders

Change orders can be soft-deleted:

1. Open the change order detail view
2. Click **Delete**
3. Confirm the deletion

Soft-deleted change orders can be restored from the deleted items view.

## Best Practices

1. **Use Descriptive Titles**: Make change order titles clear and descriptive
2. **Document Changes**: Provide detailed descriptions of what is changing and why
3. **Review Before Merging**: Always review the merge preview before merging
4. **Resolve Conflicts Early**: Address merge conflicts as soon as they appear
5. **Keep Branches Focused**: Each change order should focus on a specific set of related changes

## Examples

### Example: Adding a New Machine

1. Create a change order titled "Add Machine XYZ"
2. In the branch, add the new WBE for Machine XYZ
3. Add cost elements for the machine
4. Review the financial impact
5. Once approved, merge the branch

### Example: Modifying Budget Allocation

1. Create a change order titled "Adjust Budget Allocation"
2. In the branch, modify cost element budgets
3. Review the variance analysis
4. Once approved, merge the branch
