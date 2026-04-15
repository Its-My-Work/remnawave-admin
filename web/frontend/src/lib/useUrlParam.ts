import { useSearchParams } from 'react-router-dom'
import { useCallback, useMemo } from 'react'

type ParamValue = string | number

export interface UseUrlParamOptions<T extends ParamValue> {
  parse?: (raw: string) => T
  serialize?: (value: T) => string
}

/**
 * Persist a single filter/pagination value in URL search params.
 *
 * - Default value is never written to URL (keeps URL clean).
 * - Empty string also removes the param.
 * - Uses history.replace so filter changes don't spam browser history.
 *
 * Usage:
 *   const [page, setPage] = useUrlParam('page', 1)
 *   const [search, setSearch] = useUrlParam('q', '')
 *   const [status, setStatus] = useUrlParam('status', '')
 */
type SetValueAction<T> = T | ((prev: T) => T)

export function useUrlParam(
  key: string,
  defaultValue: string,
  options?: UseUrlParamOptions<string>,
): [string, (value: SetValueAction<string>) => void]
export function useUrlParam(
  key: string,
  defaultValue: number,
  options?: UseUrlParamOptions<number>,
): [number, (value: SetValueAction<number>) => void]
export function useUrlParam<T extends ParamValue>(
  key: string,
  defaultValue: T,
  options?: UseUrlParamOptions<T>,
): [T, (value: SetValueAction<T>) => void] {
  const [searchParams, setSearchParams] = useSearchParams()
  const raw = searchParams.get(key)

  const parse = useCallback(
    (r: string | null): T => {
      if (r === null) return defaultValue
      if (options?.parse) return options.parse(r)
      if (typeof defaultValue === 'number') {
        const n = Number(r)
        return (Number.isFinite(n) ? n : defaultValue) as T
      }
      return r as T
    },
    [defaultValue, options],
  )

  const value = useMemo<T>(() => parse(raw), [raw, parse])

  const setValue = useCallback(
    (action: SetValueAction<T>) => {
      setSearchParams(
        (prev) => {
          const params = new URLSearchParams(prev)
          const current = parse(params.get(key))
          const next =
            typeof action === 'function'
              ? (action as (p: T) => T)(current)
              : action
          const isEmpty = next === '' || next === null || next === undefined
          const isDefault = next === defaultValue
          if (isEmpty || isDefault) {
            params.delete(key)
          } else {
            params.set(key, options?.serialize ? options.serialize(next) : String(next))
          }
          return params
        },
        { replace: true },
      )
    },
    [key, defaultValue, setSearchParams, options, parse],
  )

  return [value, setValue]
}
