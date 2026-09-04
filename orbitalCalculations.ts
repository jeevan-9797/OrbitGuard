/**
 * Real-Time Astronomical & Orbital Mechanics Engine
 * Computes live Solar Beta (β) angle, Sun ECI vector, Earth rotation (GMST),
 * orbital plane precession (J2 regression of nodes), and eclipse fractions.
 */

export interface SolarBetaData {
  betaDeg: number;             // Current Solar Beta angle in degrees (-90 to +90)
  betaRad: number;
  sunlitFraction: number;      // 0 to 1 (fraction of orbit in direct sunlight)
  isFullSunlight: boolean;     // true if |beta| >= critical beta (no eclipse)
  criticalBetaDeg: number;     // e.g. ~67.2° for 541km altitude
  eclipseDurationMin: number;  // Minutes spent in Earth's shadow per orbit
  sunlightDurationMin: number; // Minutes spent in direct sunlight per orbit
  orbitPeriodMin: number;      // e.g. ~95.4 min
  dailyDriftDeg: number;       // Rate of change in beta (deg/day)
  nodalPrecessionDegPerDay: number; // J2 regression rate
  sunDeclinationDeg: number;   // Current Sun declination
  sunRightAscensionDeg: number;// Current Sun RA
  raanDeg: number;             // Current Right Ascension of Ascending Node
  sunVectorECI: [number, number, number]; // Unit vector to Sun in ECI
  orbitNormalECI: [number, number, number]; // Unit vector normal to orbit
  currentUtcIso: string;
  isCurrentlyInShadow: boolean; // Based on satellite true anomaly
}

// Earth & LEO Orbital Constants & Physical Gravitational Parameters
export const EARTH_MASS_KG = 5.9722e24; // Earth mass M = 5.9722 × 10^24 kg
export const SATELLITE_MASS_KG = 120.0; // Astra-7 satellite mass m = 120 kg
export const GRAVITATIONAL_CONSTANT_G = 6.6743e-11; // m^3 / (kg * s^2)
export const EARTH_RADIUS_KM = 6378.137;
export const SATELLITE_ALTITUDE_KM = 541.8;
export const ORBIT_SEMI_MAJOR_AXIS_KM = EARTH_RADIUS_KM + SATELLITE_ALTITUDE_KM; // 6919.937 km
export const ORBIT_INCLINATION_DEG = 51.64; // Standard LEO inclination
export const ORBIT_INCLINATION_RAD = (ORBIT_INCLINATION_DEG * Math.PI) / 180;

// Standard gravitational parameter mu = G * (M_earth + m_sat) in km^3/s^2
export const GM_EARTH = (GRAVITATIONAL_CONSTANT_G * (EARTH_MASS_KG + SATELLITE_MASS_KG)) / 1e9; // 398600.4418 km^3 / s^2

// Actual Physical Orbital Velocity (Keplerian Vis-Viva equation: v = sqrt(mu / r)):
export const PHYSICAL_ORBITAL_VELOCITY_KM_S = Math.sqrt(GM_EARTH / ORBIT_SEMI_MAJOR_AXIS_KM); // ~7.5898 km/s (Mach 22.3)

// Physical Mean Motion (Orbital Angular Velocity in rad/s: omega = sqrt(mu / r^3)):
export const PHYSICAL_ANGULAR_VELOCITY_RAD_S = Math.sqrt(
  GM_EARTH / Math.pow(ORBIT_SEMI_MAJOR_AXIS_KM, 3)
); // ~0.001096803 rad/s (0.06284 deg/s)

// Calculate orbital period in seconds: T = 2 * pi * sqrt(a^3 / mu) = 2 * pi / omega
export const ORBIT_PERIOD_SEC = (2 * Math.PI) / PHYSICAL_ANGULAR_VELOCITY_RAD_S; // ~5727.6 sec (~95.46 min)
export const ORBIT_PERIOD_MIN = ORBIT_PERIOD_SEC / 60;

// Physical Earth sidereal rotation rate relative to satellite orbit
// Earth completes 1 rotation in 86,164.1 s; satellite in 5,727.6 s -> ratio ~ 1 / 15.043
export const EARTH_TO_ORBIT_ROTATION_RATIO = ORBIT_PERIOD_SEC / 86164.1; // ~0.06647

// Calibrated Animation Scale:
// In raw real-time (1x), 1 orbit takes 95.46 minutes (too slow for human visual perception).
// Grounded in the actual mass of Earth, satellite mass, scale, and gravitational influence:
// A calibrated scale factor of 72x produces an elegant, stately orbital period of ~79.5 seconds per revolution (~0.079 rad/s),
// replacing the previous frantic 6.9-second cycle with majestic, physically authentic orbital motion.
export const GRAVITATIONAL_TIME_SCALE = 72;
export const CALIBRATED_ORBITAL_SPEED_RAD_S = PHYSICAL_ANGULAR_VELOCITY_RAD_S * GRAVITATIONAL_TIME_SCALE; // ~0.07897 rad/s

