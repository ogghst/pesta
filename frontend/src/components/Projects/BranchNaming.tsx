import {
  Alert,
  Box,
  Button,
  Flex,
  Heading,
  Input,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useCallback, useEffect, useMemo, useState } from "react"
import { useBranch } from "@/context/BranchContext"

interface BranchNamingProps {
  projectId: string
  onNamesChange?: (names: Record<string, string>) => void
}

const NAME_PATTERN = /^[A-Za-z0-9][A-Za-z0-9\s\-_/().]*$/

const BranchNaming = ({ projectId, onNamesChange }: BranchNamingProps) => {
  const { availableBranches, isLoading } = useBranch()
  const storageKey = `branch-names-${projectId}`
  const [names, setNames] = useState<Record<string, string>>({})
  const [initialNames, setInitialNames] = useState<Record<string, string>>({})
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  const buildMapFromSource = useCallback(
    (source: Record<string, string> | undefined) => {
      const map: Record<string, string> = {}
      availableBranches.forEach((branch) => {
        map[branch] = source?.[branch] ?? branch
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
      const next = buildMapFromSource(parsed)
      setNames(next)
      setInitialNames(next)
    } catch (error) {
      console.warn("Failed to load branch names", error)
      const fallback = buildMapFromSource(undefined)
      setNames(fallback)
      setInitialNames(fallback)
    }
  }, [storageKey, buildMapFromSource])

  const errors = useMemo(() => {
    const result: Record<string, string | null> = {}
    const seenNames = new Map<string, string>()
    availableBranches.forEach((branch) => {
      const value = (names[branch] ?? branch).trim()
      if (!NAME_PATTERN.test(value)) {
        result[branch] =
          "Use letters, numbers, spaces, dash, underscore, slash, parentheses, or dots."
        return
      }
      const normalized = value.toLowerCase()
      const existing = seenNames.get(normalized)
      if (existing && existing !== branch) {
        result[branch] = "Name must be unique across branches."
        return
      }
      seenNames.set(normalized, branch)
      result[branch] = null
    })
    return result
  }, [names, availableBranches])

  const hasErrors = Object.values(errors).some(Boolean)
  const hasChanges = availableBranches.some((branch) => {
    const current = (names[branch] ?? branch).trim()
    const initial = (initialNames[branch] ?? branch).trim()
    return current !== initial
  })

  const handleNameChange = (branch: string, value: string) => {
    setStatusMessage(null)
    setNames((prev) => ({ ...prev, [branch]: value }))
  }

  const handleSave = () => {
    if (hasErrors || !hasChanges) {
      return
    }
    const normalized = availableBranches.reduce<Record<string, string>>(
      (acc, branch) => {
        acc[branch] = (names[branch] ?? branch).trim() || branch
        return acc
      },
      {},
    )

    try {
      localStorage.setItem(storageKey, JSON.stringify(normalized))
      setInitialNames(normalized)
      setStatusMessage("Names saved successfully.")
      onNamesChange?.(normalized)
    } catch (error) {
      console.warn("Failed to save branch names", error)
    }
  }

  return (
    <Box borderWidth="1px" borderRadius="lg" p={4}>
      <VStack align="stretch" gap={4}>
        <Box>
          <Heading size="md">Branch Naming</Heading>
          <Text color="fg.muted">
            Assign friendly names to branches to make project navigation easier.
          </Text>
        </Box>

        {availableBranches.length === 0 ? (
          <Text color="fg.muted">No branches available yet.</Text>
        ) : (
          availableBranches.map((branch) => (
            <Box key={branch}>
              <Text fontWeight="medium">Display name for {branch}</Text>
              <Input
                mt={1}
                value={names[branch] ?? branch}
                aria-label={`Display name for ${branch}`}
                data-invalid={Boolean(errors[branch]) || undefined}
                onChange={(event) =>
                  handleNameChange(branch, event.target.value)
                }
                placeholder={`e.g., ${branch.toUpperCase()}`}
              />
              {errors[branch] && (
                <Text mt={1} fontSize="xs" color="fg.error">
                  {errors[branch]}
                </Text>
              )}
            </Box>
          ))
        )}

        {statusMessage && (
          <Alert.Root status="success">
            <Alert.Title>Names saved</Alert.Title>
            <Alert.Description>{statusMessage}</Alert.Description>
          </Alert.Root>
        )}

        <Flex justify="flex-end">
          <Button
            colorPalette="blue"
            onClick={handleSave}
            disabled={isLoading || hasErrors || !hasChanges}
          >
            Save Names
          </Button>
        </Flex>
      </VStack>
    </Box>
  )
}

export default BranchNaming
