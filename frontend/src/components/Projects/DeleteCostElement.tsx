import { Button, DialogTitle, Text } from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { FiTrash2 } from "react-icons/fi"

import { type CostElementPublic, CostElementsService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import {
  DialogActionTrigger,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTrigger,
} from "@/components/ui/dialog"
import { useBranch } from "@/context/BranchContext"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface DeleteCostElementProps {
  costElement: CostElementPublic
  departmentName: string
}

const DeleteCostElement = ({
  costElement,
  departmentName,
}: DeleteCostElementProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const { currentBranch } = useBranch()
  const {
    handleSubmit,
    formState: { isSubmitting },
  } = useForm()

  const deleteCostElement = async (entityId: string, branch: string) => {
    await CostElementsService.deleteCostElement({ entityId, branch })
  }

  const mutation = useMutation({
    mutationFn: () =>
      deleteCostElement(
        costElement.entity_id,
        currentBranch || costElement.branch || "main",
      ),
    onSuccess: () => {
      showSuccessToast("Cost element deleted successfully")
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["cost-elements"] })
      queryClient.invalidateQueries({ queryKey: ["cost-summary"] })
    },
  })

  const onSubmit = async () => {
    mutation.mutate()
  }

  return (
    <DialogRoot
      size={{ base: "xs", md: "md" }}
      placement="center"
      role="alertdialog"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" colorPalette="red">
          <FiTrash2 fontSize="16px" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Delete Cost Element</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>
              Are you sure you want to delete <strong>{departmentName}</strong>?
              This action cannot be undone.
            </Text>
          </DialogBody>

          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button
                variant="subtle"
                colorPalette="gray"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              colorPalette="red"
              type="submit"
              loading={isSubmitting}
            >
              Delete
            </Button>
          </DialogFooter>
          <DialogCloseTrigger />
        </form>
      </DialogContent>
    </DialogRoot>
  )
}

export default DeleteCostElement
