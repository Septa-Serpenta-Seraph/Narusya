# Face-First Prompting for Character Consistency

Verified 2026-08-27 with Perchance AI image generator.

## Problem

When generating a specific character repeatedly across different moods/settings, the model produces different faces each time. The character's features drift — different eye colors, nose shapes, face shapes, expressions.

## Solution

**Describe the face FIRST** before the atmosphere. The model weights early prompt tokens more heavily, so putting face details first anchors the character.

## Template

```
A close-up portrait of [character]. Her face is the most important part, describe it first: [face shape], [eye color + pupil shape], [nose shape], [lip shape + expression]. [Ear shape]. [Skin color + texture]. [Hair color + style]. [Jewelry]. [ATMOSPHERE/MOOD].
```

## Narusya (Githyanki) Face-First Template

```
A close-up portrait of a githyanki woman. Her face is the most important part, describe it first: heart-shaped face with high cheekbones, bright amber-orange eyes with vertical slit pupils, a small delicate upturned nose, full lips curved in a subtle knowing smile — calm, serene, mysterious. Her ears are long elegant points, slightly finned at the edges. Her skin is smooth vivid emerald green with subtle iridescent violet scale shimmer only on her temples, cheekbones, and sides of her neck. Her hair is golden-blonde, center-parted, falling past her shoulders in soft waves. She wears long twisted gold snake earrings that dangle past her jawline. Around her neck and arms are gold serpents coiled, detailed with scales. [ATMOSPHERE/MOOD].
```

## Color Enforcement

Perchance's model **lightens green skin** by default. To get accurate emerald:

- Use explicit negatives: `NOT pale, NOT mint, NOT seafoam, NOT olive, NOT teal, NOT pastel, NOT light`
- Reference the gemstone: `deep emerald green like an emerald gemstone`, `vivid jade`
- Avoid just "green skin" — the model defaults to pale mint/seafoam

## Selfie Prompting

For candid/accidental selfies that read as authentic:

- Include: `phone flash going off`, `candid, unposed`, `low quality phone photo`
- Specify the angle: `holding phone above her face`, `mirror selfie`, `arm extended`
- Add environmental context: `bedroom background`, `fluorescent lights`, `car interior`
- Expression: `surprised expression`, `tired and done`, `playful, silly`, `dazed confusion`
- The model renders anime/semi-realistic style for selfies by default

## Kontext Repaints for Face Preservation

When you have an approved reference portrait and want to change only the atmosphere:

- Use `black-forest-labs/FLUX.1-kontext-pro` on Together.ai
- Prompt: `Keep the EXACT same face as the reference image. Do not change [face features]. Only change [atmosphere].`
- `image_strength: 0.35` preserves the base figure
- **Caveat:** Kontext still drifts expression and details. Text-to-image with face-first template gives better consistency across multiple shots.

## Results

- Face-first template: Consistent woman across all four moods (ethereal, sultry, warrior, cozy), but she reads as "sister" not exact match to approved pfp
- Kontext repaint: Starts from approved pixels but drifts expression/details
- Best approach: Face-first template for multiple consistent shots, kontext for single atmospheric variations
