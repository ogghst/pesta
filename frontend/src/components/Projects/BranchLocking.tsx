import {
  Alert,
  Box,
  Button,
  Heading,
  SimpleGrid,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation } from "@tanstack/react-query"
import { useState } from "react"
import { useBranch } from "@/context/BranchContext"

interface BranchLockingProps {
  projectId: string
}

type LockInfo = {
  lockedBy: string
  lockedAt: string
}

const BranchLocking = ({ projectId }: BranchLockingProps) => {
  const { availableBranches } = useBranch()
  const [locks, setLocks] = useState<Record<string, LockInfo | null>>({})
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [statusType, setStatusType] = useState<"success" | "error">("success")

  const lockMutation = useMutation({
    mutationFn: async (branch: string) => {
      const response = await fetch(
        `/api/v1/projects/${projectId}/branches/${branch}/lock`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reason: "Manual lock" }),
        },
      )
      if (!response.ok) {
        throw new Error("Failed to lock branch")
      }
    },
    onSuccess: (_, branch) => {
      setLocks((prev) => ({
        ...prev,
        [branch]: { lockedBy: "You", lockedAt: new Date().toISOString() },
      }))
      setStatusType("success")
      setStatusMessage(`Branch ${branch} locked.`)
    },
    onError: () => {
      setStatusType("error")
      setStatusMessage("Unable to lock branch. Please try again.")
    },
  })

  const unlockMutation = useMutation({
    mutationFn: async (branch: string) => {
      const response = await fetch(
        `/api/v1/projects/${projectId}/branches/${branch}/lock`,
        {
          method: "DELETE",
        },
      )
      if (!response.ok) {
        throw new Error("Failed to unlock branch")
      }
    },
    onSuccess: (_, branch) => {
      setLocks((prev) => ({ ...prev, [branch]: null }))
      setStatusType("success")
      setStatusMessage(`Branch ${branch} unlocked.`)
    },
    onError: () => {
      setStatusType("error")
      setStatusMessage("Unable to unlock branch. Please try again.")
    },
  })

  const isMutating = lockMutation.isPending || unlockMutation.isPending

  return (
    <VStack align="stretch" gap={4}>
      <Heading size="md">Branch Locking</Heading>
      <Text color="fg.muted">
        Lock a branch to prevent other editors from making changes while you are
        working.
      </Text>

      <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
        {availableBranches.map((branch) => {
          const lockInfo = locks[branch]
          const isLocked = Boolean(lockInfo)
          return (
            <Box key={branch} borderWidth="1px" borderRadius="md" p={3}>
              <Text fontWeight="semibold">{branch}</Text>
              {isLocked ? (
                <Text fontSize="sm" color="fg.muted">
                  Locked by {lockInfo?.lockedBy} at{" "}
                  {new Date(lockInfo!.lockedAt).toLocaleString()}
                </Text>
              ) : (
                <Text fontSize="sm" color="fg.muted">
                  Unlocked
                </Text>
              )}
              <Button
                mt={3}
                size="sm"
                onClick={() =>
                  isLocked
                    ? unlockMutation.mutate(branch)
                    : lockMutation.mutate(branch)
                }
                disabled={isMutating}
              >
                {isLocked ? `Unlock ${branch}` : `Lock ${branch}`}
              </Button>
            </Box>
          )
        })}
      </SimpleGrid>

      {statusMessage && (
        <Alert.Root status={statusType} borderRadius="md">
          <Alert.Title>
            {statusType === "success" ? "Success" : "Error"}
          </Alert.Title>
          <Alert.Description>{statusMessage}</Alert.Description>
        </Alert.Root>
      )}
    </VStack>
  )
}

export default BranchLocking
