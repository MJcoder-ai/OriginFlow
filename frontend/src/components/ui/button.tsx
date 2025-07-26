import React from 'react';
import clsx from 'clsx';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'ghost' | 'destructive' | 'default';
  size?: 'icon' | 'default';
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'default',
  size = 'default',
  className,
  ...props
}) => {
  const variantClasses = {
    default: 'bg-blue-600 text-white hover:bg-blue-700',
    ghost: 'bg-transparent hover:bg-gray-100 text-gray-700',
    destructive: 'bg-red-600 text-white hover:bg-red-700',
  }[variant];

  const sizeClasses = size === 'icon' ? 'p-2' : 'px-4 py-2';

  return (
    <button
      className={clsx('rounded-md focus:outline-none', variantClasses, sizeClasses, className)}
      {...props}
    />
  );
};

export default Button;
