import { useEffect } from 'react'
import { useAppearanceStore, useResolvedColorMode } from '../store/useAppearanceStore'

/**
 * Syncs appearance settings from the Zustand store to the <html> element
 * as data-* attributes so CSS can respond to them globally.
 */
export function AppearanceProvider({ children }: { children: React.ReactNode }) {
  const { theme, density, borderRadius, fontSize, animationsEnabled } = useAppearanceStore()
  const resolvedMode = useResolvedColorMode()

  useEffect(() => {
    const root = document.documentElement
    root.setAttribute('data-theme', theme)
    root.setAttribute('data-mode', resolvedMode)
    root.setAttribute('data-density', density)
    root.setAttribute('data-radius', borderRadius)
    root.setAttribute('data-font-size', fontSize)
    root.setAttribute('data-animations', String(animationsEnabled))
  }, [theme, resolvedMode, density, borderRadius, fontSize, animationsEnabled])

  return <>{children}</>
}
