# Physics Verification Reference: Mecha/Airship Feasibility

Real calculations performed during the Cultus Anarchia document consolidation (July 2026).
Use these as reference patterns for verifying fictional engineering claims.

## HALO / High-Altitude Mecha Drop

### The Problem
An 18-ton (16,330 kg) mecha in an aerodynamic pod dropped from 15,000 ft with retro-rockets
firing at 800 ft. Is this survivable?

### Terminal Velocity
```
v_t = sqrt(2 * m * g / (ρ * Cd * A))
```
- m = 16,330 kg (18 US short tons)
- g = 9.81 m/s²
- ρ = air density at altitude (0.77 kg/m³ at 15k ft, 1.19 at 800 ft)
- Cd = 0.35 (aerodynamic pod fairing)
- A = π × (3.5/2)² = 9.62 m² (pod cross-section)

Result: v_t ≈ 297-369 m/s (664-826 mph) depending on altitude.

### Does the pod reach terminal velocity before 800 ft?
- Time to terminal: v_t / g ≈ 35 seconds
- Distance to terminal: 0.5 × v_t × t ≈ 5,939 m
- Available fall distance: 15,000 - 800 = 14,200 ft = 4,328 m
- Pod does NOT fully reach terminal velocity, but gets close (~340 m/s)

### Deceleration at 800 ft with rockets only
```
a = (v₀² - v²) / (2 × d)
```
- v₀ = 340 m/s, v = 5 m/s, d = 244 m (800 ft)
- a = 238.7 m/s² = 24.3 G
- **VERDICT: FATAL.** 24.3 G exceeds human tolerance (9 G max with restraints, 15 G for <3 sec).

### Working Solution: Multi-Stage Deceleration (Archangel Drop)
1. Free fall 15,000 → 5,000 ft (terminal velocity ~340 m/s)
2. Drogue parachute at 5,000 ft → slows to 80 m/s (0.5 G deceleration)
3. Main parachutes at 1,500 ft → slows to 8 m/s (0.3 G)
   - 3 canopies, ~64m diameter each, ~3,200 m² total
   - Area check: A = 2mg / (ρ·Cd·v²) = 2×16330×9.81/(1.15×1.5×64) ≈ 3,199 m² ✓
4. Retro-rockets at 100 ft → slows to 3 m/s (0.1 G)
   - Propellant needed: ~250 kg (only for final 8→3 m/s burn)

Total descent: ~90 seconds. All deceleration phases under 1 G. Pilot survives.

### Unmanned Variant
Drop mecha without pilot. Machine can survive 20+ G. Drop empty with full multi-stage
system (or even just rockets at 800 ft — no human to kill). Pilot does conventional human
HALO separately (free fall → parachute at 3,000 ft → 5 m/s landing). Sync on ground.

## Airship Lift Capacity

### Leviathan-Class (310m × 50m ellipsoid)
- Envelope volume: (4/3) × π × 25² × 155 ≈ 405,789 m³
- Helium lift at sea level: ~1.047 kg/m³
- Gross lift: 405,789 × 1.047 ≈ 424,860 kg
- Structure estimate: ~200,000 kg (carbon-nanotube composite, titanium, skin, systems)
- Usable payload: ~224,860 kg (225 tons)
- Claimed payload: 7 × 18 tons = 126 tons → ✓ (1.8x margin)
- Service ceiling with full payload: ~8,000 ft (above this, lift drops below threshold)

### Comparison Points
| Airship | Length | Volume | Lift |
|---|---|---|---|
| Pathfinder 1 (real) | 120 m | 28,000 m³ | ~29 tons |
| Airlander 10 (real) | 92 m | 38,000 m³ | ~40 tons |
| Hindenburg (real) | 245 m | 200,000 m³ | ~210 tons |
| LCA60T (real, planned) | 200 m | ~50,000 m³ | 60 tons |
| Leviathan (fictional) | 310 m | 405,789 m³ | ~225 tons |

## VCDS Buoyancy Exchange

### Equation
```
ΔV = M_mech / (ρ_air - ρ_He)
```
- M = 16,330 kg, ρ_air = 1.225, ρ_He = 0.178
- ΔV = 16,330 / (1.225 - 0.178) = 15,727 m³

### Compression
- At 10,000 PSI: He density ~100 kg/m³, compression ratio ~562x
- 15,727 m³ → ~28 m³ compressed (fits in ~2m radius spheres)
- Two-stage: pre-charge to 2,000 PSI (140x), then full to 10,000 PSI (562x)

### Flow Rate
- 15,727 m³ in 0.8 seconds = 19,659 m³/s
- vs largest industrial compressors (~10,000 m³/min = 167 m³/s)
- Requires ~118x industrial capacity → achieved by repurposing 64 superconducting turbines

### Air Intake
- Vent velocity at 0.5 atm ΔP: ~286 m/s (near-sonic)
- Required vent area: Q / (Cd × v) ≈ 125 m² (11m × 11m opening)
- For a 310m airship: feasible
- 200ms valve opening time: aggressive but feasible for this scale

## Mecha Scale Reference

| Real-World Mech | Height | Weight |
|---|---|---|
| Boston Dynamics Atlas | 1.88 m | 80 kg |
| Method-2 (South Korea) | 4.0 m | 1,500 kg |
| Prosthesis (Greathouse) | 4.5 m | 3,000 kg |
| M2 Bradley (IFV, not bipedal) | 3.0 m | 27,000 kg |
| Tiger I tank (not bipedal) | 3.0 m | 54,000 kg |
| **Titan-Class (fictional)** | **6.5 m** | **18,000 kg** |

An 18-ton biped at 6.5m is plausible weight-wise (lighter than a Bradley) but top-heavy.
Requires active balance compensation (Bullsnake dampeners).

## Human G-Tolerance Reference

| G-force | Duration | Effect |
|---|---|---|
| 1 G | indefinite | Normal gravity |
| 3-5 G | sustained | Untrained person greys/blacks out |
| 9 G | sustained | Trained pilot with G-suit, max sustained |
| 12 G | <3 seconds | Survivable with full restraints + dampeners |
| 15 G | <3 seconds | Upper limit of gyroscopic pod tolerance |
| 20+ G | any | Fatal — organ damage, internal hemorrhaging |
| 24.3 G | any | **Fatal** — original HALO drop as written |
