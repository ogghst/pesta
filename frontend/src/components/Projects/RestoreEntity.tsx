import { Button } from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  type ChangeOrderPublic,
  type CostElementPublic,
  type ProjectPublic,
  RestoreService,
  type WBEPublic,
} from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface RestoreEntityProps {
  entityType: "wbe" | "costelement" | "changeorder" | "project"
  entityId: string
  branch?: string
}

const RestoreEntity = ({
  entityType,
  entityId,
  branch,
}: RestoreEntityProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const restoreMutation = useMutation<
    WBEPublic | CostElementPublic | ChangeOrderPublic | ProjectPublic,
    ApiError,
    void
  >({
    mutationFn: async () => {
      switch (entityType) {
        case "wbe":
          return await RestoreService.restoreWbe({
            wbeId: entityId,
            branch,
          })
        case "costelement":
          return await RestoreService.restoreCostElement({
            costElementId: entityId,
            branch,
          })
        case "changeorder":
          return await RestoreService.restoreChangeOrder({
            changeOrderId: entityId,
          })
        case "project":
          return await RestoreService.restoreProject({
            projectId: entityId,
          })
        default:
          throw new Error(`Unsupported entity type: ${entityType}`)
      }
    },
    onSuccess: () => {
      showSuccessToast(`${entityType} restored successfully.`)
      queryClient.invalidateQueries({
        queryKey: [
          entityType === "wbe"
            ? "wbes"
            : entityType === "costelement"
              ? "cost-elements"
              : entityType === "changeorder"
                ? "change-orders"
                : "projects",
        ],
      })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })

  return (
    <Button
      variant="outline"
      colorPalette="green"
      size="sm"
      onClick={() => restoreMutation.mutate()}
      disabled={restoreMutation.isPending}
      loading={restoreMutation.isPending}
    >
      Restore
    </Button>
  )
}

export default RestoreEntity