// Critical beta angle for 100% sunlight: beta* = arcsin(R_earth / r_sat)
export const CRITICAL_BETA_RAD = Math.asin(EARTH_RADIUS_KM / ORBIT_SEMI_MAJOR_AXIS_KM);
export const CRITICAL_BETA_DEG = (CRITICAL_BETA_RAD * 180) / Math.PI; // ~67.16°

// J2 Nodal Precession rate: dOmega/dt in deg/day
// dOmega/dt = -9.97 * (R_E / a)^(7/2) * cos(i) deg/day
export const NODAL_PRECESSION_DEG_PER_DAY =
  -9.97 * Math.pow(EARTH_RADIUS_KM / ORBIT_SEMI_MAJOR_AXIS_KM, 3.5) * Math.cos(ORBIT_INCLINATION_RAD); // ~ -5.23°/day

/**
 * Computes Julian Date from JavaScript Date object
 */
export function getJulianDate(date: Date): number {
  return date.getTime() / 86400000 + 2440587.5;
}

/**
 * Computes Greenwich Mean Sidereal Time (GMST) in radians [0, 2*PI)
 */
export function getGMST(date: Date): number {
  const jd = getJulianDate(date);
  const d = jd - 2451545.0; // days since J2000.0
  // GMST in degrees = 280.46061837 + 360.98564736629 * d
  let gmstDeg = (280.46061837 + 360.98564736629 * d) % 360;
  if (gmstDeg < 0) gmstDeg += 360;
  return (gmstDeg * Math.PI) / 180;
}

/**
 * Computes Sun Position in Earth-Centered Inertial (ECI) coordinate frame
 */
export function getSunPositionECI(date: Date): {
  vector: [number, number, number];
  declinationDeg: number;
  rightAscensionDeg: number;
} {
  const jd = getJulianDate(date);
  const n = jd - 2451545.0; // Days since J2000.0

  // Mean longitude of the Sun (degrees)
  let L = (280.46 + 0.9856474 * n) % 360;
  if (L < 0) L += 360;

  // Mean anomaly of the Sun (degrees)
  let g = (357.528 + 0.9856003 * n) % 360;
  if (g < 0) g += 360;
  const gRad = (g * Math.PI) / 180;

  // Ecliptic longitude (degrees)
  const lambdaDeg = L + 1.915 * Math.sin(gRad) + 0.02 * Math.sin(2 * gRad);
  const lambdaRad = (lambdaDeg * Math.PI) / 180;

  // Obliquity of the ecliptic (degrees)
  const epsilonDeg = 23.439 - 0.0000004 * n;
  const epsilonRad = (epsilonDeg * Math.PI) / 180;

  // Sun unit vector in ECI
  const sx = Math.cos(lambdaRad);
  const sy = Math.cos(epsilonRad) * Math.sin(lambdaRad);
  const sz = Math.sin(epsilonRad) * Math.sin(lambdaRad);

  const declinationRad = Math.asin(sz);
  let raRad = Math.atan2(sy, sx);
  if (raRad < 0) raRad += 2 * Math.PI;

  return {
    vector: [sx, sy, sz],
    declinationDeg: (declinationRad * 180) / Math.PI,
    rightAscensionDeg: (raRad * 180) / Math.PI,
  };
}

/**
 * Computes RAAN (Right Ascension of Ascending Node) for satellite based on epoch and J2 precession
 */
export function getSatelliteRAAN(date: Date, epochRaanDeg = 78.4, epochDate = new Date('2026-01-01T00:00:00Z')): number {
  const daysSinceEpoch = (date.getTime() - epochDate.getTime()) / (1000 * 86400);
  let currentRaan = (epochRaanDeg + NODAL_PRECESSION_DEG_PER_DAY * daysSinceEpoch) % 360;
  if (currentRaan < 0) currentRaan += 360;
  return currentRaan;
}

/**
 * Comprehensive Solar Beta and Eclipse analysis
 */
