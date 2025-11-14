import { Flex } from "@chakra-ui/react"
import type {
  BaselineCostElementWithCostElementPublic,
  EarnedValueEntryPublic,
} from "@/client"
import type { ColumnDefExtended } from "@/components/DataTable/types"
import DeleteEarnedValueEntry from "@/components/Projects/DeleteEarnedValueEntry"
import EditEarnedValueEntry from "@/components/Projects/EditEarnedValueEntry"

export const formatDate = (value: string | undefined) =>
  value ? new Date(value).toLocaleDateString() : "N/A"

export const formatPercent = (value: string | number | undefined) => {
  const numeric = typeof value === "string" ? parseFloat(value) : Number(value)
  if (Number.isNaN(numeric)) {
    return "0.00%"
  }
  return `${numeric.toFixed(2)}%`
}

export const formatCurrency = (value: string | number | undefined | null) => {
  if (value === null || value === undefined) {
    return "€0.00"
  }
  const numeric = typeof value === "string" ? parseFloat(value) : Number(value)
  if (Number.isNaN(numeric)) {
    return "€0.00"
  }
  return `€${numeric.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

export function buildEarnedValueColumns(
  costElementId: string,
  budgetBac?: string | number | null,
): ColumnDefExtended<EarnedValueEntryPublic>[] {
  void costElementId
  return [
    {
      accessorKey: "completion_date",
      header: "Completion Date",
      enableSorting: true,
      enableResizing: true,
      size: 140,
      defaultVisible: true,
      cell: ({ getValue }) => formatDate(getValue() as string),
    },
    {
      accessorKey: "percent_complete",
      header: "Percent Complete",
      enableSorting: true,
      enableResizing: true,
      size: 140,
      defaultVisible: true,
      cell: ({ getValue }) => formatPercent(getValue() as string | number),
    },
    {
      accessorKey: "earned_value",
      header: "Earned Value",
      enableSorting: true,
      enableResizing: true,
      size: 140,
      defaultVisible: true,
      cell: ({ getValue }) =>
        formatCurrency(getValue() as string | number | null),
    },
    {
      accessorKey: "deliverables",
      header: "Deliverables",
      enableSorting: true,
      enableResizing: true,
      size: 220,
      defaultVisible: true,
      cell: ({ getValue }) => (getValue() as string) ?? "—",
    },
    {
      accessorKey: "description",
      header: "Description",
      enableSorting: true,
      enableResizing: true,
      size: 220,
      defaultVisible: true,
      cell: ({ getValue }) => (getValue() as string) ?? "—",
    },
    {
      id: "actions",
      header: "Actions",
      enableSorting: false,
      enableResizing: false,
      enableColumnFilter: false,
      size: 160,
      defaultVisible: true,
      cell: ({ row }) => (
        <Flex gap={2}>
          <EditEarnedValueEntry
            earnedValueEntry={row.original}
            budgetBac={budgetBac}
          />
          <DeleteEarnedValueEntry
            earnedValueId={row.original.earned_value_id}
            description={row.original.deliverables ?? "Earned value entry"}
          />
        </Flex>
      ),
    },
  ]
}

export function buildBaselineEarnedValueColumns(): ColumnDefExtended<BaselineCostElementWithCostElementPublic>[] {
  const formatText = (value: string | null | undefined) => (value ? value : "—")

  return [
    {
      accessorKey: "department_name",
      header: "Department",
      enableSorting: true,
      enableResizing: true,
      size: 200,
      defaultVisible: true,
      cell: ({ getValue }) => formatText(getValue() as string | null),
    },
    {
      accessorKey: "department_code",
      header: "Code",
      enableSorting: true,
      enableResizing: true,
      size: 120,
      defaultVisible: true,
      cell: ({ getValue }) => formatText(getValue() as string | null),
    },
    {
      accessorKey: "percent_complete",
      header: "Percent Complete",
      enableSorting: true,
      enableResizing: true,
      size: 140,
      defaultVisible: true,
      cell: ({ getValue }) => {
        const value = getValue() as string | number | null
        if (value === null || value === undefined) {
          return "—"
        }
        const numeric =
          typeof value === "string" ? parseFloat(value) : Number(value)
        if (Number.isNaN(numeric)) {
          return "—"
        }
        return `${numeric.toFixed(2)}%`
      },
    },
    {
      accessorKey: "earned_ev",
      header: "Earned Value",
      enableSorting: true,
      enableResizing: true,
      size: 140,
      defaultVisible: true,
      cell: ({ getValue }) =>
        formatCurrency(getValue() as string | number | null),
    },
    {
      accessorKey: "actual_ac",
      header: "Actual Cost",
      enableSorting: true,
      enableResizing: true,
      size: 140,
      defaultVisible: true,
      cell: ({ getValue }) =>
        formatCurrency(getValue() as string | number | null),
    },
    {
      accessorKey: "budget_bac",
      header: "Budget (BAC)",
      enableSorting: true,
      enableResizing: true,
      size: 140,
      defaultVisible: true,
      cell: ({ getValue }) =>
        formatCurrency(getValue() as string | number | null),
    },
    {
      accessorKey: "wbe_machine_type",
      header: "WBE",
      enableSorting: true,
      enableResizing: true,
      size: 200,
      defaultVisible: true,
      cell: ({ getValue }) => formatText(getValue() as string | null),
    },
  ]
}
