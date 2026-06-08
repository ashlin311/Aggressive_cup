---
name: Football Foul Fest
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#3a3939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#e6bdb8'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#ac8884'
  outline-variant: '#5c403c'
  surface-tint: '#ffb4ab'
  primary: '#ffb4ab'
  on-primary: '#690005'
  primary-container: '#dc2626'
  on-primary-container: '#fff6f5'
  inverse-primary: '#bf0715'
  secondary: '#ffe083'
  on-secondary: '#3c2f00'
  secondary-container: '#eec200'
  on-secondary-container: '#645000'
  tertiary: '#ffb4ac'
  on-tertiary: '#690007'
  tertiary-container: '#cb403a'
  on-tertiary-container: '#fff6f4'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad6'
  primary-fixed-dim: '#ffb4ab'
  on-primary-fixed: '#410002'
  on-primary-fixed-variant: '#93000b'
  secondary-fixed: '#ffe083'
  secondary-fixed-dim: '#eec200'
  on-secondary-fixed: '#231b00'
  on-secondary-fixed-variant: '#574500'
  tertiary-fixed: '#ffdad6'
  tertiary-fixed-dim: '#ffb4ac'
  on-tertiary-fixed: '#410002'
  on-tertiary-fixed-variant: '#8e1214'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '900'
    lineHeight: '1.1'
    letterSpacing: 0.05em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '800'
    lineHeight: '1.2'
    letterSpacing: 0.025em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '800'
    lineHeight: '1.2'
    letterSpacing: 0.025em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '800'
    lineHeight: '1.2'
    letterSpacing: 0.025em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.1em
  stats-number:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '900'
    lineHeight: '1'
    letterSpacing: -0.02em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  container-margin: 24px
  gutter: 16px
  section-gap: 48px
  component-padding-x: 16px
  component-padding-y: 12px
---

## Brand & Style

The design system is engineered to capture the high-stakes adrenaline of elite professional sports broadcasting, filtered through a lens of chaos and aggression. It prioritizes intensity and impact, treating every foul and card as a headline event. The aesthetic is "Aggressive Broadcast"—combining the precision of modern sports telemetry with the raw energy of a stadium under floodlights.

The target audience consists of hardcore football enthusiasts and data-driven fans who appreciate the "darker" side of the game. The UI should evoke an emotional response of urgency, tension, and authority. This is achieved through a **High-Contrast / Bold** style that utilizes deep shadows, vibrant signals, and a relentless focus on the hierarchy of the pitch.

## Colors

The palette is rooted in the "Red Card / Yellow Card" disciplinary system of football.
- **Deep Neutral (#0a0a0a):** The "pitch at night." Used for backgrounds to make all other data points pop with maximum intensity.
- **Vibrant Red (#dc2626):** The primary action color. Represents Red Cards, critical errors, and high-urgency interactions.
- **Cautionary Yellow (#facc15):** The secondary signal. Used for scores, Yellow Card warnings, and secondary highlights to ensure visibility against the dark base.
- **Dark Red (#991b1b):** Used for structural accents, hover states on primary actions, and "blood" zones in the UI to maintain the aggressive tone without overwhelming the eye.
- **Light Grey (#d1d5db):** Dedicated to body text to ensure high readability while maintaining the dark atmosphere.

## Typography

This design system uses **Inter** across all roles to maintain a systematic, robust feel. 

**Headings:** All headings must be uppercase with expanded letter spacing to mimic broadcast graphics. Weight should never drop below 800 (Extra Bold) for display elements.
**Body:** Body text uses a standard sentence case for maximum readability in data-heavy sections. The light grey color reduces eye strain against the black background.
**Labels:** Small utility text should be bold and uppercase to differentiate it from data values.
**Stats:** Numbers related to score or foul counts should use the `stats-number` role, which features tight letter spacing and heavy weight to emphasize the data.

## Layout & Spacing

The layout follows a **Fixed Grid** model for desktop to maintain the tight, controlled feel of a broadcast monitor.
- **Grid:** 12-column system with 16px gutters.
- **Rhythm:** A 4px baseline grid ensures all elements align vertically.
- **Breakpoints:** 
  - *Mobile:* Single column, 16px margins. 
  - *Tablet:* 8-column, 20px margins.
  - *Desktop:* 12-column, 24px margins, max-width 1280px.

Spacing should be used aggressively to group related "incident" data. Use large `section-gap` values to separate different matches or event categories, while keeping internal component padding tight to increase the perceived density of the "chaos."

## Elevation & Depth

This design system avoids soft, ambient shadows in favor of **Tonal Layers** and **Bold Outlines**.
- **Surface Layering:** The primary background is `#0a0a0a`. "Cards" or containers use a slightly elevated surface of `#171717`.
- **Inner Glows:** To simulate a backlit screen, critical elements (like a Red Card alert) should use a subtle 1px internal border in a brighter tint of the primary color.
- **Hard Shadows:** If depth is required for stacked elements, use 100% opacity shadows with 0 blur, offset by 4px to create a "cutout" broadcast effect.
- **Dividers:** Use 1px solid `#262626` (Neutral 800) for structural division.

## Shapes

The shape language is industrial and sharp. A "Soft" (`0.25rem`) corner radius is the maximum allowed to prevent the UI from feeling too "friendly." This slight rounding prevents the interface from looking dated while maintaining an aggressive, technical edge.
- **Buttons & Inputs:** 4px (0.25rem) radius.
- **Large Cards:** 8px (0.5rem) radius.
- **Disciplinary Cards:** Must remain 0px (Sharp) to mimic the actual physical cards used by referees.

## Components

- **Buttons:** 
  - *Primary:* Solid `#dc2626` background, white text, bold uppercase.
  - *Secondary:* Transparent with a 2px `#facc15` border.
- **Incident Cards:** High-contrast containers with a thick (4px) left-side border indicating the card color (Yellow/Red). Use emoji flags for nationality (e.g., 🏴󠁧󠁢󠁥󠁮󠁧󠁿, 🇧🇷) next to player names.
- **Foul Counters:** Circular badges using `stats-number` typography, utilizing the cautionary yellow for visibility.
- **Lists:** Zebra-striping is forbidden. Use 1px dividers. Hover states should use a dark red (`#991b1b`) subtle background tint.
- **Inputs:** Dark backgrounds (`#000000`) with a 1px `#404040` border that turns `#dc2626` on focus.
- **Chips/Tags:** Small, sharp-cornered blocks of color. Red for "Serious Foul Play," Yellow for "Tactical Foul."