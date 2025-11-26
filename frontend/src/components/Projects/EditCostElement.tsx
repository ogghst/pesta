import {
  Button,
  DialogActionTrigger,
  DialogTitle,
  Input,
  Text,
  Textarea,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import {
  Controller,
  type FieldValues,
  type SubmitHandler,
  useForm,
} from "react-hook-form"
import { FaExchangeAlt } from "react-icons/fa"
import {
  type ApiError,
  type CostElementPublic,
  CostElementsService,
  type CostElementUpdate,
} from "@/client"
import { useBranch } from "@/context/BranchContext"
import { useRevenuePlanValidation } from "@/hooks/useRevenuePlanValidation"
import { handleError } from "@/utils"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTrigger,
} from "../ui/dialog"
import { Field } from "../ui/field"

interface EditCostElementProps {
  costElement: CostElementPublic
}

type CostElementUpdateFormValues = CostElementUpdate & FieldValues

const EditCostElement = ({ costElement }: EditCostElementProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { currentBranch } = useBranch()

  const {
    control,
    register,
    handleSubmit,
    reset,
    watch,
    setError,
    clearErrors,
    formState: { errors, isValid, isSubmitting },
  } = useForm<CostElementUpdateFormValues>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      department_code: costElement.department_code,
      department_name: costElement.department_name,
      budget_bac: costElement.budget_bac,
      revenue_plan: costElement.revenue_plan,
      business_status: costElement.business_status ?? "planned",
      notes: costElement.notes,
    },
  })

  // Watch revenue_plan for real-time validation
  const revenuePlanValue = watch("revenue_plan")

  // Validate revenue_plan against WBE limit
  const revenueValidation = useRevenuePlanValidation(
    costElement.wbe_id,
    costElement.cost_element_id,
    revenuePlanValue !== undefined ? Number(revenuePlanValue) : undefined,
  )

  // Update form error state based on validation (using useEffect to avoid infinite loops)
  useEffect(() => {
    if (revenueValidation.errorMessage && revenuePlanValue !== undefined) {
      setError("revenue_plan", {
        type: "manual",
        message: revenueValidation.errorMessage,
      })
    } else if (
      !revenueValidation.errorMessage &&
      errors.revenue_plan?.type === "manual"
    ) {
      clearErrors("revenue_plan")
    }
  }, [
    revenueValidation.errorMessage,
    revenuePlanValue,
    setError,
    clearErrors,
    errors.revenue_plan?.type,
  ])

  // Form is valid only if React Hook Form validation passes AND revenue validation passes
  const isFormValid = isValid && revenueValidation.isValid

  const mutation = useMutation({
    mutationFn: (data: CostElementUpdate) =>
      CostElementsService.updateCostElement({
        id: costElement.cost_element_id,
        requestBody: data,
        branch: currentBranch || costElement.branch || "main",
      }),
    onSuccess: () => {
      // Don't show toast here - will show after both operations complete
      reset()
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["cost-elements"] })
      queryClient.invalidateQueries({
        queryKey: ["cost-elements", costElement.cost_element_id],
      })
      queryClient.invalidateQueries({ queryKey: ["cost-summary"] })
    },
  })

  const onSubmit: SubmitHandler<CostElementUpdateFormValues> = async (data) => {
    await mutation.mutateAsync(data)
  }

  return (
    <DialogRoot
      size={{ base: "xs", md: "xl" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          aria-label="Edit cost element"
          title="Edit cost element"
        >
          <FaExchangeAlt fontSize="16px" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Edit Cost Element</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Update the cost element details below.</Text>
            <VStack gap={4}>
              <Field
                required
                invalid={!!errors.department_code}
                errorText={errors.department_code?.message}
                label="Department Code"
              >
                <Input
                  {...register("department_code", {
                    required: "Department code is required",
                  })}
                  placeholder="Department Code"
                  type="text"
                />
              </Field>

              <Field
                required
                invalid={!!errors.department_name}
                errorText={errors.department_name?.message}
                label="Department Name"
              >
                <Input
                  {...register("department_name", {
                    required: "Department name is required",
                  })}
                  placeholder="Department Name"
                  type="text"
                />
              </Field>

              <Field
                invalid={!!errors.budget_bac}
                errorText={errors.budget_bac?.message}
                label="Budget (BAC)"
              >
                <Input
                  {...register("budget_bac", {
                    min: {
                      value: 0,
                      message: "Budget must be positive",
                    },
                  })}
                  placeholder="0.00"
                  type="number"
                  step="0.01"
                />
              </Field>

              <Field
                invalid={!!errors.revenue_plan || !revenueValidation.isValid}
                errorText={
                  errors.revenue_plan?.message || revenueValidation.errorMessage
                }
                label="Revenue Plan"
              >
                <Input
                  {...register("revenue_plan", {
                    min: {
                      value: 0,
                      message: "Revenue plan must be positive",
                    },
                  })}
                  placeholder="0.00"
                  type="number"
                  step="0.01"
                />
                {revenuePlanValue !== undefined &&
                  revenueValidation.limit > 0 && (
                    <Text fontSize="xs" color="gray.600" mt={1}>
                      Total: €
                      {revenueValidation.currentTotal.toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}{" "}
                      / Limit: €
                      {revenueValidation.limit.toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}{" "}
                      ({revenueValidation.remaining >= 0 ? "+" : ""}€
                      {revenueValidation.remaining.toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}{" "}
                      remaining)
                    </Text>
                  )}
              </Field>

              <Field
                invalid={!!errors.business_status}
                errorText={errors.business_status?.message}
                label="Business Status"
              >
                <Controller
                  control={control}
                  name="business_status"
                  render={({ field }) => (
                    <select
                      {...field}
                      value={field.value ?? ""}
                      style={{
                        width: "100%",
                        padding: "8px",
                        borderRadius: "4px",
                        border: "1px solid #e2e8f0",
                      }}
                    >
                      <option value="planned">Planned</option>
                      <option value="active">Active</option>
                      <option value="on-hold">On Hold</option>
                      <option value="completed">Completed</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                  )}
                />
              </Field>

              <Field
                invalid={!!errors.notes}
                errorText={errors.notes?.message}
                label="Notes"
              >
                <Textarea {...register("notes")} placeholder="Notes" rows={3} />
              </Field>
            </VStack>
          </DialogBody>

          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button
                variant="subtle"
                colorPalette="gray"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            </DialogActionTrigger>
            <Button
              variant="solid"
              type="submit"
              disabled={!isFormValid || isSubmitting}
              loading={isSubmitting}
            >
              Save
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default EditCostElement
