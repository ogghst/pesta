import {
  Alert,
  Box,
  Button,
  Flex,
  Heading,
  Input,
  SimpleGrid,
  Text,
  Textarea,
  VStack,
} from "@chakra-ui/react"
import { useEffect, useMemo, useState } from "react"

type BranchTemplate = {
  id: string
  name: string
  description: string
  branchPrefix: string
}

interface BranchTemplatesProps {
  projectId: string
  onApplyTemplate?: (template: BranchTemplate) => void
}

const NAME_PATTERN = /^[A-Za-z][A-Za-z0-9\s-_]{2,30}$/

const BranchTemplates = ({
  projectId,
  onApplyTemplate,
}: BranchTemplatesProps) => {
  const storageKey = `branch-templates-${projectId}`
  const [templates, setTemplates] = useState<BranchTemplate[]>([])
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [formValues, setFormValues] = useState({
    name: "",
    description: "",
    branchPrefix: "",
  })

  useEffect(() => {
    try {
      const stored = localStorage.getItem(storageKey)
      const parsed = stored ? (JSON.parse(stored) as BranchTemplate[]) : []
      setTemplates(parsed)
    } catch (error) {
      console.warn("Failed to load branch templates", error)
    }
  }, [storageKey])

  const nameError = useMemo(() => {
    if (!formValues.name) {
      return null
    }
    if (!NAME_PATTERN.test(formValues.name)) {
      return "Use letters and numbers only (3-30 characters)."
    }
    return null
  }, [formValues.name])

  const prefixError = useMemo(() => {
    if (!formValues.branchPrefix) {
      return null
    }
    if (!/^[a-z0-9-]+$/i.test(formValues.branchPrefix)) {
      return "Prefix can include letters, numbers, and hyphens."
    }
    return null
  }, [formValues.branchPrefix])

  const canAddTemplate =
    formValues.name.trim().length > 0 &&
    formValues.description.trim().length > 0 &&
    formValues.branchPrefix.trim().length > 0 &&
    !nameError &&
    !prefixError

  const persistTemplates = (next: BranchTemplate[]) => {
    setTemplates(next)
    try {
      localStorage.setItem(storageKey, JSON.stringify(next))
    } catch (error) {
      console.warn("Failed to save branch templates", error)
    }
  }

  const handleAddTemplate = () => {
    if (!canAddTemplate) {
      return
    }
    const newTemplate: BranchTemplate = {
      id: crypto.randomUUID(),
      name: formValues.name.trim(),
      description: formValues.description.trim(),
      branchPrefix: formValues.branchPrefix.trim(),
    }
    const next = [...templates, newTemplate]
    persistTemplates(next)
    setFormValues({ name: "", description: "", branchPrefix: "" })
    setStatusMessage("Template added.")
  }

  const handleApply = (template: BranchTemplate) => {
    setStatusMessage(`Applied template "${template.name}".`)
    onApplyTemplate?.(template)
  }

  return (
    <VStack align="stretch" gap={6}>
      <Box borderWidth="1px" borderRadius="lg" p={4}>
        <Heading size="md" mb={3}>
          Create Branch Template
        </Heading>
        <SimpleGrid columns={{ base: 1, md: 3 }} gap={3}>
          <Box>
            <Text fontWeight="semibold">Template Name</Text>
            <Input
              aria-label="Template Name"
              placeholder="e.g., Feature"
              value={formValues.name}
              onChange={(event) =>
                setFormValues((prev) => ({ ...prev, name: event.target.value }))
              }
              onBlur={() => setStatusMessage(null)}
              data-invalid={Boolean(nameError) || undefined}
            />
            {nameError && (
              <Text mt={1} fontSize="xs" color="fg.error">
                {nameError}
              </Text>
            )}
          </Box>
          <Box>
            <Text fontWeight="semibold">Description</Text>
            <Textarea
              aria-label="Description"
              placeholder="Explain how this template should be used"
              value={formValues.description}
              onChange={(event) =>
                setFormValues((prev) => ({
                  ...prev,
                  description: event.target.value,
                }))
              }
            />
          </Box>
          <Box>
            <Text fontWeight="semibold">Branch Prefix</Text>
            <Input
              aria-label="Branch Prefix"
              placeholder="e.g., feat-"
              value={formValues.branchPrefix}
              onChange={(event) =>
                setFormValues((prev) => ({
                  ...prev,
                  branchPrefix: event.target.value,
                }))
              }
              data-invalid={Boolean(prefixError) || undefined}
            />
            {prefixError && (
              <Text mt={1} fontSize="xs" color="fg.error">
                {prefixError}
              </Text>
            )}
          </Box>
        </SimpleGrid>
        <Flex justify="flex-end" mt={4}>
          <Button
            colorPalette="blue"
            onClick={handleAddTemplate}
            disabled={!canAddTemplate}
          >
            Add Template
          </Button>
        </Flex>
      </Box>

      <Box borderWidth="1px" borderRadius="lg" p={4}>
        <Heading size="md" mb={3}>
          Saved Templates
        </Heading>
        {templates.length === 0 ? (
          <Text color="fg.muted">
            No templates yet. Create one to speed up branch setup.
          </Text>
        ) : (
          <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
            {templates.map((template) => (
              <Box key={template.id} borderWidth="1px" borderRadius="md" p={3}>
                <Text fontWeight="semibold">{template.name}</Text>
                <Text fontSize="sm" color="fg.muted">
                  {template.description}
                </Text>
                <Text fontSize="sm" mt={2}>
                  Prefix: <strong>{template.branchPrefix}</strong>
                </Text>
                <Flex justify="flex-end" mt={3}>
                  <Button size="sm" onClick={() => handleApply(template)}>
                    Apply {template.name}
                  </Button>
                </Flex>
              </Box>
            ))}
          </SimpleGrid>
        )}
      </Box>

      {statusMessage && (
        <Alert.Root status="success" borderRadius="md">
          <Alert.Title>Templates</Alert.Title>
          <Alert.Description>{statusMessage}</Alert.Description>
        </Alert.Root>
      )}
    </VStack>
  )
}

export default BranchTemplates
