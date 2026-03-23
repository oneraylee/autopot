import { useMutation, type UseMutationOptions } from "@tanstack/react-query";

interface UseMutationWithToastOptions<TData, TError, TVariables, TContext = unknown>
  extends Omit<UseMutationOptions<TData, TError, TVariables, TContext>, "mutationFn"> {
  mutationFn: (variables: TVariables) => Promise<TData>;
  successMessage?: string;
}

export function useMutationWithToast<
  TData = unknown,
  TError extends Error = Error,
  TVariables = void,
  TContext = unknown,
>(options: UseMutationWithToastOptions<TData, TError, TVariables, TContext>) {
  const { successMessage, onSuccess, onError, ...rest } = options;

  return useMutation<TData, TError, TVariables, TContext>({
    ...rest,
    onSuccess: (...args) => {
      if (successMessage) {
        console.info(`[toast:success] ${successMessage}`);
      }
      onSuccess?.(...args);
    },
    onError: (...args) => {
      console.error(`[toast:error] ${args[0].message}`);
      onError?.(...args);
    },
  });
}
