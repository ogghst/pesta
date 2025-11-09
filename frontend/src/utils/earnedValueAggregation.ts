import type { EarnedValueEntryPublic } from "@/client"
import { generateTimeSeries } from "@/utils/timeSeriesGenerator"

export interface EarnedValueTimelinePoint {
  date: Date
  cumulativeEarnedValue: number
}

function toDateKey(date: Date): string {
  return date.toISOString().slice(0, 10)
}

export function buildEarnedValueTimeline({
  entries,
  startDate,
  endDate,
}: {
  entries: EarnedValueEntryPublic[]
  startDate?: Date
  endDate?: Date
}): EarnedValueTimelinePoint[] {
  if (!entries || entries.length === 0) {
    return []
  }

  const valuesByDate = new Map<string, number>()

  for (const entry of entries) {
    const { completion_date: completionDate, earned_value: earnedValueRaw } =
      entry

    if (
      !completionDate ||
      earnedValueRaw === undefined ||
      earnedValueRaw === null
    ) {
      continue
    }

    const parsedDate = new Date(completionDate)
    if (Number.isNaN(parsedDate.getTime())) {
      continue
    }

    const earnedValue = Number(earnedValueRaw)
    if (Number.isNaN(earnedValue)) {
      continue
    }

    const key = toDateKey(parsedDate)
    valuesByDate.set(key, (valuesByDate.get(key) ?? 0) + earnedValue)
  }

  if (valuesByDate.size === 0) {
    return []
  }

  const sortedKeys = Array.from(valuesByDate.keys()).sort()

  const firstDate = startDate ?? new Date(sortedKeys[0])
  const lastDate = endDate ?? new Date(sortedKeys[sortedKeys.length - 1])

  if (Number.isNaN(firstDate.getTime()) || Number.isNaN(lastDate.getTime())) {
    return []
  }

  if (firstDate > lastDate) {
    return []
  }

  const dateSeries = generateTimeSeries(firstDate, lastDate, "daily")
  let cumulative = 0

  return dateSeries.map((date) => {
    const key = toDateKey(date)
    if (valuesByDate.has(key)) {
      cumulative += valuesByDate.get(key) ?? 0
    }
    return {
      date,
      cumulativeEarnedValue: cumulative,
    }
  })
}
