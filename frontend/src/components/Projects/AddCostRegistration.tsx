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
import { FaPlus } from "react-icons/fa"
import {
  CostCategoriesService,
  CostElementSchedulesService,
  type CostRegistrationCreate,
  CostRegistrationsService,
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

interface AddCostRegistrationProps {
  costElementId: string
}

const AddCostRegistration = ({ costElementId }: AddCostRegistrationProps) => {
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
    queryKey: ["cost-element-schedule", costElementId],
    queryFn: async () => {
      try {
        return await CostElementSchedulesService.readScheduleByCostElement({
          costElementId,
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
  } = useForm<CostRegistrationCreate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      cost_element_id: costElementId,
      registration_date: new Date().toISOString().split("T")[0],
      amount: 0,
      cost_category: "",
      description: "",
      invoice_number: null,
      is_quality_cost: false,
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

  const mutation = useMutation({
    mutationFn: (data: CostRegistrationCreate) =>
      CostRegistrationsService.createCostRegistration({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Cost registration created successfully.")
      reset()
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

  const onSubmit: SubmitHandler<CostRegistrationCreate> = (data) => {
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
        <Button value="add-cost-registration" my={4}>
          <FaPlus fontSize="16px" />
          Add Cost Registration
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Add Cost Registration</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>
              Fill in the form below to create a new cost registration.
            </Text>
            <VStack gap={4}>
              {dateAlert && (
                <Alert.Root status="warning" width="100%">
                  <Alert.Indicator />
                  <Alert.Title>{dateAlert}</Alert.Title>
                </Alert.Root>
              )}

              <Field
                required
                invalid={!!errors.registration_date}
                errorText={errors.registration_date?.message}
                label="Registration Date"
              >
                <Input
                  {...register("registration_date", {
                    required: "Registration date is required",
                  })}
                  type="date"
                />
              </Field>

              <Field
                required
                invalid={!!errors.amount}
                errorText={errors.amount?.message}
                label="Amount"
              >
                <Input
                  {...register("amount", {
                    required: "Amount is required",
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
                required
                invalid={!!errors.cost_category}
                errorText={errors.cost_category?.message}
                label="Cost Category"
              >
                <Controller
                  control={control}
                  name="cost_category"
                  rules={{ required: "Cost category is required" }}
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
                required
                invalid={!!errors.description}
                errorText={errors.description?.message}
                label="Description"
              >
                <Textarea
                  {...register("description", {
                    required: "Description is required",
                  })}
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
                      checked={field.value}
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
              Save
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default AddCostRegistration
