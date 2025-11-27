import { Button, Text, VStack } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ChangeOrdersService, UsersService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface ChangeOrderStatusTransitionProps {
  projectId: string
  changeOrderId: string
  currentStatus: "design" | "approve" | "execute" | "cancelled"
  onSuccess?: () => void
}

const ChangeOrderStatusTransition = ({
  projectId,
  changeOrderId,
  currentStatus,
  onSuccess,
}: ChangeOrderStatusTransitionProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  // Get current user for approved_by_id and implemented_by_id
  const { data: currentUser } = useQuery({
    queryFn: () => UsersService.readUserMe(),
    queryKey: ["users", "me"],
  })

  const getNextStatus = (): "approve" | "execute" | null => {
    if (currentStatus === "design") return "approve"
    if (currentStatus === "approve") return "execute"
    return null
  }

  const nextStatus = getNextStatus()

  const transitionMutation = useMutation({
    mutationFn: (newStatus: "approve" | "execute") => {
      const requestBody: {
        workflow_status: "approve" | "execute"
        approved_by_id?: string
        implemented_by_id?: string
      } = {
        workflow_status: newStatus,
      }

      // Include approved_by_id when transitioning to approve
      if (newStatus === "approve" && currentUser?.id) {
        requestBody.approved_by_id = currentUser.id
      }

      // Include implemented_by_id when transitioning to execute
      if (newStatus === "execute" && currentUser?.id) {
        requestBody.implemented_by_id = currentUser.id
      }

      return ChangeOrdersService.transitionChangeOrderStatus({
        projectId,
        changeOrderId,
        requestBody,
      })
    },
    onSuccess: (data) => {
      showSuccessToast(
        `Change order status updated to ${data.workflow_status} successfully.`,
      )
      queryClient.invalidateQueries({ queryKey: ["change-orders"] })
      if (data.workflow_status === "execute") {
        // Invalidate branch-dependent queries after merge
        queryClient.invalidateQueries({ queryKey: ["wbes"] })
        queryClient.invalidateQueries({ queryKey: ["cost-elements"] })
      }
      onSuccess?.()
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })

  const handleTransition = () => {
    if (nextStatus) {
      transitionMutation.mutate(nextStatus)
    }
  }

  if (!nextStatus) {
    return (
      <Text color="fg.muted">
        No transitions available from status: {currentStatus}
      </Text>
    )
  }

  const transitionLabels: Record<"approve" | "execute", string> = {
    approve: "Approve",
    execute: "Execute (Merge Branch)",
  }

  return (
    <VStack gap={2} align="stretch">
      <Text fontSize="sm" color="fg.muted">
        Current status: <strong>{currentStatus}</strong>
      </Text>
      <Button
        variant="solid"
        colorPalette="blue"
        onClick={handleTransition}
        disabled={transitionMutation.isPending || !currentUser?.id}
        loading={transitionMutation.isPending}
      >
        Transition to {transitionLabels[nextStatus]}
      </Button>
      {nextStatus === "execute" && (
        <Text fontSize="xs" color="orange.500">
          Warning: This will merge the branch into main and cannot be undone.
        </Text>
      )}
    </VStack>
  )
}

export default ChangeOrderStatusTransition