export function calculateSolarBeta(
  date: Date,
  satelliteTrueAnomalyRad = 0,
  manualRaanOffsetDeg = 0
): SolarBetaData {
  const sunInfo = getSunPositionECI(date);
  const raanDeg = (getSatelliteRAAN(date) + manualRaanOffsetDeg) % 360;
  const raanRad = (raanDeg * Math.PI) / 180;

  // Orbit plane unit normal vector n_hat in ECI
  // n_x = sin(RAAN) * sin(i)
  // n_y = -cos(RAAN) * sin(i)
  // n_z = cos(i)
  const nx = Math.sin(raanRad) * Math.sin(ORBIT_INCLINATION_RAD);
  const ny = -Math.cos(raanRad) * Math.sin(ORBIT_INCLINATION_RAD);
  const nz = Math.cos(ORBIT_INCLINATION_RAD);

  // Dot product: sin(beta) = n_hat . s_hat
  const sinBeta = nx * sunInfo.vector[0] + ny * sunInfo.vector[1] + nz * sunInfo.vector[2];
  const clampedSinBeta = Math.max(-1, Math.min(1, sinBeta));
  const betaRad = Math.asin(clampedSinBeta);
  const betaDeg = (betaRad * 180) / Math.PI;

  // Determine shadow / eclipse characteristics
  const isFullSunlight = Math.abs(betaDeg) >= CRITICAL_BETA_DEG;

  let shadowFraction = 0;
  if (!isFullSunlight) {
    const cosBeta = Math.max(0.0001, Math.cos(betaRad));
    const shadowParam = Math.sqrt(1 - Math.pow(EARTH_RADIUS_KM / ORBIT_SEMI_MAJOR_AXIS_KM, 2)) / cosBeta;
    if (shadowParam < 1) {
      const thetaShadow = Math.acos(shadowParam); // half-angle of shadow arc
      shadowFraction = (2 * thetaShadow) / (2 * Math.PI);
    }
  }

  const eclipseDurationMin = shadowFraction * ORBIT_PERIOD_MIN;
  const sunlightDurationMin = ORBIT_PERIOD_MIN - eclipseDurationMin;
  const sunlitFraction = 1 - shadowFraction;

  // Rate of change in beta (deg/day) by sampling +1 hour
  const futureDate = new Date(date.getTime() + 3600 * 1000);
  const futureSun = getSunPositionECI(futureDate);
  const futureRaanRad = ((raanDeg + NODAL_PRECESSION_DEG_PER_DAY / 24) * Math.PI) / 180;
  const fnx = Math.sin(futureRaanRad) * Math.sin(ORBIT_INCLINATION_RAD);
  const fny = -Math.cos(futureRaanRad) * Math.sin(ORBIT_INCLINATION_RAD);
  const fnz = Math.cos(ORBIT_INCLINATION_RAD);
  const futureSinBeta = fnx * futureSun.vector[0] + fny * futureSun.vector[1] + fnz * futureSun.vector[2];
  const futureBetaDeg = (Math.asin(Math.max(-1, Math.min(1, futureSinBeta))) * 180) / Math.PI;
  const dailyDriftDeg = (futureBetaDeg - betaDeg) * 24;

  // Check if satellite's instantaneous position is currently in Earth's shadow cone
  // Satellite position in orbital plane:
  // p_orbit = [cos(u), sin(u), 0]
  // In ECI: rotate by argument of perigee (assume circular ~ 0), inclination, RAAN
  const u = satelliteTrueAnomalyRad;
  const satX = Math.cos(u) * Math.cos(raanRad) - Math.sin(u) * Math.sin(raanRad) * Math.cos(ORBIT_INCLINATION_RAD);
  const satY = Math.cos(u) * Math.sin(raanRad) + Math.sin(u) * Math.cos(raanRad) * Math.cos(ORBIT_INCLINATION_RAD);
  const satZ = Math.sin(u) * Math.sin(ORBIT_INCLINATION_RAD);

  // Satellite distance along Sun vector: projection = sat . s_hat
  const satDotSun = satX * sunInfo.vector[0] + satY * sunInfo.vector[1] + satZ * sunInfo.vector[2];
  let isCurrentlyInShadow = false;
  if (satDotSun < 0) {
    // Behind Earth relative to Sun
    // Perpendicular distance from Earth-Sun centerline:
    // d_perp^2 = r_sat^2 - (sat . s_hat)^2
    const distSq = 1 - satDotSun * satDotSun;
    const perpKm = Math.sqrt(distSq) * ORBIT_SEMI_MAJOR_AXIS_KM;
    if (perpKm < EARTH_RADIUS_KM) {
      isCurrentlyInShadow = true;
    }
  }

  return {
    betaDeg,
    betaRad,
    sunlitFraction,
    isFullSunlight,
    criticalBetaDeg: CRITICAL_BETA_DEG,
    eclipseDurationMin,
    sunlightDurationMin,
    orbitPeriodMin: ORBIT_PERIOD_MIN,
    dailyDriftDeg,
    nodalPrecessionDegPerDay: NODAL_PRECESSION_DEG_PER_DAY,
    sunDeclinationDeg: sunInfo.declinationDeg,
    sunRightAscensionDeg: sunInfo.rightAscensionDeg,
    raanDeg,
    sunVectorECI: sunInfo.vector,
    orbitNormalECI: [nx, ny, nz],
    currentUtcIso: date.toISOString(),
    isCurrentlyInShadow,
  };
}
