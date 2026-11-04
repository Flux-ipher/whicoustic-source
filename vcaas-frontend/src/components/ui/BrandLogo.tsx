import React from 'react';

export interface BrandLogoProps {
  variant?: 'dark' | 'white' | 'amber';
  type?: 'wordmark' | 'full' | 'icon' | 'badge';
  className?: string;
  alt?: string;
}

export const BrandLogo: React.FC<BrandLogoProps> = ({
  variant = 'dark',
  type = 'wordmark',
  className = 'h-8 w-auto',
  alt = 'Whicoustic Logo',
}) => {
  let src = '/brand/whicoustic-wordmark.svg';

  if (type === 'icon') {
    src = '/brand/whicoustic-icon.svg';
  } else if (type === 'badge') {
    src = '/brand/whicoustic-badge.svg';
  } else if (type === 'full') {
    src = variant === 'white' 
      ? '/brand/whicoustic-full-white.svg' 
      : variant === 'amber'
      ? '/brand/whicoustic-full-amber.svg'
      : '/brand/whicoustic-full-dark.svg';
  } else {
    // wordmark
    src = variant === 'white'
      ? '/brand/whicoustic-wordmark-white.svg'
      : '/brand/whicoustic-wordmark.svg';
  }

  return (
    <img
      src={src}
      alt={alt}
      className={`inline-block select-none object-contain ${className}`}
      loading="eager"
    />
  );
};

