import { RadioGroup, Stack } from "@chakra-ui/react"
import { useBranch } from "@/context/BranchContext"

export function ViewModeToggle() {
  const { viewMode, setViewMode, currentBranch } = useBranch()

  // Hide toggle when viewing main branch (merged view is always used)
  if (currentBranch === "main") {
    return null
  }

  return (
    <RadioGroup.Root
      value={viewMode}
      onValueChange={(details) =>
        setViewMode(details.value as "merged" | "branch-only")
      }
      size="sm"
    >
      <Stack direction="row" gap={4}>
        <RadioGroup.Item value="merged">
          <RadioGroup.ItemHiddenInput />
          <RadioGroup.ItemIndicator />
          <RadioGroup.ItemText>Merged View</RadioGroup.ItemText>
        </RadioGroup.Item>
        <RadioGroup.Item value="branch-only">
          <RadioGroup.ItemHiddenInput />
          <RadioGroup.ItemIndicator />
          <RadioGroup.ItemText>Branch Only</RadioGroup.ItemText>
        </RadioGroup.Item>
      </Stack>
    </RadioGroup.Root>
  )
}
