import React from 'react';
import clsx from 'clsx';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'dark' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'left',
  isLoading = false,
  className,
  disabled,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-berthold font-medium rounded-pill transition-all duration-200 select-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none active:scale-[0.98]';

  const variants = {
    // Primary Amber Pill CTA
    primary:
      'bg-primary-container text-white hover:bg-primary-hover shadow-amber-glow hover:shadow-lg',
    // Secondary Outlined Pill
    secondary:
      'bg-white text-on-surface border border-outline-subtle hover:border-on-surface hover:bg-surface-container-low shadow-sm',
    // Dark Slate Utility Pill
    dark:
      'bg-on-surface text-white hover:bg-inverse-surface shadow-md',
    // Subtle Ghost Pill
    ghost:
      'bg-transparent text-secondary hover:text-on-surface hover:bg-surface-container-high',
    // Danger Pill
    danger:
      'bg-error text-white hover:bg-red-700 shadow-sm',
  };

  const sizes = {
    sm: 'text-xs px-3.5 py-1.5 gap-1.5',
    md: 'text-sm px-5 py-2.5 gap-2',
    lg: 'text-base px-7 py-3.5 gap-2.5',
  };

  return (
    <button
      className={clsx(baseStyles, variants[variant], sizes[size], className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      ) : (
        icon && iconPosition === 'left' && <span className="inline-flex shrink-0">{icon}</span>
      )}
      <span>{children}</span>
      {!isLoading && icon && iconPosition === 'right' && (
        <span className="inline-flex shrink-0">{icon}</span>
      )}
    </button>
  );
};

