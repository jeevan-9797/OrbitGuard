/**
 * Spacecraft Epoch & Time Utilities - Indian Standard Time (IST, UTC+05:30)
 */

export const IST_TIMEZONE = 'Asia/Kolkata';

/**
 * Returns HH:MM:SS in Indian Standard Time (IST)
 */
export function getISTTimeString(date: Date = new Date()): string {
  const timeStr = date.toLocaleTimeString('en-IN', {
    timeZone: IST_TIMEZONE,
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
  return `${timeStr} IST`;
}

/**
 * Returns HH:MM:SS.ms in Indian Standard Time (IST)
 */
export function getISTTimeWithMs(date: Date = new Date()): string {
  const timeStr = date.toLocaleTimeString('en-IN', {
    timeZone: IST_TIMEZONE,
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
  const ms = String(Math.floor(date.getMilliseconds() / 10)).padStart(2, '0');
  return `${timeStr}.${ms} IST`;
}

/**
 * Format a Date or ISO string into a standard IST timestamp string
 */
export function formatToIST(date: Date | string | number = new Date()): string {
  const d = typeof date === 'object' ? date : new Date(date);
  return d.toLocaleString('en-IN', {
    timeZone: IST_TIMEZONE,
    hour12: false,
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }) + ' IST';
}
