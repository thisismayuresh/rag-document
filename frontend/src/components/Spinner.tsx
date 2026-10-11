// Loading spinner. SVG has no conic gradient, so the fading tail is built
// from stacked, semi-transparent arcs of different lengths. Layer m
// (1..steps) covers tailAngle * m / steps degrees with opacity 1 / m, which
// makes the combined opacity fall off linearly from the head (fully opaque)
// to the tail (transparent).

import { useMemo } from "react";

export interface SpinnerProps {
  /** Rendered size in px (width and height). */
  size?: number;
  /** Stroke color of the arc and head. Any CSS color. */
  color?: string;
  /** Ring thickness, in viewBox units (viewBox is 100x100). */
  thickness?: number;
  /** Length of the visible tail in degrees (max 360). */
  tailAngle?: number;
  /** Seconds per full rotation. */
  duration?: number;
  /** Opacity of the faint background ring (0 to 1). */
  trackOpacity?: number;
  /** Number of stacked layers that make the gradient. More = smoother. */
  steps?: number;
  className?: string;
  /** Accessible label announced by screen readers. */
  label?: string;
}

const VIEWBOX = 100;
const CENTER = VIEWBOX / 2;

export function Spinner({
  size = 48,
  color = "currentColor",
  thickness = 10,
  tailAngle = 270,
  duration = 1,
  trackOpacity = 0.1,
  steps = 48,
  className,
  label = "Loading",
}: SpinnerProps) {
  const radius = CENTER - thickness / 2;
  const circumference = 2 * Math.PI * radius;

  const layers = useMemo(
    () =>
      Array.from({ length: steps }, (_, i) => {
        const m = i + 1;
        const angle = (tailAngle * m) / steps;
        return {
          key: m,
          dash: (circumference * angle) / 360,
          rotation: -angle,
          opacity: 1 / m,
        };
      }),
    [steps, tailAngle, circumference],
  );

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${VIEWBOX} ${VIEWBOX}`}
      className={className}
      role="status"
      aria-label={label}
    >
      {/* Static background ring */}
      <circle
        cx={CENTER}
        cy={CENTER}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={thickness}
        opacity={trackOpacity}
      />

      {/* Rotating arc + rounded head */}
      <g>
        <animateTransform
          attributeName="transform"
          type="rotate"
          from={`0 ${CENTER} ${CENTER}`}
          to={`360 ${CENTER} ${CENTER}`}
          dur={`${duration}s`}
          repeatCount="indefinite"
        />

        <g transform={`translate(${CENTER} ${CENTER})`}>
          {layers.map((l) => (
            <circle
              key={l.key}
              r={radius}
              fill="none"
              stroke={color}
              strokeWidth={thickness}
              strokeDasharray={`${l.dash} ${circumference}`}
              opacity={l.opacity}
              transform={`rotate(${l.rotation})`}
            />
          ))}
          {/* Rounded cap at the head (3 o'clock before rotation) */}
          <circle cx={radius} cy={0} r={thickness / 2} fill={color} />
        </g>
      </g>
    </svg>
  );
}
