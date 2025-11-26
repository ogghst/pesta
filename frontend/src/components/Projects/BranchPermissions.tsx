import {
  Alert,
  Box,
  Button,
  Flex,
  Heading,
  NativeSelect,
  SimpleGrid,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useCallback, useEffect, useMemo, useState } from "react"
import { useBranch } from "@/context/BranchContext"

interface BranchPermissionsProps {
  projectId: string
  onSave?: (permissions: Record<string, string>) => void
}

const roleOptions = [
  { value: "viewer", label: "Viewer (read-only)" },
  { value: "editor", label: "Editor (update branch data)" },
  { value: "approver", label: "Approver (merge & delete)" },
  { value: "admin", label: "Admin (full control)" },
]

const roleWeight: Record<string, number> = {
  viewer: 1,
  editor: 2,
  approver: 3,
  admin: 4,
}

const BranchPermissions = ({ projectId, onSave }: BranchPermissionsProps) => {
  const { availableBranches, isLoading } = useBranch()
  const storageKey = `branch-permissions-${projectId}`
  const [permissions, setPermissions] = useState<Record<string, string>>({})
  const [initialPermissions, setInitialPermissions] = useState<
    Record<string, string>
  >({})
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  const buildMap = useCallback(
    (source?: Record<string, string>) => {
      const map: Record<string, string> = {}
      availableBranches.forEach((branch) => {
        map[branch] =
          source?.[branch] ?? (branch === "main" ? "approver" : "editor")
      })
      return map
    },
    [availableBranches],
  )

  useEffect(() => {
    try {
      const stored = localStorage.getItem(storageKey)
      const parsed = stored
        ? (JSON.parse(stored) as Record<string, string>)
        : undefined
      const next = buildMap(parsed)
      setPermissions(next)
      setInitialPermissions(next)
    } catch (error) {
      console.warn("Failed to load branch permissions", error)
      const fallback = buildMap()
      setPermissions(fallback)
      setInitialPermissions(fallback)
    }
  }, [storageKey, buildMap])

  const errors = useMemo(() => {
    const result: Record<string, string | null> = {}
    availableBranches.forEach((branch) => {
      const role = permissions[branch] ?? "viewer"
      if (branch === "main" && roleWeight[role] < roleWeight.approver) {
        result[branch] = "Main branch requires approver or admin access."
        return
      }
      result[branch] = null
    })
    return result
  }, [permissions, availableBranches])

  const hasErrors = Object.values(errors).some(Boolean)
  const hasChanges = availableBranches.some((branch) => {
    const current = permissions[branch]
    const initial = initialPermissions[branch]
    return current !== initial
  })

  const handleRoleChange = (branch: string, value: string) => {
    setStatusMessage(null)
    setPermissions((prev) => ({ ...prev, [branch]: value }))
  }

  const handleSave = () => {
    if (hasErrors || !hasChanges) {
      return
    }
    try {
      localStorage.setItem(storageKey, JSON.stringify(permissions))
      setInitialPermissions(permissions)
      setStatusMessage("Permissions updated successfully.")
      onSave?.(permissions)
    } catch (error) {
      console.warn("Failed to persist branch permissions", error)
    }
  }

  return (
    <Box borderWidth="1px" borderRadius="lg" p={4}>
      <VStack align="stretch" gap={4}>
        <Box>
          <Heading size="md">Branch Permissions</Heading>
          <Text color="fg.muted">
            Control who can edit, approve, or delete each branch before merging.
          </Text>
        </Box>

        {availableBranches.length === 0 ? (
          <Text color="fg.muted">No branches available.</Text>
        ) : (
          <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
            {availableBranches.map((branch) => (
              <Box key={branch} borderWidth="1px" borderRadius="md" p={3}>
                <Text fontWeight="semibold">{branch}</Text>
                <Text fontSize="sm" color="fg.muted" mb={2}>
                  Assign the minimum role required to work on this branch.
                </Text>
                <NativeSelect.Root>
                  <NativeSelect.Field
                    aria-label={branch}
                    value={permissions[branch] ?? "viewer"}
                    onChange={(event) =>
                      handleRoleChange(branch, event.target.value)
                    }
                    data-invalid={Boolean(errors[branch]) || undefined}
                  >
                    {roleOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </NativeSelect.Field>
                  <NativeSelect.Indicator />
                </NativeSelect.Root>
                {errors[branch] && (
                  <Text mt={2} fontSize="xs" color="fg.error">
                    {errors[branch]}
                  </Text>
                )}
              </Box>
            ))}
          </SimpleGrid>
        )}

        {statusMessage && (
          <Alert.Root status="success">
            <Alert.Title>Permissions updated</Alert.Title>
            <Alert.Description>{statusMessage}</Alert.Description>
          </Alert.Root>
        )}

        <Flex justify="flex-end">
          <Button
            colorPalette="blue"
            onClick={handleSave}
            disabled={isLoading || hasErrors || !hasChanges}
          >
            Save Permissions
          </Button>
        </Flex>
      </VStack>
    </Box>
  )
}

export default BranchPermissions
