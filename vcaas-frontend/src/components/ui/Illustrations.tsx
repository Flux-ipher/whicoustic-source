import React from 'react';
import { motion } from 'framer-motion';

// Common SVG props
interface IllustrationProps {
  className?: string;
  size?: number;
}

/**
 * 1. Microphone Blocked / Permission Denied Illustration
 * Features an acoustic studio microphone with muted waves and a visual browser permission shield
 */
export const MicBlockedIllustration: React.FC<IllustrationProps> = ({ className = '', size = 200 }) => {
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 200 200"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="overflow-visible"
      >
        {/* Soft radial background glow */}
        <circle cx="100" cy="100" r="75" fill="#FEE2E2" fillOpacity="0.45" />
        
        {/* Animated blocked soundwave rings */}
        <motion.circle
          cx="100"
          cy="95"
          r="55"
          stroke="#EF4444"
          strokeWidth="2"
          strokeDasharray="4 6"
          strokeOpacity="0.4"
          animate={{ scale: [0.95, 1.05, 0.95], opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        />
        <circle cx="100" cy="95" r="40" stroke="#F87171" strokeWidth="2" strokeOpacity="0.5" strokeDasharray="3 4" />

        {/* Microphone Base Stand */}
        <path d="M75 162H125" stroke="#0B1C30" strokeWidth="4" strokeLinecap="round" />
        <path d="M100 138V162" stroke="#0B1C30" strokeWidth="4" strokeLinecap="round" />
        <path
          d="M72 100C72 115.464 84.536 128 100 128C115.464 128 128 115.464 128 100"
          stroke="#0B1C30"
          strokeWidth="4"
          strokeLinecap="round"
        />

        {/* Microphone Capsule */}
        <rect x="86" y="62" width="28" height="52" rx="14" fill="#FFFFFF" stroke="#0B1C30" strokeWidth="4" />
        <line x1="88" y1="84" x2="112" y2="84" stroke="#CBD5E1" strokeWidth="3" strokeLinecap="round" />
        <line x1="92" y1="74" x2="108" y2="74" stroke="#CBD5E1" strokeWidth="2" strokeLinecap="round" />
        <line x1="92" y1="94" x2="108" y2="94" stroke="#CBD5E1" strokeWidth="2" strokeLinecap="round" />

        {/* Warning / Blocked Slash */}
        <motion.line
          x1="65"
          y1="60"
          x2="135"
          y2="130"
          stroke="#EF4444"
          strokeWidth="5"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />

        {/* Floating Browser Permission Badge */}
        <motion.g
          animate={{ y: [-3, 3, -3] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
        >
          <rect x="122" y="42" width="38" height="38" rx="10" fill="#FFFFFF" stroke="#EF4444" strokeWidth="2.5" />
          <circle cx="141" cy="56" r="4" fill="#EF4444" />
          <path d="M141 64V68" stroke="#EF4444" strokeWidth="2.5" strokeLinecap="round" />
        </motion.g>
      </svg>
    </div>
  );
};

/**
 * 2. Connection Lost / Server Offline Illustration
 * Features an acoustic server rack with disconnected telemetry signals and retry antenna
 */
export const ConnectionLostIllustration: React.FC<IllustrationProps> = ({ className = '', size = 200 }) => {
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 200 200"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="overflow-visible"
      >
        <circle cx="100" cy="100" r="75" fill="#FEF3C7" fillOpacity="0.45" />

        {/* Severed Signal Waveforms */}
        <path d="M35 100H65L75 80L85 110L90 100" stroke="#CBD5E1" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M110 100L115 90L125 120L135 100H165" stroke="#CBD5E1" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />

        {/* Severed Connection Spark */}
        <motion.circle
          cx="100"
          cy="100"
          r="16"
          fill="#F59E0B"
          fillOpacity="0.2"
          animate={{ scale: [1, 1.3, 1], opacity: [0.4, 0.8, 0.4] }}
          transition={{ duration: 2, repeat: Infinity }}
        />
        <circle cx="100" cy="100" r="8" fill="#F59E0B" />

        {/* Server Block */}
        <rect x="65" y="125" width="70" height="35" rx="8" fill="#FFFFFF" stroke="#0B1C30" strokeWidth="3.5" />
        <line x1="77" y1="137" x2="105" y2="137" stroke="#CBD5E1" strokeWidth="3" strokeLinecap="round" />
        <line x1="77" y1="147" x2="95" y2="147" stroke="#CBD5E1" strokeWidth="3" strokeLinecap="round" />
        <circle cx="123" cy="137" r="3" fill="#EF4444" />
        <circle cx="123" cy="147" r="3" fill="#CBD5E1" />

        {/* Antenna Tower with radiating radar signal */}
        <path d="M100 70V50" stroke="#0B1C30" strokeWidth="3.5" strokeLinecap="round" />
        <circle cx="100" cy="46" r="4" fill="#F59E0B" />
        <motion.path
          d="M86 42C90 36 110 36 114 42"
          stroke="#F59E0B"
          strokeWidth="2.5"
          strokeLinecap="round"
          animate={{ opacity: [0.2, 1, 0.2] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
        <motion.path
          d="M78 35C86 26 114 26 122 35"
          stroke="#F59E0B"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeDasharray="3 4"
          animate={{ opacity: [0.1, 0.7, 0.1] }}
          transition={{ duration: 1.5, repeat: Infinity, delay: 0.3 }}
        />
      </svg>
    </div>
  );
};

/**
 * 3. Empty Search / No Results Illustration
 * Magnifying glass scanning acoustic spectrum with 0 frequency peaks
 */
export const EmptySearchIllustration: React.FC<IllustrationProps> = ({ className = '', size = 200 }) => {
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 200 200"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="overflow-visible"
      >
        <circle cx="100" cy="100" r="75" fill="#E5EEFF" fillOpacity="0.45" />

        {/* Flat Acoustic Baseline */}
        <line x1="40" y1="110" x2="160" y2="110" stroke="#CBD5E1" strokeWidth="2.5" strokeDasharray="4 6" />

        {/* Magnifying Glass with Scan Sweep */}
        <motion.g
          animate={{
            x: [-6, 6, -6],
            y: [-4, 4, -4],
          }}
          transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
        >
          <circle cx="95" cy="88" r="34" fill="#FFFFFF" stroke="#0B1C30" strokeWidth="4" />
          <circle cx="95" cy="88" r="26" fill="#F8F9FF" />
          <path d="M120 113L146 139" stroke="#0B1C30" strokeWidth="5" strokeLinecap="round" />
          
          {/* Subtle acoustic wave inside lens */}
          <path
            d="M78 88H84L89 80L95 96L101 84L106 88H112"
            stroke="#F59E0B"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </motion.g>

        {/* Little Floating Zero/Question Particle */}
        <motion.g
          animate={{ y: [-3, 3, -3], opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 2.2, repeat: Infinity }}
        >
          <circle cx="145" cy="65" r="14" fill="#FFFFFF" stroke="#CBD5E1" strokeWidth="2" />
          <text x="145" y="70" textAnchor="middle" fill="#0B1C30" fontSize="13" fontWeight="bold" fontFamily="monospace">
            0
          </text>
        </motion.g>
      </svg>
    </div>
  );
};

/**
 * 4. Empty Vault / No Voice Clones Illustration
 * An acoustic vault door waiting for reference biometric audio samples
 */
export const EmptyVaultIllustration: React.FC<IllustrationProps> = ({ className = '', size = 200 }) => {
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 200 200"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="overflow-visible"
      >
        <circle cx="100" cy="100" r="75" fill="#FEF3C7" fillOpacity="0.4" />

        {/* Vault Frame */}
        <rect x="52" y="48" width="96" height="104" rx="16" fill="#FFFFFF" stroke="#0B1C30" strokeWidth="4" />

        {/* Vault Dial */}
        <circle cx="100" cy="100" r="30" fill="#F8F9FF" stroke="#0B1C30" strokeWidth="3.5" />
        <motion.g
          animate={{ rotate: 360 }}
          transition={{ duration: 16, repeat: Infinity, ease: 'linear' }}
          style={{ originX: '100px', originY: '100px' }}
        >
          <circle cx="100" cy="100" r="22" stroke="#CBD5E1" strokeWidth="2" strokeDasharray="3 5" />
          <circle cx="100" cy="78" r="3" fill="#F59E0B" />
        </motion.g>

        {/* Center Audio Keyhole */}
        <path
          d="M96 95C96 92.79 97.79 91 100 91C102.21 91 104 92.79 104 95C104 96.6 103.04 97.98 101.66 98.62L103 107H97L98.34 98.62C96.96 97.98 96 96.6 96 95Z"
          fill="#0B1C30"
        />

        {/* Floating Plus Seed */}
        <motion.g
          animate={{ scale: [1, 1.15, 1] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        >
          <circle cx="140" cy="58" r="14" fill="#F59E0B" />
          <path d="M140 52V64M134 58H146" stroke="#0B1C30" strokeWidth="2.5" strokeLinecap="round" />
        </motion.g>
      </svg>
    </div>
  );
};

/**
 * 5. Empty Inbox / No Requests Illustration
 * Studio licensing desk with clean ledger and peaceful acoustic waves
 */
export const EmptyInboxIllustration: React.FC<IllustrationProps> = ({ className = '', size = 200 }) => {
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 200 200"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="overflow-visible"
      >
        <circle cx="100" cy="100" r="75" fill="#E5EEFF" fillOpacity="0.45" />

        {/* Document clipboard */}
        <rect x="62" y="55" width="76" height="95" rx="10" fill="#FFFFFF" stroke="#0B1C30" strokeWidth="3.5" />
        <rect x="80" y="46" width="40" height="15" rx="5" fill="#0B1C30" />
        
        {/* Document placeholder lines */}
        <line x1="76" y1="78" x2="114" y2="78" stroke="#CBD5E1" strokeWidth="3" strokeLinecap="round" />
        <line x1="76" y1="92" x2="124" y2="92" stroke="#CBD5E1" strokeWidth="3" strokeLinecap="round" />
        <line x1="76" y1="106" x2="105" y2="106" stroke="#CBD5E1" strokeWidth="3" strokeLinecap="round" />

        {/* Checkmark Stamp */}
        <motion.g
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <circle cx="130" cy="130" r="18" fill="#10B981" />
          <path d="M123 130L128 135L138 125" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </motion.g>
      </svg>
    </div>
  );
};

/**
 * 6. 404 Not Found Illustration
 * Disconnected soundwave spectrum drifting into orbit
 */
export const NotFoundIllustration: React.FC<IllustrationProps> = ({ className = '', size = 220 }) => {
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 220 220"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="overflow-visible"
      >
        <circle cx="110" cy="110" r="85" fill="#FEF3C7" fillOpacity="0.35" />

        {/* Giant 404 Text */}
        <text
          x="110"
          y="100"
          textAnchor="middle"
          fill="#0B1C30"
          fontSize="48"
          fontWeight="bold"
          fontFamily="Recoleta, Georgia, serif"
          letterSpacing="-0.03em"
        >
          404
        </text>

        {/* Radar Orbit */}
        <ellipse cx="110" cy="120" rx="70" ry="25" stroke="#CBD5E1" strokeWidth="2" strokeDasharray="5 7" />

        {/* Orbiting Satellite Node */}
        <motion.g
          animate={{
            x: [0, 40, 0, -40, 0],
            y: [0, -8, 0, 8, 0],
          }}
          transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
        >
          <circle cx="110" cy="145" r="9" fill="#F59E0B" />
          <circle cx="110" cy="145" r="14" stroke="#F59E0B" strokeWidth="1.5" strokeOpacity="0.5" />
        </motion.g>

        {/* Ground Waveform Baseline */}
        <path
          d="M50 170L70 170L80 160L90 180L100 165L110 175L120 160L130 178L140 170L170 170"
          stroke="#0B1C30"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
};


/**
 * 7. Biometric Shield & Provenance Illustration
 * Used in Privacy, Settings, and Security panels
 */
export const BiometricShieldIllustration: React.FC<IllustrationProps> = ({ className = '', size = 180 }) => {
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg width={size} height={size} viewBox="0 0 180 180" fill="none" xmlns="http://www.w3.org/2000/svg" className="overflow-visible">
        <circle cx="90" cy="90" r="70" fill="#E5EEFF" fillOpacity="0.45" />

        {/* Shield outline */}
        <path
          d="M90 32L132 48V94C132 122 114 144 90 152C66 144 48 122 48 94V48L90 32Z"
          fill="#FFFFFF"
          stroke="#0B1C30"
          strokeWidth="3.5"
          strokeLinejoin="round"
        />

        {/* Animated Inner Biometric Soundwave Ring */}
        <motion.path
          d="M70 90C70 78.954 78.954 70 90 70C101.046 70 110 78.954 110 90C110 101.046 101.046 110 90 110"
          stroke="#F59E0B"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeDasharray="4 4"
          animate={{ rotate: 360 }}
          transition={{ duration: 12, repeat: Infinity, ease: 'linear' }}
          style={{ originX: '90px', originY: '90px' }}
        />

        {/* Center Sound Frequency Nodes */}
        <line x1="80" y1="90" x2="80" y2="90.01" stroke="#0B1C30" strokeWidth="4" strokeLinecap="round" />
        <line x1="86" y1="84" x2="86" y2="96" stroke="#0B1C30" strokeWidth="3" strokeLinecap="round" />
        <line x1="90" y1="78" x2="90" y2="102" stroke="#F59E0B" strokeWidth="3.5" strokeLinecap="round" />
        <line x1="94" y1="84" x2="94" y2="96" stroke="#0B1C30" strokeWidth="3" strokeLinecap="round" />
        <line x1="100" y1="90" x2="100" y2="90.01" stroke="#0B1C30" strokeWidth="4" strokeLinecap="round" />

        {/* Checkmark verification badge */}
        <circle cx="122" cy="120" r="14" fill="#10B981" />
        <path d="M117 120L121 124L127 116" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
};

/**
 * 8. Studio Consultation & Engineering Illustration
 * Used in ContactPage and Studio Consultation sections
 */
export const StudioConsultationIllustration: React.FC<IllustrationProps> = ({ className = '', size = 180 }) => {
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg width={size} height={size} viewBox="0 0 180 180" fill="none" xmlns="http://www.w3.org/2000/svg" className="overflow-visible">
        <circle cx="90" cy="90" r="70" fill="#FEF3C7" fillOpacity="0.45" />

        {/* Studio Mixing Console Base */}
        <rect x="44" y="95" width="92" height="48" rx="8" fill="#FFFFFF" stroke="#0B1C30" strokeWidth="3.5" />
        
        {/* Sliders & Knobs */}
        <line x1="62" y1="106" x2="62" y2="132" stroke="#CBD5E1" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx="62" cy="116" r="4.5" fill="#F59E0B" />

        <line x1="80" y1="106" x2="80" y2="132" stroke="#CBD5E1" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx="80" cy="124" r="4.5" fill="#0B1C30" />

        <line x1="98" y1="106" x2="98" y2="132" stroke="#CBD5E1" strokeWidth="2.5" strokeLinecap="round" />
        <circle cx="98" cy="112" r="4.5" fill="#F59E0B" />

        <circle cx="120" cy="114" r="5" stroke="#0B1C30" strokeWidth="2.5" />
        <circle cx="120" cy="128" r="5" stroke="#CBD5E1" strokeWidth="2.5" />

        {/* Floating Studio Headphones */}
        <motion.g
          animate={{ y: [-3, 3, -3] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        >
          <path d="M60 76C60 59.431 73.431 46 90 46C106.569 46 120 59.431 120 76" stroke="#0B1C30" strokeWidth="3.5" strokeLinecap="round" fill="none" />
          <rect x="52" y="70" width="12" height="22" rx="6" fill="#F59E0B" stroke="#0B1C30" strokeWidth="3" />
          <rect x="116" y="70" width="12" height="22" rx="6" fill="#F59E0B" stroke="#0B1C30" strokeWidth="3" />
        </motion.g>
      </svg>
    </div>
  );
};

/**
 * 9. Legal Compliance & Governance Illustration
 * Used in Terms of Service and IP protocol sections
 */
export const LegalComplianceIllustration: React.FC<IllustrationProps> = ({ className = '', size = 180 }) => {
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg width={size} height={size} viewBox="0 0 180 180" fill="none" xmlns="http://www.w3.org/2000/svg" className="overflow-visible">
        <circle cx="90" cy="90" r="70" fill="#E5EEFF" fillOpacity="0.45" />

        {/* Pillar of Justice / Framework */}
        <rect x="52" y="142" width="76" height="10" rx="3" fill="#0B1C30" />
        <rect x="58" y="134" width="64" height="8" rx="2" fill="#FFFFFF" stroke="#0B1C30" strokeWidth="2.5" />

        {/* Pillars */}
        <line x1="68" y1="62" x2="68" y2="134" stroke="#0B1C30" strokeWidth="3.5" strokeLinecap="round" />
        <line x1="90" y1="62" x2="90" y2="134" stroke="#0B1C30" strokeWidth="3.5" strokeLinecap="round" />
        <line x1="112" y1="62" x2="112" y2="134" stroke="#0B1C30" strokeWidth="3.5" strokeLinecap="round" />

        {/* Top Pediment */}
        <path d="M50 62L90 38L130 62H50Z" fill="#FFFFFF" stroke="#0B1C30" strokeWidth="3.5" strokeLinejoin="round" />
        
        {/* Floating Golden Seal */}
        <motion.g
          animate={{ scale: [1, 1.1, 1] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
        >
          <circle cx="90" cy="52" r="6" fill="#F59E0B" />
        </motion.g>

        {/* Sound frequency banner */}
        <rect x="74" y="90" width="32" height="22" rx="4" fill="#FFFFFF" stroke="#F59E0B" strokeWidth="2" />
        <path d="M78 101H82L85 96L89 106L93 98L97 101H102" stroke="#F59E0B" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
};

/**
 * 10. Royalty Escrow & Disbursements Illustration
 * Used in EarningsPage and RoyaltiesPage
 */
export const RoyaltyEscrowIllustration: React.FC<IllustrationProps> = ({ className = '', size = 180 }) => {
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg width={size} height={size} viewBox="0 0 180 180" fill="none" xmlns="http://www.w3.org/2000/svg" className="overflow-visible">
        <circle cx="90" cy="90" r="70" fill="#FEF3C7" fillOpacity="0.4" />

        {/* Vault Safe */}
        <rect x="52" y="60" width="76" height="84" rx="10" fill="#FFFFFF" stroke="#0B1C30" strokeWidth="3.5" />
        
        {/* Safe Handle */}
        <circle cx="90" cy="102" r="18" fill="#F8F9FF" stroke="#0B1C30" strokeWidth="3" />
        <circle cx="90" cy="102" r="6" fill="#F59E0B" />

        {/* Floating Escrow Tokens / Coins with Motion */}
        <motion.g
          animate={{ y: [-4, 4, -4] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
        >
          <circle cx="68" cy="48" r="14" fill="#F59E0B" stroke="#0B1C30" strokeWidth="2.5" />
          <text x="68" y="53" textAnchor="middle" fill="#0B1C30" fontSize="12" fontWeight="bold" fontFamily="monospace">$</text>
        </motion.g>

        <motion.g
          animate={{ y: [4, -4, 4] }}
          transition={{ duration: 2.6, repeat: Infinity, ease: 'easeInOut', delay: 0.3 }}
        >
          <circle cx="112" cy="42" r="12" fill="#FFFFFF" stroke="#0B1C30" strokeWidth="2.5" />
          <path d="M107 42H117M112 37V47" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" />
        </motion.g>

        {/* Acoustic Flow Line into Vault */}
        <path d="M68 62V72C68 80 80 82 80 90" stroke="#CBD5E1" strokeWidth="2" strokeDasharray="3 3" />
      </svg>
    </div>
  );
};

/**
 * 11. Talent & Voice Persona Illustration
 * Used in Talent Hub and Artist profile settings
 */
export const TalentVoiceIllustration: React.FC<IllustrationProps> = ({ className = '', size = 180 }) => {
  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg width={size} height={size} viewBox="0 0 180 180" fill="none" xmlns="http://www.w3.org/2000/svg" className="overflow-visible">
        <circle cx="90" cy="90" r="70" fill="#E5EEFF" fillOpacity="0.45" />

        {/* Star Performer Aura */}
        <motion.circle
          cx="90"
          cy="90"
          r="54"
          stroke="#F59E0B"
          strokeWidth="2"
          strokeDasharray="4 6"
          strokeOpacity="0.4"
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          style={{ originX: '90px', originY: '90px' }}
        />

        {/* Vintage Studio Mic */}
        <rect x="76" y="52" width="28" height="46" rx="14" fill="#FFFFFF" stroke="#0B1C30" strokeWidth="3.5" />
        <line x1="82" y1="64" x2="98" y2="64" stroke="#CBD5E1" strokeWidth="2" strokeLinecap="round" />
        <line x1="80" y1="74" x2="100" y2="74" stroke="#F59E0B" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="82" y1="84" x2="98" y2="84" stroke="#CBD5E1" strokeWidth="2" strokeLinecap="round" />

        <path d="M66 82C66 95.255 76.745 106 90 106C103.255 106 114 95.255 114 82" stroke="#0B1C30" strokeWidth="3.5" strokeLinecap="round" />
        <path d="M90 106V130" stroke="#0B1C30" strokeWidth="3.5" strokeLinecap="round" />
        <line x1="72" y1="130" x2="108" y2="130" stroke="#0B1C30" strokeWidth="4" strokeLinecap="round" />

        {/* Verified Voice Shield */}
        <circle cx="122" cy="62" r="14" fill="#10B981" />
        <path d="M117 62L121 66L127 58" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
};
