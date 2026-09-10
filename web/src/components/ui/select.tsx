'use client'

import * as React from 'react'
import { Check, ChevronDown } from 'lucide-react'

import { cn } from '@/lib/utils'

/**
 * Dependency-free Select primitives.
 *
 * Mirrors the compositional shadcn/Radix API surface the app already imports
 * (`Select`, `SelectTrigger`, `SelectValue`, `SelectContent`, `SelectItem`)
 * without pulling in `@radix-ui/react-select`. Keyboard support is limited to
 * open/close + Escape; it is a lightweight popover over a controlled value.
 */

interface SelectContextValue {
  value: string | undefined
  onValueChange: (value: string) => void
  open: boolean
  setOpen: (open: boolean) => void
  registerItem: (value: string, label: string) => void
  labels: Record<string, string>
}

const SelectContext = React.createContext<SelectContextValue | null>(null)

function useSelectContext(component: string): SelectContextValue {
  const ctx = React.useContext(SelectContext)
  if (!ctx) {
    throw new Error(`<${component}> must be used within <Select>`)
  }
  return ctx
}

export interface SelectProps {
  value?: string
  defaultValue?: string
  onValueChange?: (value: string) => void
  disabled?: boolean
  children: React.ReactNode
}

function Select({ value, defaultValue, onValueChange, children }: SelectProps) {
  const [uncontrolled, setUncontrolled] = React.useState<string | undefined>(defaultValue)
  const [open, setOpen] = React.useState(false)
  const [labels, setLabels] = React.useState<Record<string, string>>({})

  const isControlled = value !== undefined
  const currentValue = isControlled ? value : uncontrolled

  const handleValueChange = React.useCallback(
    (next: string) => {
      if (!isControlled) {
        setUncontrolled(next)
      }
      onValueChange?.(next)
      setOpen(false)
    },
    [isControlled, onValueChange],
  )

  const registerItem = React.useCallback((itemValue: string, label: string) => {
    setLabels((prev) => (prev[itemValue] === label ? prev : { ...prev, [itemValue]: label }))
  }, [])

  const ctx = React.useMemo<SelectContextValue>(
    () => ({
      value: currentValue,
      onValueChange: handleValueChange,
      open,
      setOpen,
      registerItem,
      labels,
    }),
    [currentValue, handleValueChange, open, registerItem, labels],
  )

  return (
    <SelectContext.Provider value={ctx}>
      <div className="relative">{children}</div>
    </SelectContext.Provider>
  )
}

export type SelectTriggerProps = React.ButtonHTMLAttributes<HTMLButtonElement>

const SelectTrigger = React.forwardRef<HTMLButtonElement, SelectTriggerProps>(
  ({ className, children, ...props }, ref) => {
    const { open, setOpen } = useSelectContext('SelectTrigger')
    return (
      <button
        ref={ref}
        type="button"
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        onClick={() => setOpen(!open)}
        className={cn(
          'flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
          className,
        )}
        {...props}
      >
        {children}
        <ChevronDown className="h-4 w-4 opacity-50" />
      </button>
    )
  },
)
SelectTrigger.displayName = 'SelectTrigger'

export interface SelectValueProps {
  placeholder?: string
  className?: string
}

function SelectValue({ placeholder, className }: SelectValueProps) {
  const { value, labels } = useSelectContext('SelectValue')
  const display = value !== undefined ? labels[value] ?? value : undefined
  return (
    <span className={cn('truncate', display ? undefined : 'text-muted-foreground', className)}>
      {display ?? placeholder ?? ''}
    </span>
  )
}

export type SelectContentProps = React.HTMLAttributes<HTMLDivElement>

const SelectContent = React.forwardRef<HTMLDivElement, SelectContentProps>(
  ({ className, children, ...props }, ref) => {
    const { open, setOpen } = useSelectContext('SelectContent')

    React.useEffect(() => {
      if (!open) return
      const onKey = (e: KeyboardEvent) => {
        if (e.key === 'Escape') setOpen(false)
      }
      document.addEventListener('keydown', onKey)
      return () => document.removeEventListener('keydown', onKey)
    }, [open, setOpen])

    return (
      <>
        {open && (
          <div
            className="fixed inset-0 z-40"
            aria-hidden="true"
            onClick={() => setOpen(false)}
          />
        )}
        <div
          ref={ref}
          role="listbox"
          hidden={!open}
          className={cn(
            'absolute z-50 mt-1 max-h-60 w-full min-w-[8rem] overflow-auto rounded-md border bg-popover p-1 text-popover-foreground shadow-md',
            className,
          )}
          {...props}
        >
          {children}
        </div>
      </>
    )
  },
)
SelectContent.displayName = 'SelectContent'

export interface SelectItemProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onSelect'> {
  value: string
}

const SelectItem = React.forwardRef<HTMLDivElement, SelectItemProps>(
  ({ className, children, value, ...props }, ref) => {
    const { value: selected, onValueChange, registerItem } = useSelectContext('SelectItem')

    React.useEffect(() => {
      if (typeof children === 'string') {
        registerItem(value, children)
      }
    }, [value, children, registerItem])

    const isSelected = selected === value

    return (
      <div
        ref={ref}
        role="option"
        aria-selected={isSelected}
        onClick={() => onValueChange(value)}
        className={cn(
          'relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground',
          isSelected && 'bg-accent/50',
          className,
        )}
        {...props}
      >
        <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
          {isSelected && <Check className="h-4 w-4" />}
        </span>
        {children}
      </div>
    )
  },
)
SelectItem.displayName = 'SelectItem'

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem }
