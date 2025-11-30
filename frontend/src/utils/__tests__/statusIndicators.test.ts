/**
 * Tests for status indicator utilities
 *
 * These tests verify that status indicator functions correctly
 * categorize performance metrics and return appropriate visual indicators.
 */

import { describe, expect, it } from "vitest"
import {
  getCpiStatus,
  getCvStatus,
  getSpiStatus,
  getSvStatus,
  getTcpiStatus,
  getVarianceStatus,
} from "../statusIndicators"

describe("statusIndicators utilities", () => {
  describe("getCpiStatus", () => {
    it("should return 'Over Budget' status for CPI < 0.95", () => {
      const status = getCpiStatus("0.90")
      expect(status.label).toBe("Over Budget")
      expect(status.color).toBe("red.500")
    })

    it("should return 'On Target' status for 0.95 <= CPI < 1.0", () => {
      const status = getCpiStatus("0.98")
      expect(status.label).toBe("On Target")
      expect(status.color).toBe("yellow.500")
    })

    it("should return 'Under Budget' status for CPI >= 1.0", () => {
      const status = getCpiStatus("1.05")
      expect(status.label).toBe("Under Budget")
      expect(status.color).toBe("green.500")
    })

    it("should return 'N/A' status for null value", () => {
      const status = getCpiStatus(null)
      expect(status.label).toBe("N/A")
      expect(status.color).toBe("gray.500")
    })

    it("should return 'N/A' status for undefined value", () => {
      const status = getCpiStatus(undefined)
      expect(status.label).toBe("N/A")
      expect(status.color).toBe("gray.500")
    })
  })

  describe("getSpiStatus", () => {
    it("should return 'Behind Schedule' status for SPI < 0.95", () => {
      const status = getSpiStatus("0.90")
      expect(status.label).toBe("Behind Schedule")
      expect(status.color).toBe("red.500")
    })

    it("should return 'On Schedule' status for 0.95 <= SPI < 1.0", () => {
      const status = getSpiStatus("0.98")
      expect(status.label).toBe("On Schedule")
      expect(status.color).toBe("yellow.500")
    })

    it("should return 'Ahead of Schedule' status for SPI >= 1.0", () => {
      const status = getSpiStatus("1.05")
      expect(status.label).toBe("Ahead of Schedule")
      expect(status.color).toBe("green.500")
    })

    it("should return 'N/A' status for null value", () => {
      const status = getSpiStatus(null)
      expect(status.label).toBe("N/A")
      expect(status.color).toBe("gray.500")
    })
  })

  describe("getTcpiStatus", () => {
    it("should return 'Overrun' status for 'overrun' value", () => {
      const status = getTcpiStatus("overrun")
      expect(status.label).toBe("Overrun")
      expect(status.color).toBe("red.500")
    })

    it("should return 'On Track' status for TCPI <= 1.0", () => {
      const status = getTcpiStatus("0.95")
      expect(status.label).toBe("On Track")
      expect(status.color).toBe("green.500")
    })

    it("should return 'At Risk' status for 1.0 < TCPI <= 1.1", () => {
      const status = getTcpiStatus("1.05")
      expect(status.label).toBe("At Risk")
      expect(status.color).toBe("yellow.500")
    })

    it("should return 'Over Target' status for TCPI > 1.1", () => {
      const status = getTcpiStatus("1.15")
      expect(status.label).toBe("Over Target")
      expect(status.color).toBe("red.500")
    })

    it("should return 'N/A' status for null value", () => {
      const status = getTcpiStatus(null)
      expect(status.label).toBe("N/A")
      expect(status.color).toBe("gray.500")
    })
  })

  describe("getCvStatus", () => {
    it("should return 'Over Budget' status for negative variance", () => {
      const status = getCvStatus("-1000")
      expect(status.label).toBe("Over Budget")
      expect(status.color).toBe("red.500")
    })

    it("should return 'On Budget' status for zero variance", () => {
      const status = getCvStatus("0")
      expect(status.label).toBe("On Budget")
      expect(status.color).toBe("yellow.500")
    })

    it("should return 'Under Budget' status for positive variance", () => {
      const status = getCvStatus("1000")
      expect(status.label).toBe("Under Budget")
      expect(status.color).toBe("green.500")
    })

    it("should return 'N/A' status for null value", () => {
      const status = getCvStatus(null)
      expect(status.label).toBe("N/A")
      expect(status.color).toBe("gray.500")
    })

    it("should handle number input", () => {
      const status = getCvStatus(-500)
      expect(status.label).toBe("Over Budget")
      expect(status.color).toBe("red.500")
    })
  })

  describe("getSvStatus", () => {
    it("should return 'Behind Schedule' status for negative variance", () => {
      const status = getSvStatus("-1000")
      expect(status.label).toBe("Behind Schedule")
      expect(status.color).toBe("red.500")
    })

    it("should return 'On Schedule' status for zero variance", () => {
      const status = getSvStatus("0")
      expect(status.label).toBe("On Schedule")
      expect(status.color).toBe("yellow.500")
    })

    it("should return 'Ahead of Schedule' status for positive variance", () => {
      const status = getSvStatus("1000")
      expect(status.label).toBe("Ahead of Schedule")
      expect(status.color).toBe("green.500")
    })

    it("should return 'N/A' status for null value", () => {
      const status = getSvStatus(null)
      expect(status.label).toBe("N/A")
      expect(status.color).toBe("gray.500")
    })
  })

  describe("getVarianceStatus", () => {
    it("should use CV status logic", () => {
      const status = getVarianceStatus("-1000")
      expect(status.label).toBe("Over Budget")
      expect(status.color).toBe("red.500")
    })
  })
})
