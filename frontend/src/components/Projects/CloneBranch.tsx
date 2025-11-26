import {
  Alert,
  Box,
  Button,
  Heading,
  Input,
  NativeSelect,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect, useMemo, useState } from "react"
import { useBranch } from "@/context/BranchContext"

interface CloneBranchProps {
  projectId: string
}

const CloneBranch = ({ projectId }: CloneBranchProps) => {
  const { availableBranches } = useBranch()
  const queryClient = useQueryClient()
  const [sourceBranch, setSourceBranch] = useState<string>("")
  const [newBranchName, setNewBranchName] = useState("")
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [statusType, setStatusType] = useState<"success" | "error">("success")

  useEffect(() => {
    if (availableBranches.length === 0) {
      return
    }
    if (!sourceBranch || !availableBranches.includes(sourceBranch)) {
      setSourceBranch(availableBranches[0])
      return
    }
    if (
      sourceBranch === "main" &&
      availableBranches.some((branch) => branch !== "main")
    ) {
      const next = availableBranches.find((branch) => branch !== "main")
      if (next) {
        setSourceBranch(next)
      }
    }
  }, [availableBranches, sourceBranch])

  const nameError = useMemo(() => {
    if (!newBranchName) {
      return null
    }
    if (!/^[a-z0-9-]+$/i.test(newBranchName)) {
      return "Branch name can contain letters, numbers, and hyphens."
    }
    if (
      availableBranches.some(
        (branch) => branch.toLowerCase() === newBranchName.toLowerCase(),
      )
    ) {
      return "Branch name already exists."
    }
    return null
  }, [newBranchName, availableBranches])

  const mutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(
        `/api/v1/projects/${projectId}/branches/${sourceBranch}/clone`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ new_branch: newBranchName }),
        },
      )
      if (!response.ok) {
        throw new Error("Failed to clone branch")
      }
      return (await response.json()) as { branch: string }
    },
    onSuccess: (data) => {
      setStatusType("success")
      setStatusMessage(`Branch cloned to ${data.branch ?? newBranchName}.`)
      queryClient.invalidateQueries({ queryKey: ["change-orders", projectId] })
      setNewBranchName("")
    },
    onError: () => {
      setStatusType("error")
      setStatusMessage("Unable to clone branch. Please try again.")
    },
  })

  const canSubmit =
    Boolean(sourceBranch) &&
    newBranchName.trim().length > 0 &&
    !nameError &&
    !mutation.isPending

  return (
    <Box borderWidth="1px" borderRadius="lg" p={4}>
      <VStack align="stretch" gap={4}>
        <Heading size="md">Clone Branch</Heading>
        <Text color="fg.muted">
          Select a branch to duplicate and provide a name for the new branch.
          All WBEs and cost elements will be copied into the new branch.
        </Text>

        <Box>
          <Text fontWeight="semibold" mb={1}>
            Select branch to clone
          </Text>
          <NativeSelect.Root>
            <NativeSelect.Field
              aria-label="Select branch to clone"
              value={sourceBranch}
              onChange={(event) => setSourceBranch(event.target.value)}
            >
              {availableBranches.map((branch) => (
                <option key={branch} value={branch}>
                  {branch}
                </option>
              ))}
            </NativeSelect.Field>
            <NativeSelect.Indicator />
          </NativeSelect.Root>
        </Box>

        <Box>
          <Text fontWeight="semibold" mb={1}>
            New branch name
          </Text>
          <Input
            aria-label="New branch name"
            placeholder="e.g., co-001-clone"
            value={newBranchName}
            onChange={(event) => {
              setStatusMessage(null)
              setNewBranchName(event.target.value)
            }}
            data-invalid={Boolean(nameError) || undefined}
          />
          {nameError && (
            <Text mt={1} fontSize="xs" color="fg.error">
              {nameError}
            </Text>
          )}
        </Box>

        <Button
          colorPalette="blue"
          onClick={() => mutation.mutate()}
          disabled={!canSubmit}
          loading={mutation.isPending}
        >
          Clone Branch
        </Button>

        {statusMessage && (
          <Alert.Root status={statusType} borderRadius="md">
            <Alert.Title>
              {statusType === "success" ? "Branch Cloned" : "Clone Failed"}
            </Alert.Title>
            <Alert.Description>{statusMessage}</Alert.Description>
          </Alert.Root>
        )}
      </VStack>
    </Box>
  )
}

export default CloneBranch
