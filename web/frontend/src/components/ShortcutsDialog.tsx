import { useTranslation } from 'react-i18next'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'

const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform)
const modKey = isMac ? '⌘' : 'Ctrl'

interface Shortcut {
  keys: string[]
  descKey: string
  descDefault: string
}

const shortcuts: Shortcut[] = [
  { keys: [modKey, 'K'], descKey: 'shortcuts.commandPalette', descDefault: 'Открыть командную палитру' },
  { keys: ['/'], descKey: 'shortcuts.quickSearch', descDefault: 'Быстрый поиск' },
  { keys: ['?'], descKey: 'shortcuts.showShortcuts', descDefault: 'Показать шорткаты' },
  { keys: ['Esc'], descKey: 'shortcuts.closeModal', descDefault: 'Закрыть модалку' },
]

function KeyBadge({ label }: { label: string }) {
  return (
    <kbd className="inline-flex items-center justify-center min-w-[28px] h-7 px-2 rounded-md border border-white/10 bg-white/5 text-xs font-medium text-dark-100 shadow-sm">
      {label}
    </kbd>
  )
}

export function ShortcutsDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const { t } = useTranslation()
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{t('shortcuts.title', { defaultValue: 'Горячие клавиши' })}</DialogTitle>
        </DialogHeader>
        <div className="space-y-2 pt-2">
          {shortcuts.map((s) => (
            <div key={s.descKey} className="flex items-center justify-between py-1.5">
              <span className="text-sm text-dark-200">
                {t(s.descKey, { defaultValue: s.descDefault })}
              </span>
              <div className="flex items-center gap-1">
                {s.keys.map((k, i) => (
                  <span key={i} className="flex items-center gap-1">
                    {i > 0 && <span className="text-dark-400 text-xs">+</span>}
                    <KeyBadge label={k} />
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  )
}
