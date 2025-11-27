import { Badge } from "@chakra-ui/react"

type ChangeStatus = "created" | "updated" | "deleted" | "unchanged"

type ChangeStatusIndicatorProps = {
  changeStatus: ChangeStatus
}

export function ChangeStatusIndicator({
  changeStatus,
}: ChangeStatusIndicatorProps) {
  // Don't render anything for unchanged status
  if (changeStatus === "unchanged") {
    return null
  }

  const statusConfig = {
    created: {
      color: "green",
      label: "Created",
      symbol: "+",
    },
    updated: {
      color: "yellow",
      label: "Updated",
      symbol: "~",
    },
    deleted: {
      color: "red",
      label: "Deleted",
      symbol: "×",
    },
  }

  const config = statusConfig[changeStatus]

  return (
    <Badge
      colorScheme={config.color}
      aria-label={`${config.label} in branch`}
      display="flex"
      alignItems="center"
      gap={1}
      fontSize="xs"
    >
      <span aria-hidden="true">{config.symbol}</span>
      {config.label}
    </Badge>
  )
}
