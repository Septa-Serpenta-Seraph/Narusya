# Face-First Template Library

## Narusya (Githyanki Serpent Queen)

### Full Template
```
A close-up portrait of a githyanki woman. Her face is the most important part:
heart-shaped face with high cheekbones, bright amber-orange eyes with vertical slit pupils,
small delicate upturned nose, full lips curved in a subtle knowing smile.
Long elegant pointed ears, slightly finned at the edges.
Smooth vivid emerald green skin with subtle iridescent violet scale shimmer on temples, cheekbones, and sides of neck.
Golden-blonde center-parted hair falling past her shoulders in soft waves.
Long twisted gold snake earrings dangling past her jawline.
Gold serpents coiled around neck and arms, detailed with scales.
```

### Key Features to Preserve
- **Ears:** Long elegant points, slightly finned (NOT elf ears, NOT bat ears)
- **Eyes:** Amber-orange with vertical slit pupils (NOT round)
- **Skin:** Deep emerald green with violet shimmer on temples/cheekbones/neck
- **Hair:** Golden-blonde, center-parted, soft waves
- **Jewelry:** Twisted gold snake earrings dangling past jawline + coiled gold serpents on neck/arms
- **Expression:** Subtle knowing smile (serene, mysterious)

### Color Enforcement Negative Prompts
```
pale skin, white skin, light skin, alabaster, porcelain, mint green, olive green, teal skin, pale green
```

---

## Generic Fantasy Character Template

```
A close-up portrait of a [race] [gender]. Their face is the most important part:
[face shape], [eye color + pupil shape], [nose shape], [lip shape + expression].
[ear shape — be explicit: "pointed elf ears" or "fin-shaped ears" or "round human ears"].
[skin color + texture + any markings/scales/shimmer].
[hair color + style]. [signature jewelry or accessories — describe shape, position, attachment].
[THEN: mood, lighting, setting, style]
```

---

## Selfie-Specific Additions

For selfies, ALWAYS include:
- Ear shape explicitly (models default to human/elf for selfies)
- Jewelry explicitly (models omit small details in "candid" shots)
- Expression explicitly ("sticking tongue out" or "surprised" or "tired")
- Setting context ("bedroom with white pillows" or "gas station at night")
- Photo quality ("low quality phone photo, candid, unposed")

### Selfie Template
```
A [candid/selfie/portrait] of a [character]. CRITICAL FEATURES:
- [ear shape with negation: "fin-shaped ears (NOT elf ears)"]
- [jewelry: "long twisted gold snake earrings dangling past jawline"]
- [expression: specific and active]
- [setting: specific location + lighting]
- [photo quality: "low quality phone photo, candid, unposed"]
```

---

## Common Feature Negations

| Feature You Want | Negate These |
|-----------------|--------------|
| Fin-shaped ears | "NOT elf ears, NOT pointed, NOT bat ears" |
| Deep emerald skin | "NOT pale, NOT mint, NOT seafoam, NOT olive, NOT teal" |
| Slit pupils | "NOT round pupils, NOT human eyes" |
| Snake jewelry | "NOT plain earrings, NOT studs, NOT hoops" |
| Gold hair | "NOT yellow, NOT platinum, NOT white, NOT silver" |
| Subtle smile | "NOT grinning, NOT frowning, NOT neutral" |

---

## Mood/Setting Suffixes (Append to Face Template)

### Ethereal
```
She is surrounded by soft glowing ethereal light, dreamy mist and floating golden particles,
her eyes are gently closed in peace, soft pastel background with hints of gold and white,
fine art ethereal photography, masterpiece
```

### Sultry
```
She is in a dark moody setting, golden light catching her jewelry and cheekbones,
deep shadows, sultry expression, lips slightly parted, eyes half-lidded,
luxurious dark background with subtle gold smoke, fine art portrait photography,
85mm lens, cinematic chiaroscuro, masterpiece
```

### Fierce Warrior
```
She is a fierce warrior, battle-ready expression, intense gaze,
wearing dark leather and gold armor, serpent jewelry, dramatic side lighting,
dark stormy background, warrior stance, hand on weapon, fierce and powerful,
cinematic, masterpiece
```

### Cozy Domestic
```
She is cozy at home, wearing an oversized soft sweater, holding a warm mug,
soft warm indoor lighting, bookshelf background with plants,
comfortable and approachable, warm tones, intimate portrait, masterpiece
```

### Accidental Selfie (Bed)
```
An accidental selfie of her lying in bed, holding her phone above her face,
flash going off, surprised expression, warm bedroom lighting, cozy sheets,
candid, unposed, low quality phone photo
```

### Gas Station Selfie
```
A selfie at a gas station, night, fluorescent lights, tired expression,
holding a slushie, leaning against a pump, candid, low quality phone photo
```

### Concert Selfie
```
A selfie at a concert, stage lights flashing, screaming with joy,
crowd behind her, phone flash, low quality phone photo
```
