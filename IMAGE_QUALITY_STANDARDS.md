# Face-Sense Image Quality Standards

This document outlines the standards and guidelines for input images used in the Face-Sense facial recognition system. Following these guidelines will ensure optimal recognition accuracy while maintaining system performance on lightweight CPU machines.

## Image Quality Factors

The Face-Sense system evaluates image quality based on three key factors:

1. **Face Size** (40% of quality score)
   - Optimal face size is 30-70% of the total image area
   - Larger faces provide more detail for recognition
   - Too large (>80%) may cut off facial features
   - Too small (<20%) lacks sufficient detail

2. **Blur Detection** (40% of quality score)
   - Measured using Laplacian variance
   - Sharp images have higher variance values
   - Blurry images significantly reduce recognition accuracy

3. **Lighting Conditions** (20% of quality score)
   - Measured using histogram standard deviation
   - Even, well-lit faces provide better recognition
   - Avoid harsh shadows or overexposure
   - Moderate contrast is ideal

## Image Requirements

### Essential Requirements

- **Resolution**: Minimum 640x480, preferred 1280x720 or higher
- **Format**: JPG recommended (PNG also supported)
- **Face Position**: Centered, forward-facing
- **Expression**: Neutral expression preferred
- **Accessories**: Avoid sunglasses; regular glasses are acceptable
- **File Size**: Less than 5MB per image

### Optimal Conditions

- **Background**: Plain, contrasting background
- **Lighting**: Even, diffused lighting (avoid harsh shadows)
- **Distance**: Subject should be 2-3 feet from camera
- **Face Angle**: Direct frontal view (±15° acceptable)
- **Eyes**: Open and clearly visible
- **Framing**: Head and upper shoulders visible

## Multiple Image Strategy

For optimal recognition accuracy, we recommend providing multiple images per person:

1. **Primary Image**: High-quality frontal face shot under ideal conditions
2. **Secondary Images** (optional but recommended):
   - Different angles (±15°)
   - Different lighting conditions
   - Different expressions (slight smile, neutral)
   - Different backgrounds

The system will automatically generate variations from these images to improve recognition across different conditions.

## Quality Score Impact

Images with higher quality scores provide several benefits:

1. **Higher Recognition Confidence**: Quality scores directly influence the weighted accuracy calculation
2. **Adaptive Thresholds**: Higher quality reference images allow for more precise matching
3. **Better Variation Generation**: The system creates better encoding variations from high-quality source images

## Common Issues to Avoid

1. **Motion Blur**: Ensure the subject is stationary when taking the photo
2. **Poor Lighting**: Avoid backlighting, harsh shadows, or dim conditions
3. **Occlusion**: Ensure the face is not partially covered by hair, hands, or objects
4. **Extreme Angles**: Avoid profile views or extreme tilting
5. **Heavy Makeup**: Can alter facial features and reduce recognition accuracy
6. **Digital Artifacts**: Avoid highly compressed or previously processed images

## Technical Specifications

- **Aspect Ratio**: 4:3 or 16:9 preferred
- **Color Space**: RGB
- **Bit Depth**: 24-bit color
- **Compression**: Moderate JPEG compression (quality 80% or higher)

Following these guidelines will ensure optimal performance of the Face-Sense system while maintaining efficiency on CPU-based machines.

