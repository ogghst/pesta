import {
  Alert,
  Button,
  DialogActionTrigger,
  DialogTitle,
  Input,
  Text,
  Textarea,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { Controller, type SubmitHandler, useForm } from "react-hook-form"
import { FaExchangeAlt } from "react-icons/fa"
import {
  CostCategoriesService,
  CostElementSchedulesService,
  type CostRegistrationPublic,
  CostRegistrationsService,
  type CostRegistrationUpdate,
} from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
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

interface EditCostRegistrationProps {
  costRegistration: CostRegistrationPublic
}

const EditCostRegistration = ({
  costRegistration,
}: EditCostRegistrationProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const [dateAlert, setDateAlert] = useState<string | null>(null)

  // Fetch cost categories for dropdown
  const { data: categoriesData } = useQuery({
    queryFn: () => CostCategoriesService.readCostCategories(),
    queryKey: ["cost-categories"],
  })

  const costCategories = categoriesData?.data || []

  // Fetch schedule for date boundary check
  const { data: scheduleData } = useQuery({
    queryKey: ["cost-element-schedule", costRegistration.cost_element_id],
    queryFn: async () => {
      try {
        return await CostElementSchedulesService.readScheduleByCostElement({
          costElementId: costRegistration.cost_element_id,
        })
      } catch (error) {
        // Handle 404 gracefully - schedule may not exist
        if (error instanceof ApiError && error.status === 404) {
          return null
        }
        throw error
      }
    },
    enabled: isOpen, // Only fetch when dialog is open
    retry: false,
  })

  const {
    control,
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isValid, isSubmitting },
  } = useForm<CostRegistrationUpdate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      registration_date: costRegistration.registration_date,
      amount: costRegistration.amount ? parseFloat(costRegistration.amount) : 0,
      cost_category: costRegistration.cost_category,
      invoice_number: costRegistration.invoice_number,
      description: costRegistration.description,
      is_quality_cost: costRegistration.is_quality_cost,
    },
  })

  // Watch registration_date for alert check
  const registrationDate = watch("registration_date")

  // Check date against schedule boundaries
  useEffect(() => {
    if (!registrationDate || !scheduleData) {
      setDateAlert(null)
      return
    }

    const date = new Date(registrationDate)
    const startDate = new Date(scheduleData.start_date)
    const endDate = new Date(scheduleData.end_date)

    if (date < startDate || date > endDate) {
      setDateAlert(
        `Warning: Registration date is outside the cost element schedule boundaries (${scheduleData.start_date} to ${scheduleData.end_date}).`,
      )
    } else {
      setDateAlert(null)
    }
  }, [registrationDate, scheduleData])

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (isOpen) {
      reset({
        registration_date: costRegistration.registration_date,
        amount: costRegistration.amount
          ? parseFloat(costRegistration.amount)
          : 0,
        cost_category: costRegistration.cost_category,
        invoice_number: costRegistration.invoice_number,
        description: costRegistration.description,
        is_quality_cost: costRegistration.is_quality_cost,
      })
      setDateAlert(null)
    }
  }, [isOpen, costRegistration, reset])

  const mutation = useMutation({
    mutationFn: (data: CostRegistrationUpdate) =>
      CostRegistrationsService.updateCostRegistration({
        id: costRegistration.cost_registration_id,
        requestBody: data,
      }),
    onSuccess: () => {
      showSuccessToast("Cost registration updated successfully.")
      setIsOpen(false)
      setDateAlert(null)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["cost-registrations"] })
    },
  })

  const onSubmit: SubmitHandler<CostRegistrationUpdate> = (data) => {
    mutation.mutate(data)
  }

  return (
    <DialogRoot
      size={{ base: "xs", md: "lg" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm">
          <FaExchangeAlt fontSize="16px" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Edit Cost Registration</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Update the cost registration information below.</Text>
            <VStack gap={4}>
              {dateAlert && (
                <Alert.Root status="warning" width="100%">
                  <Alert.Indicator />
                  <Alert.Title>{dateAlert}</Alert.Title>
                </Alert.Root>
              )}

              <Field
                invalid={!!errors.registration_date}
                errorText={errors.registration_date?.message}
                label="Registration Date"
              >
                <Input {...register("registration_date")} type="date" />
              </Field>

              <Field
                invalid={!!errors.amount}
                errorText={errors.amount?.message}
                label="Amount"
              >
                <Input
                  {...register("amount", {
                    min: {
                      value: 0.01,
                      message: "Amount must be greater than zero",
                    },
                  })}
                  placeholder="0.00"
                  type="number"
                  step="0.01"
                />
              </Field>

              <Field
                invalid={!!errors.cost_category}
                errorText={errors.cost_category?.message}
                label="Cost Category"
              >
                <Controller
                  control={control}
                  name="cost_category"
                  render={({ field }) => (
                    <select
                      {...field}
                      style={{
                        width: "100%",
                        padding: "8px",
                        borderRadius: "4px",
                        border: errors.cost_category
                          ? "1px solid #ef4444"
                          : "1px solid #e2e8f0",
                      }}
                    >
                      <option value="">Select cost category...</option>
                      {costCategories.map((category) => (
                        <option key={category.code} value={category.code}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  )}
                />
              </Field>

              <Field
                invalid={!!errors.invoice_number}
                errorText={errors.invoice_number?.message}
                label="Invoice Number"
              >
                <Input
                  {...register("invoice_number")}
                  placeholder="Invoice Number"
                  type="text"
                />
              </Field>

              <Field
                invalid={!!errors.description}
                errorText={errors.description?.message}
                label="Description"
              >
                <Textarea
                  {...register("description")}
                  placeholder="Description"
                  rows={3}
                />
              </Field>

              <Field
                invalid={!!errors.is_quality_cost}
                errorText={errors.is_quality_cost?.message}
                label="Quality Cost"
              >
                <Controller
                  control={control}
                  name="is_quality_cost"
                  render={({ field }) => (
                    <input
                      type="checkbox"
                      checked={field.value || false}
                      onChange={field.onChange}
                    />
                  )}
                />
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
              disabled={!isValid || isSubmitting}
              loading={isSubmitting}
            >
              Update
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default EditCostRegistration
