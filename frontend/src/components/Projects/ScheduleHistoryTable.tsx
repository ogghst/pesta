import {
  Box,
  HStack,
  Separator,
  Spinner,
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react"
import { format } from "date-fns"

import type { CostElementSchedulePublic } from "@/client"

// Extended type to include fields that exist in backend but are missing from generated types
type CostElementSchedulePublicExtended = CostElementSchedulePublic & {
  registration_date?: string | null
  description?: string | null
}

interface ScheduleHistoryTableProps {
  history: CostElementSchedulePublicExtended[]
  isLoading: boolean
}

const formatDate = (value: string | null | undefined) => {
  if (!value) {
    return "—"
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return format(parsed, "yyyy-MM-dd")
}

const ScheduleHistoryTable = ({
  history,
  isLoading,
}: ScheduleHistoryTableProps) => {
  if (isLoading) {
    return (
      <HStack gap={2}>
        <Spinner size="sm" />
        <Text fontSize="sm" color="fg.muted">
          Loading schedule history…
        </Text>
      </HStack>
    )
  }

  if (history.length === 0) {
    return (
      <Text fontSize="sm" color="fg.muted">
        No schedule registrations recorded yet.
      </Text>
    )
  }

  return (
    <VStack width="100%" alignItems="stretch" gap={3}>
      {history.map((entry, index) => (
        <Stack
          key={entry.schedule_id}
          data-testid="schedule-history-row"
          direction={{ base: "column", md: "row" }}
          justify="space-between"
          gap={3}
          padding={3}
          borderWidth="1px"
          borderRadius="md"
          bg={index === 0 ? "bg.muted" : "bg.canvas"}
        >
          <Box>
            <Text fontSize="xs" textTransform="uppercase" color="fg.muted">
              Registration Date
            </Text>
            <Text fontWeight="medium">
              {formatDate(entry.registration_date ?? undefined)}
            </Text>
          </Box>
          <Separator display={{ base: "block", md: "none" }} />
          <Box flex="1">
            <Text fontSize="xs" textTransform="uppercase" color="fg.muted">
              Description
            </Text>
            <Text>{entry.description?.trim() || "—"}</Text>
          </Box>
          <Separator display={{ base: "block", md: "none" }} />
          <Box>
            <Text fontSize="xs" textTransform="uppercase" color="fg.muted">
              Start → End
            </Text>
            <Text>
              {formatDate(entry.start_date)} → {formatDate(entry.end_date)}
            </Text>
          </Box>
          <Separator display={{ base: "block", md: "none" }} />
          <Box>
            <Text fontSize="xs" textTransform="uppercase" color="fg.muted">
              Progression
            </Text>
            <Text>{entry.progression_type}</Text>
          </Box>
        </Stack>
      ))}
    </VStack>
  )
}

export default ScheduleHistoryTable
