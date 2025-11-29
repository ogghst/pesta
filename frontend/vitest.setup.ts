import { vi } from "vitest"
import "@testing-library/jest-dom/vitest"

// Suppress CSS parsing errors in jsdom (jsdom doesn't support modern CSS features like @layer)
// This error occurs when emotion/Chakra UI tries to inject CSS with @layer directive
const originalConsoleError = console.error

console.error = (...args: any[]) => {
  // Check all arguments for CSS parsing error messages
  const hasCssError = args.some((arg) => {
    if (typeof arg === "string") {
      return (
        arg.includes("Could not parse CSS stylesheet") ||
        arg.includes("stylesheets.js")
      )
    }
    if (arg instanceof Error) {
      return (
        arg.message.includes("Could not parse CSS stylesheet") ||
        arg.stack?.includes("stylesheets.js")
      )
    }
    if (typeof arg === "object" && arg !== null) {
      const message = (arg as any).message || String(arg)
      const stack = (arg as any).stack
      return (
        (typeof message === "string" &&
          message.includes("Could not parse CSS stylesheet")) ||
        (typeof stack === "string" && stack.includes("stylesheets.js"))
      )
    }
    return false
  })

  if (hasCssError) {
    return // Silently ignore CSS parsing errors
  }
  originalConsoleError.apply(console, args)
}

vi.mock("@/components/ui/toaster", () => {
  return {
    toaster: {
      create: () => {},
    },
    Toaster: () => null,
  }
})

// Mock next-themes matchMedia usage
vi.mock("next-themes", () => {
  let currentTheme: "light" | "dark" = "light"
  return {
    ThemeProvider: ({ children, forcedTheme, defaultTheme }: any) => {
      if (forcedTheme) currentTheme = forcedTheme
      else if (defaultTheme) currentTheme = defaultTheme
      return children
    },
    useTheme: () => ({
      resolvedTheme: currentTheme,
      setTheme: (t: "light" | "dark") => {
        currentTheme = t
      },
    }),
  }
})

// Mock UsersService for TimeMachineProvider
vi.mock("@/client", async (importOriginal) => {
  const actual = await importOriginal<any>()
  const today = new Date().toISOString().slice(0, 10)
  return {
    ...actual,
    UsersService: {
      ...(actual.UsersService ?? {}),
      readTimeMachinePreference: vi
        .fn()
        .mockResolvedValue({ time_machine_date: today }),
      updateTimeMachinePreference: vi
        .fn()
        .mockResolvedValue({ time_machine_date: today }),
    },
  }
})
