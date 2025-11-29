import { Button, Text } from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { FiUnlock } from "react-icons/fi"
import { OpenAPI } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog"

interface UnlockBranchProps {
  projectId: string
  branch: string
  isLocked: boolean
}

const UnlockBranch = ({ projectId, branch, isLocked }: UnlockBranchProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const {
    handleSubmit,
    formState: { isSubmitting },
  } = useForm()

  const mutation = useMutation({
    mutationFn: async () => {
      const apiBase =
        OpenAPI.BASE ||
        window.env?.VITE_API_URL ||
        import.meta.env.VITE_API_URL ||
        "http://localhost:8010"
      const token = localStorage.getItem("access_token") || ""
      const response = await fetch(
        `${apiBase}/api/v1/projects/${projectId}/branches/${branch}/lock`,
        {
          method: "DELETE",
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        },
      )
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Failed to unlock branch")
      }
      return response.json()
    },
    onSuccess: () => {
      showSuccessToast(`Branch ${branch} unlocked successfully.`)
      setIsOpen(false)
    },
    onError: (err: Error) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["branch-locks", projectId] })
      queryClient.invalidateQueries({ queryKey: ["change-orders", projectId] })
    },
  })

  const onSubmit = async () => {
    await mutation.mutateAsync()
  }

  if (!isLocked) {
    return null
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
        <Button
          variant="ghost"
          size="sm"
          aria-label="Unlock branch"
          title="Unlock branch"
          colorPalette="green"
        >
          <FiUnlock fontSize="16px" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Unlock Branch</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>
              Are you sure you want to unlock branch <strong>{branch}</strong>?
              This will allow modifications to the branch.
            </Text>
          </DialogBody>
          <DialogFooter gap={2}>
            <DialogCloseTrigger asChild>
              <Button
                variant="subtle"
                colorPalette="gray"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            </DialogCloseTrigger>
            <Button
              variant="solid"
              colorPalette="green"
              type="submit"
              disabled={isSubmitting}
              loading={isSubmitting}
            >
              Unlock Branch
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default UnlockBranch
