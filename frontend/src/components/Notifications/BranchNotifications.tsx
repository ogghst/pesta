import {
  Alert,
  Badge,
  Box,
  Button,
  Heading,
  HStack,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"

type BranchNotificationItem = {
  notification_id: string
  branch: string
  event_type: string
  message: string
  recipients: string[]
  context?: Record<string, unknown>
  created_at: string
}

interface BranchNotificationsResponse {
  data: BranchNotificationItem[]
  count: number
}

interface BranchNotificationsProps {
  projectId: string
  limit?: number
}

const BranchNotifications = ({
  projectId,
  limit = 10,
}: BranchNotificationsProps) => {
  const { data, isLoading, isError, refetch, isFetching } =
    useQuery<BranchNotificationsResponse>({
      queryKey: ["branch-notifications", projectId, limit],
      queryFn: async () => {
        const response = await fetch(
          `/api/v1/projects/${projectId}/notifications?limit=${limit}`,
        )
        if (!response.ok) {
          throw new Error("Failed to load branch notifications")
        }
        return response.json()
      },
      enabled: Boolean(projectId),
    })

  if (isLoading) {
    return (
      <Box p={4}>
        <HStack gap={3}>
          <Spinner />
          <Text>Loading branch notifications…</Text>
        </HStack>
      </Box>
    )
  }

  if (isError || !data) {
    return (
      <Alert.Root status="error" borderRadius="md">
        <Alert.Title>Unable to load notifications</Alert.Title>
        <Alert.Description>
          Please try again. If the issue persists contact an administrator.
        </Alert.Description>
        <Button
          mt={3}
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          Retry
        </Button>
      </Alert.Root>
    )
  }

  if (data.data.length === 0) {
    return (
      <Box borderWidth="1px" borderRadius="lg" p={4}>
        <Heading size="sm" mb={1}>
          Branch Notifications
        </Heading>
        <Text color="fg.muted">No branch notifications yet.</Text>
      </Box>
    )
  }

  return (
    <Box borderWidth="1px" borderRadius="lg" p={4}>
      <HStack justify="space-between" align="center" mb={3}>
        <Heading size="sm">Branch Notifications</Heading>
        <Button
          size="sm"
          variant="subtle"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          Refresh
        </Button>
      </HStack>
      <VStack align="stretch" gap={3}>
        {data.data.map((notification) => (
          <Box
            key={notification.notification_id}
            borderWidth="1px"
            borderRadius="md"
            p={3}
          >
            <HStack justify="space-between">
              <Text fontWeight="semibold">{notification.message}</Text>
              <Badge colorPalette="blue" textTransform="capitalize">
                {notification.event_type.replace(/_/g, " ")}
              </Badge>
            </HStack>
            <Text color="fg.muted" fontSize="sm">
              Branch {notification.branch} •{" "}
              {new Date(notification.created_at).toLocaleString()}
            </Text>
            {notification.recipients.length > 0 && (
              <Text fontSize="sm" mt={1}>
                Notified: {notification.recipients.join(", ")}
              </Text>
            )}
            {notification.context &&
              Object.keys(notification.context).length > 0 && (
                <Text fontSize="sm" color="fg.muted" mt={1}>
                  Details:{" "}
                  {Object.entries(notification.context)
                    .map(([key, value]) => `${key}: ${value}`)
                    .join(", ")}
                </Text>
              )}
          </Box>
        ))}
      </VStack>
    </Box>
  )
}

export default BranchNotifications
