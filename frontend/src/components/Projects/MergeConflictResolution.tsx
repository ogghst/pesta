import {
  Box,
  Button,
  Flex,
  Heading,
  Input,
  NativeSelect,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMemo, useState } from "react"

type Conflict = {
  id: string
  entityId: string
  entityType: string
  field: string
  branchValue: string
  baseValue: string
  notes?: string
}

interface MergeConflictResolutionProps {
  conflicts: Conflict[]
  onResolve?: (resolution: Record<string, string>) => void
}

const resolutionOptions = [
  { value: "branch", label: "Keep branch value" },
  { value: "base", label: "Keep main branch value" },
  { value: "custom", label: "Enter custom value" },
]

const MergeConflictResolution = ({
  conflicts,
  onResolve,
}: MergeConflictResolutionProps) => {
  const [resolutions, setResolutions] = useState<Record<string, string>>(() =>
    conflicts.reduce<Record<string, string>>((acc, conflict) => {
      acc[conflict.id] = "branch"
      return acc
    }, {}),
  )
  const [customValues, setCustomValues] = useState<Record<string, string>>({})

  const conflictCount = conflicts.length
  const summary = useMemo(() => {
    const counts = { branch: 0, base: 0, custom: 0 }
    Object.values(resolutions).forEach((value) => {
      counts[value as keyof typeof counts] += 1
    })
    return counts
  }, [resolutions])

  if (conflictCount === 0) {
    return (
      <Box borderWidth="1px" borderRadius="lg" p={4}>
        <Heading size="md">Merge Conflicts</Heading>
        <Text color="fg.muted">No conflicts detected. Nothing to resolve.</Text>
      </Box>
    )
  }

  const handleResolutionChange = (conflictId: string, value: string) => {
    setResolutions((prev) => ({ ...prev, [conflictId]: value }))
  }

  const handleCustomChange = (conflictId: string, value: string) => {
    setCustomValues((prev) => ({ ...prev, [conflictId]: value }))
  }

  const customValueMissing = conflicts.some((conflict) => {
    if (resolutions[conflict.id] !== "custom") {
      return false
    }
    const value = customValues[conflict.id]?.trim()
    return !value
  })

  const isApplyDisabled = conflictCount === 0 || customValueMissing

  const handleApply = () => {
    if (isApplyDisabled) {
      return
    }
    const payload = { ...resolutions }
    Object.entries(customValues).forEach(([conflictId, value]) => {
      if (resolutions[conflictId] === "custom" && value) {
        payload[conflictId] = value.trim()
      }
    })
    onResolve?.(payload)
  }

  return (
    <Box borderWidth="1px" borderRadius="lg" p={4}>
      <VStack align="stretch" gap={4}>
        <Box>
          <Heading size="md">Merge Conflict Resolution</Heading>
          <Text color="fg.muted">
            Resolve {conflictCount} conflict{conflictCount === 1 ? "" : "s"}{" "}
            before merging.
          </Text>
          <Text fontSize="sm" mt={2}>
            Branch choices: {summary.branch} • Main choices: {summary.base} •
            Custom: {summary.custom}
          </Text>
        </Box>

        <Box borderBottomWidth="1px" />

        <VStack gap={4} align="stretch">
          {conflicts.map((conflict) => {
            const selectId = `resolution-${conflict.id}`
            const currentResolution = resolutions[conflict.id] ?? "branch"
            return (
              <Box
                key={conflict.id}
                borderWidth="1px"
                borderRadius="md"
                p={3}
                data-testid={`conflict-${conflict.id}`}
              >
                <Flex
                  direction={{ base: "column", md: "row" }}
                  justify="space-between"
                  gap={3}
                >
                  <Box>
                    <Text fontWeight="semibold">
                      {conflict.entityType} — {conflict.field}
                    </Text>
                    <Text fontSize="sm" color="fg.muted">
                      Branch: {conflict.branchValue} • Base:{" "}
                      {conflict.baseValue}
                    </Text>
                  </Box>
                  <Box minW={{ base: "100%", md: "250px" }}>
                    <label htmlFor={selectId}>
                      <Text fontSize="sm" mb={1}>
                        Resolution Strategy
                      </Text>
                    </label>
                    <NativeSelect.Root>
                      <NativeSelect.Field
                        id={selectId}
                        aria-label="Resolution Strategy"
                        value={currentResolution}
                        onChange={(event) =>
                          handleResolutionChange(
                            conflict.id,
                            event.target.value,
                          )
                        }
                      >
                        {resolutionOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </NativeSelect.Field>
                      <NativeSelect.Indicator />
                    </NativeSelect.Root>
                    {currentResolution === "custom" && (
                      <Box mt={2}>
                        <Input
                          placeholder="Enter custom value"
                          value={customValues[conflict.id] ?? ""}
                          onChange={(event) =>
                            handleCustomChange(conflict.id, event.target.value)
                          }
                          aria-invalid={!customValues[conflict.id]?.trim()}
                        />
                        {!customValues[conflict.id]?.trim() && (
                          <Text mt={1} fontSize="xs" color="fg.error">
                            Custom value is required for this conflict.
                          </Text>
                        )}
                      </Box>
                    )}
                  </Box>
                </Flex>
              </Box>
            )
          })}
        </VStack>

        <Flex justify="flex-end">
          <Button
            colorPalette="blue"
            onClick={handleApply}
            disabled={isApplyDisabled}
          >
            Apply Resolution
          </Button>
        </Flex>
      </VStack>
    </Box>
  )
}

export default MergeConflictResolution
