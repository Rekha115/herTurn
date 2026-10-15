import React from 'react';

export default function Button({
  children,
  variant = 'primary', // primary, secondary, outline, ghost, soft
  size = 'md', // sm, md, lg
  className = '',
  disabled = false,
  onClick,
  type = 'button',
  icon: Icon,
  iconPosition = 'left',
  ...props
}) {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-full transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] select-none text-center';

  const sizeStyles = {
    sm: 'text-xs px-3.5 py-1.5 gap-1.5 shadow-xs',
    md: 'text-sm px-5 py-2.5 gap-2 shadow-sm',
    lg: 'text-base px-6 py-3 gap-2.5 shadow-sm',
  };

  const variantStyles = {
    primary: 'bg-[#3E1E43] text-white hover:bg-[#2C1430] hover:shadow-md border border-[#3E1E43]',
    secondary: 'bg-[#F6D6C6] text-[#3E1E43] hover:bg-[#F2C4AF] border border-[#ECD0C0] font-semibold',
    outline: 'bg-transparent text-[#3E1E43] border border-[#3E1E43]/30 hover:border-[#3E1E43] hover:bg-[#3E1E43]/5',
    soft: 'bg-[#EAE3F1] text-[#3E1E43] hover:bg-[#E0D5E9] border border-[#DFD5E7]',
    ghost: 'bg-transparent text-[#4A454D] hover:text-[#3E1E43] hover:bg-[#3E1E43]/5',
  };

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`${baseStyles} ${sizeStyles[size] || sizeStyles.md} ${variantStyles[variant] || variantStyles.primary} ${className}`}
      {...props}
    >
      {Icon && iconPosition === 'left' && <Icon className="w-4 h-4 shrink-0" />}
      <span>{children}</span>
      {Icon && iconPosition === 'right' && <Icon className="w-4 h-4 shrink-0" />}
    </button>
  );
}
