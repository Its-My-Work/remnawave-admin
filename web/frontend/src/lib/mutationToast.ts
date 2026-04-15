import { toast } from 'sonner'

type ErrorLike = Error & { response?: { data?: { detail?: string } } }

/**
 * Show a toast for a failed mutation with a "Retry" action.
 *
 * Usage in react-query onError:
 *   onError: (err, vars) => toastMutationError(err, fallback, () => mutation.mutate(vars))
 */
export function toastMutationError(
  err: unknown,
  fallbackMessage: string,
  retry?: () => void,
  retryLabel = 'Повторить',
) {
  const e = err as ErrorLike
  const message = e?.response?.data?.detail || e?.message || fallbackMessage
  toast.error(message, {
    duration: 8000,
    action: retry
      ? {
          label: retryLabel,
          onClick: retry,
        }
      : undefined,
  })
}
