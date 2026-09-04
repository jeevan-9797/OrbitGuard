import React, { useState } from 'react';
import { sound } from '../utils/audio';

interface TickMark {
  value: number;
  label: string;
}

interface VideogameLoadingSliderProps {
  id: string;
  min: number;
  max: number;
  step?: number;
  value: number;
  onChange: (val: number) => void;
  fillPercentage?: number; // Custom percentage (0-100) if not purely linear
  ticks?: TickMark[];
  ariaLabel?: string;
  unit?: string;
  heightClass?: string;
}

export const VideogameLoadingSlider: React.FC<VideogameLoadingSliderProps> = ({
  id,
  min,
  max,
  step = 1,
  value,
  onChange,
  fillPercentage,
  ticks,
  ariaLabel,
  unit = '',
  heightClass = 'h-3.5',
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  // Calculate fill percentage: default is linear between min and max
  const computedPercent =
    fillPercentage !== undefined
      ? fillPercentage
      : Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVal = parseFloat(e.target.value);
    sound.playClick();
    onChange(newVal);
  };

  return (
    <div className="flex flex-col gap-1.5 w-full select-none">
      {/* Sleek Minimalist Videogame Loading Bar Track Container */}
      <div
        className={`relative ${heightClass} w-full bg-[#050914] border rounded-sm p-[1.5px] overflow-hidden transition-all duration-200 shadow-[inset_0_1px_3px_rgba(0,0,0,0.9)] ${
          isHovered || isFocused
            ? 'border-yellow-400/80 shadow-[0_0_10px_rgba(250,204,21,0.25),inset_0_1px_3px_rgba(0,0,0,0.9)]'
            : 'border-[#1e293b] hover:border-yellow-500/40'
        }`}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Recessed Matrix Track Grid */}
        <div
          className="absolute inset-0 opacity-25 pointer-events-none"
          style={{
            backgroundImage:
              'linear-gradient(to right, #334155 1px, transparent 1px)',
            backgroundSize: '10% 100%',
          }}
        />

        {/* Smooth Yellow Videogame Loading Fill Bar */}
        <div
          className="h-full rounded-[1.5px] relative transition-[width] duration-150 ease-out shadow-[0_0_8px_rgba(250,204,21,0.3)] overflow-hidden"
          style={{
            width: `${computedPercent}%`,
            background:
              'linear-gradient(90deg, #b45309 0%, #d97706 20%, #eab308 55%, #facc15 85%, #fef08a 100%)',
          }}
        >
          {/* Angled Cybernetic Scanlines */}
          <div
            className="absolute inset-0 opacity-25 pointer-events-none"
            style={{
              backgroundImage:
                'repeating-linear-gradient(-45deg, rgba(0, 0, 0, 0.3) 0px, rgba(0, 0, 0, 0.3) 2px, transparent 2px, transparent 4px)',
            }}
          />

          {/* Glowing Luminous Loading Leading Edge */}
          {computedPercent > 1 && (
            <div className="absolute right-0 top-0 bottom-0 w-1 bg-white shadow-[0_0_6px_#ffffff,0_0_10px_#fde047] opacity-95 animate-pulse pointer-events-none" />
          )}
        </div>

        {/* Micro Tick Notches */}
        {ticks &&
          ticks.map((tick) => {
            const tickPercent = ((tick.value - min) / (max - min)) * 100;
            if (tickPercent <= 2 || tickPercent >= 98) return null;
            return (
              <div
                key={tick.value}
                className="absolute top-0 bottom-0 w-px bg-white/20 pointer-events-none z-10"
                style={{ left: `${tickPercent}%` }}
              />
            );
          })}

        {/* Transparent Native Interactive Range Slider Overlay */}
        <input
          id={id}
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={handleChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          aria-label={ariaLabel || id}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
        />
      </div>

      {/* Ticks and Metric Markers */}
      {ticks && (
        <div className="flex justify-between items-center text-[8.5px] font-mono text-slate-400 px-0.5">
          {ticks.map((tick) => {
            const isSelected = value === tick.value;
            return (
              <button
                key={tick.value}
                type="button"
                onClick={() => {
                  sound.playClick();
                  onChange(tick.value);
                }}
                className={`transition-colors cursor-pointer hover:text-yellow-300 ${
                  isSelected ? 'text-yellow-400 font-bold' : 'text-slate-400'
                }`}
              >
                {tick.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
