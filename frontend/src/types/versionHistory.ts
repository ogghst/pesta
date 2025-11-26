export interface VersionHistoryEntry {
  version: number
  status?: string | null
  branch?: string | null
  created_at?: string | null
  updated_at?: string | null
  data?: Record<string, unknown>
}

export interface VersionHistoryResponse {
  entity_type: string
  entity_id: string
  branch?: string | null
  count: number
  versions: VersionHistoryEntry[]
}
