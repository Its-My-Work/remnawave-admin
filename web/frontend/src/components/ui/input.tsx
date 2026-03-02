import * as React from "react"

import { cn } from "@/lib/utils"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-[var(--glass-border)] bg-[var(--glass-bg)] backdrop-blur-sm px-3 py-2 text-sm text-dark-50 ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-dark-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:border-primary/40 focus-visible:shadow-[0_0_12px_-3px_rgba(var(--glow-rgb),0.3)] disabled:cursor-not-allowed disabled:opacity-50 transition-all hover:border-[var(--glass-border-hover)]",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
