import { Button, DialogTitle, Text } from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { FiTrash2 } from "react-icons/fi"

import { CostElementSchedulesService } from "@/client"
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
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface DeleteCostElementScheduleProps {
  id: string
  description: string | null | undefined
}

const DeleteCostElementSchedule = ({
  id,
  description,
}: DeleteCostElementScheduleProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const {
    handleSubmit,
    formState: { isSubmitting },
  } = useForm()

  const deleteSchedule = async (scheduleId: string) => {
    await CostElementSchedulesService.deleteSchedule({
      id: scheduleId,
    })
  }

  const mutation = useMutation({
    mutationFn: deleteSchedule,
    onSuccess: () => {
      showSuccessToast("Schedule deleted successfully")
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["cost-element-schedule-history"],
      })
      queryClient.invalidateQueries({
        queryKey: ["cost-element-schedule"],
      })
      // Invalidate timeline queries
      queryClient.invalidateQueries({
        queryKey: ["cost-elements-with-schedules"],
      })
      queryClient.invalidateQueries({
        queryKey: ["cost-timeline"],
      })
      queryClient.invalidateQueries({
        queryKey: ["earned-value-timeline"],
      })
    },
  })

  const onSubmit = async () => {
    mutation.mutate(id)
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
            <DialogTitle>Delete Schedule</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>
              Are you sure you want to delete this schedule registration?
              <br />
              {description && (
                <>
                  <strong>{description}</strong>
                  <br />
                </>
              )}
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

export default DeleteCostElementSchedule
