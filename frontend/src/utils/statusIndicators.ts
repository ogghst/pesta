/**
 * Status indicator utilities for EVM performance metrics
 *
 * These functions categorize performance metrics and return appropriate
 * visual indicators (color, icon, label) for display in the UI.
 */

import {
  FiAlertCircle,
  FiMinus,
  FiTrendingDown,
  FiTrendingUp,
} from "react-icons/fi"

export type StatusIndicator = {
  color: string
  icon: typeof FiTrendingUp
  label: string
}

/**
 * Get status indicator for Cost Performance Index (CPI)
 *
 * @param cpi - CPI value as string, null, or undefined
 * @returns Status indicator with color, icon, and label
 */
export function getCpiStatus(cpi: string | null | undefined): StatusIndicator {
  if (cpi === null || cpi === undefined) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  const numValue = Number(cpi)
  if (Number.isNaN(numValue)) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  if (numValue < 0.95) {
    return {
      color: "red.500",
      icon: FiTrendingDown,
      label: "Over Budget",
    }
  }
  if (numValue < 1.0) {
    return {
      color: "yellow.500",
      icon: FiMinus,
      label: "On Target",
    }
  }
  return {
    color: "green.500",
    icon: FiTrendingUp,
    label: "Under Budget",
  }
}

/**
 * Get status indicator for Schedule Performance Index (SPI)
 *
 * @param spi - SPI value as string, null, or undefined
 * @returns Status indicator with color, icon, and label
 */
export function getSpiStatus(spi: string | null | undefined): StatusIndicator {
  if (spi === null || spi === undefined) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  const numValue = Number(spi)
  if (Number.isNaN(numValue)) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  if (numValue < 0.95) {
    return {
      color: "red.500",
      icon: FiTrendingDown,
      label: "Behind Schedule",
    }
  }
  if (numValue < 1.0) {
    return {
      color: "yellow.500",
      icon: FiMinus,
      label: "On Schedule",
    }
  }
  return {
    color: "green.500",
    icon: FiTrendingUp,
    label: "Ahead of Schedule",
  }
}

/**
 * Get status indicator for To-Complete Performance Index (TCPI)
 *
 * @param tcpi - TCPI value as string, "overrun", null, or undefined
 * @returns Status indicator with color, icon, and label
 */
export function getTcpiStatus(
  tcpi: string | null | undefined,
): StatusIndicator {
  if (tcpi === null || tcpi === undefined) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  if (tcpi === "overrun") {
    return {
      color: "red.500",
      icon: FiAlertCircle,
      label: "Overrun",
    }
  }
  const numValue = Number(tcpi)
  if (Number.isNaN(numValue)) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  if (numValue <= 1.0) {
    return {
      color: "green.500",
      icon: FiTrendingUp,
      label: "On Track",
    }
  }
  if (numValue <= 1.1) {
    return {
      color: "yellow.500",
      icon: FiMinus,
      label: "At Risk",
    }
  }
  return {
    color: "red.500",
    icon: FiTrendingDown,
    label: "Over Target",
  }
}

/**
 * Get status indicator for Cost Variance (CV)
 *
 * @param cv - Cost variance value as string, number, null, or undefined
 * @returns Status indicator with color, icon, and label
 */
export function getCvStatus(
  cv: string | number | null | undefined,
): StatusIndicator {
  if (cv === null || cv === undefined) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  const numValue = typeof cv === "string" ? Number(cv) : cv
  if (Number.isNaN(numValue)) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  if (numValue < 0) {
    return {
      color: "red.500",
      icon: FiTrendingDown,
      label: "Over Budget",
    }
  }
  if (numValue === 0) {
    return {
      color: "yellow.500",
      icon: FiMinus,
      label: "On Budget",
    }
  }
  return {
    color: "green.500",
    icon: FiTrendingUp,
    label: "Under Budget",
  }
}

/**
 * Get status indicator for Schedule Variance (SV)
 *
 * @param sv - Schedule variance value as string, number, null, or undefined
 * @returns Status indicator with color, icon, and label
 */
export function getSvStatus(
  sv: string | number | null | undefined,
): StatusIndicator {
  if (sv === null || sv === undefined) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  const numValue = typeof sv === "string" ? Number(sv) : sv
  if (Number.isNaN(numValue)) {
    return {
      color: "gray.500",
      icon: FiMinus,
      label: "N/A",
    }
  }
  if (numValue < 0) {
    return {
      color: "red.500",
      icon: FiTrendingDown,
      label: "Behind Schedule",
    }
  }
  if (numValue === 0) {
    return {
      color: "yellow.500",
      icon: FiMinus,
      label: "On Schedule",
    }
  }
  return {
    color: "green.500",
    icon: FiTrendingUp,
    label: "Ahead of Schedule",
  }
}

/**
 * Get status indicator for variance (cost or schedule) - generic version
 *
 * @param variance - Variance value as string, number, null, or undefined
 * @returns Status indicator with color, icon, and label
 */
export function getVarianceStatus(
  variance: string | number | null | undefined,
): StatusIndicator {
  // Use CV status logic as default (can be used for generic variance)
  return getCvStatus(variance)
}
