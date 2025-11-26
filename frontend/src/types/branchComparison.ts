export type BranchComparisonChangeType = "wbe" | "cost_element"

export interface BranchComparisonChange {
  type: BranchComparisonChangeType
  entity_id: string
  description: string
  revenue_change?: number
  budget_change?: number
}

export interface BranchComparisonSummary {
  creates_count: number
  updates_count: number
  deletes_count: number
  total_budget_change: number
  total_revenue_change: number
}

export interface BranchComparisonResult {
  project_id: string
  branch: string
  base_branch: string
  summary: BranchComparisonSummary
  creates: BranchComparisonChange[]
  updates: BranchComparisonChange[]
  deletes: BranchComparisonChange[]
}

export interface BranchComparisonConflict {
  entity_id: string
  entity_type: string
  field: string
  branch_value: string
  base_value: string
}

export interface LegacyBranchComparisonFields {
  financial_impact?: {
    total_budget_change: string
    total_revenue_change: string
  }
  conflicts?: BranchComparisonConflict[]
}

export type BranchComparisonResponse = BranchComparisonResult &
  LegacyBranchComparisonFields
