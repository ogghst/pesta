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
import { useState } from "react"
import { Controller, type SubmitHandler, useForm } from "react-hook-form"
import { FaExchangeAlt } from "react-icons/fa"
import {
  type CostElementPublic,
  CostElementsService,
  type CostElementUpdate,
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

interface EditCostElementProps {
  costElement: CostElementPublic
}

const EditCostElement = ({ costElement }: EditCostElementProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid, isSubmitting },
  } = useForm<CostElementUpdate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      department_code: costElement.department_code,
      department_name: costElement.department_name,
      budget_bac: costElement.budget_bac,
      revenue_plan: costElement.revenue_plan,
      status: costElement.status,
      notes: costElement.notes,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: CostElementUpdate) =>
      CostElementsService.updateCostElement({
        id: costElement.cost_element_id,
        requestBody: data,
      }),
    onSuccess: () => {
      showSuccessToast("Cost Element updated successfully.")
      reset()
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["cost-elements"] })
      queryClient.invalidateQueries({
        queryKey: ["cost-elements", costElement.cost_element_id],
      })
    },
  })

  const onSubmit: SubmitHandler<CostElementUpdate> = (data) => {
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
                invalid={!!errors.revenue_plan}
                errorText={errors.revenue_plan?.message}
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
              </Field>

              <Field
                invalid={!!errors.status}
                errorText={errors.status?.message}
                label="Status"
              >
                <Controller
                  control={control}
                  name="status"
                  render={({ field }) => (
                    <select
                      {...field}
                      value={field.value || ""}
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

export default EditCostElement
