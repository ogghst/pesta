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
import { Controller, type SubmitHandler, useForm } from "react-hook-form"
import { FaPlus } from "react-icons/fa"
import {
  type CostElementScheduleBase,
  CostElementSchedulesService,
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

interface AddCostElementScheduleProps {
  costElementId: string
}

// Extended type to include fields that exist in backend but are missing from generated types
type CostElementScheduleBaseExtended = CostElementScheduleBase & {
  registration_date?: string
  description?: string
}

const getTodayIsoDate = () => new Date().toISOString().slice(0, 10)

const AddCostElementSchedule = ({
  costElementId,
}: AddCostElementScheduleProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const {
    control,
    register,
    handleSubmit,
    reset,
    watch,
    setError,
    clearErrors,
    formState: { errors, isValid, isSubmitting },
  } = useForm<CostElementScheduleBaseExtended>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      start_date: "",
      end_date: "",
      progression_type: "linear",
      registration_date: getTodayIsoDate(),
      description: "",
      notes: "",
    },
  })

  // Watch dates for validation
  const startDate = watch("start_date")
  const endDate = watch("end_date")

  // Validate end_date >= start_date
  useEffect(() => {
    if (startDate && endDate && new Date(endDate) < new Date(startDate)) {
      setError("end_date", {
        type: "manual",
        message: "End date must be greater than or equal to start date",
      })
    } else {
      clearErrors("end_date")
    }
  }, [startDate, endDate, setError, clearErrors])

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (isOpen) {
      reset({
        start_date: "",
        end_date: "",
        progression_type: "linear",
        registration_date: getTodayIsoDate(),
        description: "",
        notes: "",
      })
    }
  }, [isOpen, reset])

  const mutation = useMutation({
    mutationFn: (data: CostElementScheduleBaseExtended) =>
      CostElementSchedulesService.createSchedule({
        costElementId,
        requestBody: data as CostElementScheduleBase,
      }),
    onSuccess: () => {
      showSuccessToast("Schedule created successfully.")
      reset()
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["cost-element-schedule-history", costElementId],
      })
      queryClient.invalidateQueries({
        queryKey: ["cost-element-schedule", costElementId],
      })
      // Invalidate timeline queries
      queryClient.invalidateQueries({
        queryKey: ["cost-elements-with-schedules"],
      })
      queryClient.invalidateQueries({
        queryKey: ["cost-timeline"],
      })
      queryClient.invalidateQueries({
        queryKey: ["earned-value-timeline"],
      })
    },
  })

  const onSubmit: SubmitHandler<CostElementScheduleBaseExtended> = (data) => {
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
        <Button value="add-cost-element-schedule" my={4}>
          <FaPlus fontSize="16px" />
          Add Schedule
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Add Schedule</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>
              Fill in the form below to create a new schedule registration.
            </Text>
            <VStack gap={4}>
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
                invalid={!!errors.start_date}
                errorText={errors.start_date?.message}
                label="Start Date"
              >
                <Input
                  {...register("start_date", {
                    required: "Start date is required",
                  })}
                  type="date"
                />
              </Field>

              <Field
                required
                invalid={!!errors.end_date}
                errorText={errors.end_date?.message}
                label="End Date"
              >
                <Input
                  {...register("end_date", {
                    required: "End date is required",
                  })}
                  type="date"
                />
              </Field>

              <Field
                invalid={!!errors.progression_type}
                errorText={errors.progression_type?.message}
                label="Progression Type"
              >
                <Controller
                  control={control}
                  name="progression_type"
                  render={({ field }) => (
                    <select
                      {...field}
                      value={field.value || ""}
                      style={{
                        width: "100%",
                        padding: "8px",
                        borderRadius: "4px",
                        border: errors.progression_type
                          ? "1px solid #ef4444"
                          : "1px solid #e2e8f0",
                      }}
                    >
                      <option value="linear">Linear</option>
                      <option value="gaussian">Gaussian</option>
                      <option value="logarithmic">Logarithmic</option>
                    </select>
                  )}
                />
              </Field>

              <Field
                invalid={!!errors.description}
                errorText={errors.description?.message}
                label="Schedule Description"
              >
                <Textarea
                  {...register("description")}
                  placeholder="Optional description for this registration"
                  rows={2}
                />
              </Field>

              <Field
                invalid={!!errors.notes}
                errorText={errors.notes?.message}
                label="Schedule Notes"
              >
                <Textarea
                  {...register("notes")}
                  placeholder="Additional schedule notes"
                  rows={3}
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

export default AddCostElementSchedule
