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
import { FaExchangeAlt } from "react-icons/fa"
import {
  type CostElementSchedulePublic,
  CostElementSchedulesService,
  type CostElementScheduleUpdate,
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

// Extended type to include fields that exist in backend but are missing from generated types
type CostElementSchedulePublicExtended = CostElementSchedulePublic & {
  registration_date?: string | null
  description?: string | null
}

interface EditCostElementScheduleProps {
  schedule: CostElementSchedulePublicExtended
}

const EditCostElementSchedule = ({
  schedule,
}: EditCostElementScheduleProps) => {
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
  } = useForm<
    CostElementScheduleUpdate & {
      registration_date?: string
      description?: string
    }
  >({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      start_date: schedule.start_date,
      end_date: schedule.end_date,
      progression_type: schedule.progression_type,
      notes: schedule.notes ?? "",
      registration_date: schedule.registration_date ?? "",
      description: schedule.description ?? "",
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
        start_date: schedule.start_date,
        end_date: schedule.end_date,
        progression_type: schedule.progression_type,
        notes: schedule.notes ?? "",
        registration_date: schedule.registration_date ?? "",
        description: schedule.description ?? "",
      })
    }
  }, [isOpen, schedule, reset])

  const mutation = useMutation({
    mutationFn: (data: CostElementScheduleUpdate) =>
      CostElementSchedulesService.updateSchedule({
        id: schedule.schedule_id,
        requestBody: data,
      }),
    onSuccess: () => {
      showSuccessToast("Schedule updated successfully.")
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["cost-element-schedule-history"],
      })
      queryClient.invalidateQueries({
        queryKey: ["cost-element-schedule"],
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

  const onSubmit: SubmitHandler<
    CostElementScheduleUpdate & {
      registration_date?: string
      description?: string
    }
  > = (data) => {
    // Extract only the fields that are part of CostElementScheduleUpdate
    const updateData: CostElementScheduleUpdate = {
      start_date: data.start_date,
      end_date: data.end_date,
      progression_type: data.progression_type,
      notes: data.notes,
    }
    mutation.mutate(updateData)
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
            <DialogTitle>Edit Schedule</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Update the schedule information below.</Text>
            <VStack gap={4}>
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
              Update
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default EditCostElementSchedule
