import tailwindcssAnimate from "tailwindcss-animate"

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // shadcn/ui CSS variable-based colors
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
          // Keep Remnawave brand teal/cyan scale
          50: '#ecfeff',
          100: '#cffafe',
          200: '#a5f3fc',
          300: '#67e8f9',
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
          700: '#0e7490',
          800: '#155e75',
          900: '#164e63',
          950: '#083344',
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
          // Keep Remnawave accent colors
          teal: '#0d9488',
          cyan: '#06b6d4',
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Keep existing dark palette
        dark: {
          50: '#c9d1d9',
          100: '#b1bac4',
          200: '#8b949e',
          300: '#6e7681',
          400: '#484f58',
          500: '#30363d',
          600: '#21262d',
          700: '#161b22',
          800: '#0d1117',
          900: '#010409',
          950: '#000000',
        },
        // Sidebar colors
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        glass: "14px",
      },
      backdropBlur: {
        glass: "var(--glass-blur)",
        "glass-heavy": "var(--glass-blur-heavy)",
      },
      fontFamily: {
        sans: ['Montserrat', 'system-ui', 'sans-serif'],
        mono: ['Fira Mono', 'JetBrains Mono', 'monospace'],
        display: ['Unbounded', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInDown: {
          '0%': { opacity: '0', transform: 'translateY(-8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideDown: {
          '0%': { opacity: '0', maxHeight: '0' },
          '100%': { opacity: '1', maxHeight: '500px' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        slideInLeft: {
          '0%': { transform: 'translateX(-8px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 15px -3px rgba(var(--glow-rgb), 0.3)' },
          '50%': { boxShadow: '0 0 25px -3px rgba(var(--glow-rgb), 0.5)' },
        },
        meshFloat1: {
          '0%, 100%': { transform: 'translate(0%, 0%) scale(1)' },
          '25%': { transform: 'translate(5%, -8%) scale(1.05)' },
          '50%': { transform: 'translate(-3%, 6%) scale(0.98)' },
          '75%': { transform: 'translate(4%, 3%) scale(1.02)' },
        },
        meshFloat2: {
          '0%, 100%': { transform: 'translate(0%, 0%) scale(1)' },
          '33%': { transform: 'translate(-4%, 5%) scale(1.03)' },
          '66%': { transform: 'translate(6%, -3%) scale(0.97)' },
        },
        meshFloat3: {
          '0%, 100%': { transform: 'translate(0%, 0%) scale(1)' },
          '20%': { transform: 'translate(3%, -6%) scale(1.04)' },
          '40%': { transform: 'translate(-5%, 2%) scale(0.96)' },
          '60%': { transform: 'translate(2%, 5%) scale(1.02)' },
          '80%': { transform: 'translate(-3%, -4%) scale(0.99)' },
        },
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'fade-in-up': 'fadeInUp 0.35s ease-out both',
        'fade-in-down': 'fadeInDown 0.3s ease-out both',
        'scale-in': 'scaleIn 0.25s ease-out both',
        'slide-down': 'slideDown 0.3s ease-out both',
        'shimmer': 'shimmer 1.5s infinite',
        'slide-in': 'slideInLeft 0.3s ease-out',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
        'mesh-1': 'meshFloat1 25s ease-in-out infinite',
        'mesh-2': 'meshFloat2 30s ease-in-out infinite',
        'mesh-3': 'meshFloat3 35s ease-in-out infinite',
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
      boxShadow: {
        'glow-teal': '0 0 30px -5px rgba(var(--glow-rgb), 0.3)',
        'glow-teal-lg': '0 0 40px -5px rgba(var(--glow-rgb), 0.4)',
        'deep': '0 8px 32px rgba(0, 0, 0, 0.4)',
        'card': '0 4px 16px rgba(0, 0, 0, 0.2)',
        'glass': '0 8px 32px rgba(0, 0, 0, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
        'glass-hover': '0 12px 40px rgba(0, 0, 0, 0.16), inset 0 1px 0 rgba(255, 255, 255, 0.08)',
        'neon-sm': '0 0 15px -5px rgba(var(--glow-rgb), 0.25)',
        'neon-md': '0 0 25px -8px rgba(var(--glow-rgb), 0.35)',
        'neon-lg': '0 0 40px -10px rgba(var(--glow-rgb), 0.4)',
        'float': '0 4px 20px -4px rgba(0, 0, 0, 0.3)',
      },
    },
  },
  plugins: [tailwindcssAnimate],
}
