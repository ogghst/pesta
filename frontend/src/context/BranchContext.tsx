import { useQuery, useQueryClient } from "@tanstack/react-query"
import {
  createContext,
  type PropsWithChildren,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react"

import { ChangeOrdersService } from "@/client"

type ViewMode = "merged" | "branch-only"

type BranchContextValue = {
  currentBranch: string
  viewMode: ViewMode
  isLoading: boolean
  setCurrentBranch: (branch: string) => void
  setViewMode: (mode: ViewMode) => void
  availableBranches: string[]
}

const BranchContext = createContext<BranchContextValue | undefined>(undefined)

export function BranchProvider({
  children,
  projectId,
}: PropsWithChildren<{ projectId: string }>) {
  const queryClient = useQueryClient()
  const storageKey = `current-branch-${projectId}`
  const viewModeStorageKey = `view-mode-${projectId}`

  // Initialize branch from localStorage or default to "main"
  const [currentBranch, setCurrentBranchState] = useState<string>(() => {
    if (typeof window !== "undefined" && projectId) {
      try {
        const key = `current-branch-${projectId}`
        const stored = localStorage.getItem(key)
        return stored || "main"
      } catch {
        return "main"
      }
    }
    return "main"
  })

  // Initialize view mode from localStorage or default to "merged"
  const [viewMode, setViewModeState] = useState<ViewMode>(() => {
    if (typeof window !== "undefined" && projectId) {
      try {
        const stored = localStorage.getItem(viewModeStorageKey)
        return (stored === "branch-only" ? "branch-only" : "merged") as ViewMode
      } catch {
        return "merged"
      }
    }
    return "merged"
  })

  // Sync branch and view mode when projectId changes
  useEffect(() => {
    if (typeof window !== "undefined" && projectId) {
      try {
        const key = `current-branch-${projectId}`
        const stored = localStorage.getItem(key)
        if (stored) {
          setCurrentBranchState(stored)
        }
        const viewModeStored = localStorage.getItem(viewModeStorageKey)
        if (viewModeStored) {
          setViewModeState(
            (viewModeStored === "branch-only"
              ? "branch-only"
              : "merged") as ViewMode,
          )
        }
      } catch {
        // Ignore errors
      }
    }
    // Only run when projectId changes, not when currentBranch or viewMode changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, viewModeStorageKey])

  // Fetch change orders to get available branches
  const { data: changeOrdersData, isLoading } = useQuery({
    queryKey: ["change-orders", projectId],
    queryFn: () =>
      ChangeOrdersService.listChangeOrders({
        projectId,
        skip: 0,
        limit: 1000,
      }),
    enabled: !!projectId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Extract unique branches from change orders
  const availableBranches = useMemo(() => {
    const branches = new Set<string>(["main"]) // Always include 'main'
    changeOrdersData?.forEach((co) => {
      if (co.branch) {
        branches.add(co.branch)
      }
    })
    return Array.from(branches).sort()
  }, [changeOrdersData])

  const setCurrentBranch = useCallback(
    (branch: string) => {
      setCurrentBranchState(branch)
      // Reset view mode to 'merged' when branch changes (invalidation)
      setViewModeState("merged")
      // Persist branch selection to localStorage
      if (typeof window !== "undefined" && projectId) {
        try {
          localStorage.setItem(storageKey, branch)
          // Reset view mode in localStorage
          localStorage.setItem(viewModeStorageKey, "merged")
        } catch (error) {
          console.warn("Failed to save branch selection", error)
        }
      }
      // Invalidate queries that depend on branch
      queryClient.invalidateQueries({
        predicate: (query) => {
          // Invalidate queries that have branch in their key or are branch-dependent
          const key = query.queryKey
          return (
            key.includes("wbes") ||
            key.includes("cost-elements") ||
            key.includes("change-orders")
          )
        },
        refetchType: "active",
      })
    },
    [queryClient, projectId, storageKey, viewModeStorageKey],
  )

  const setViewMode = useCallback(
    (mode: ViewMode) => {
      setViewModeState(mode)
      // Persist view mode to localStorage
      if (typeof window !== "undefined" && projectId) {
        try {
          localStorage.setItem(viewModeStorageKey, mode)
        } catch (error) {
          console.warn("Failed to save view mode", error)
        }
      }
      // Invalidate queries that depend on view mode
      queryClient.invalidateQueries({
        predicate: (query) => {
          // Invalidate queries that have viewMode in their key or are view-dependent
          const key = query.queryKey
          return (
            key.includes("wbes") ||
            key.includes("cost-elements") ||
            key.includes("change-orders")
          )
        },
        refetchType: "active",
      })
    },
    [queryClient, projectId, viewModeStorageKey],
  )

  const value = useMemo<BranchContextValue>(
    () => ({
      currentBranch,
      viewMode,
      isLoading,
      setCurrentBranch,
      setViewMode,
      availableBranches,
    }),
    [
      currentBranch,
      viewMode,
      isLoading,
      setCurrentBranch,
      setViewMode,
      availableBranches,
    ],
  )

  return (
    <BranchContext.Provider value={value}>{children}</BranchContext.Provider>
  )
}

export function useBranch() {
  const context = useContext(BranchContext)
  if (!context) {
    throw new Error("useBranch must be used within a BranchProvider")
  }
  return context
}
