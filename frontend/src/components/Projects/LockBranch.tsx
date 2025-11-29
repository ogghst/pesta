import { Button, Text, Textarea, VStack } from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { FiLock } from "react-icons/fi"
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
import { Field } from "../ui/field"

interface LockBranchProps {
  projectId: string
  branch: string
  isLocked: boolean
}

interface LockBranchForm {
  reason: string
}

const LockBranch = ({ projectId, branch, isLocked }: LockBranchProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting },
  } = useForm<LockBranchForm>({
    defaultValues: {
      reason: "",
    },
  })

  const mutation = useMutation({
    mutationFn: async (data: LockBranchForm) => {
      const apiBase =
        OpenAPI.BASE ||
        window.env?.VITE_API_URL ||
        import.meta.env.VITE_API_URL ||
        "http://localhost:8010"
      const token = localStorage.getItem("access_token") || ""
      const response = await fetch(
        `${apiBase}/api/v1/projects/${projectId}/branches/${branch}/lock`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ reason: data.reason || null }),
        },
      )
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Failed to lock branch")
      }
      return response.json()
    },
    onSuccess: () => {
      showSuccessToast(`Branch ${branch} locked successfully.`)
      reset()
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

  const onSubmit = async (data: LockBranchForm) => {
    await mutation.mutateAsync(data)
  }

  if (isLocked) {
    return null
  }

  return (
    <DialogRoot
      size={{ base: "xs", md: "md" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          aria-label="Lock branch"
          title="Lock branch"
          colorPalette="orange"
        >
          <FiLock fontSize="16px" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Lock Branch</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>
              Lock branch <strong>{branch}</strong> to prevent modifications.
            </Text>
            <VStack gap={4}>
              <Field label="Reason (optional)">
                <Textarea
                  {...register("reason")}
                  placeholder="Optional reason for locking this branch"
                  rows={3}
                  disabled={isSubmitting}
                />
              </Field>
            </VStack>
          </DialogBody>
          <DialogFooter gap={2}>
            <DialogCloseTrigger asChild>
              <Button
                variant="subtle"
                colorPalette="gray"
                disabled={isSubmitting}
                onClick={() => reset()}
              >
                Cancel
              </Button>
            </DialogCloseTrigger>
            <Button
              variant="solid"
              colorPalette="orange"
              type="submit"
              disabled={isSubmitting}
              loading={isSubmitting}
            >
              Lock Branch
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default LockBranch
