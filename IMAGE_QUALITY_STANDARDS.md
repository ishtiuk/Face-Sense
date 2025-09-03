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

## Single Image Strategy

**One high-quality image per person is sufficient** for optimal recognition accuracy:

1. **Primary Image**: High-quality frontal face shot under ideal conditions
2. **Automatic Variation Generation**: The system automatically creates 5+ variations from this single image
3. **Smart Processing**: Variations include different expressions, angles, and lighting conditions
4. **Efficient Storage**: Single input image generates comprehensive recognition model

The system intelligently generates all necessary variations automatically, eliminating the need for multiple input images.

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

## 📋 **Best Practices for Optimal Recognition**

### **Image Collection Strategy**
1. **Single High-Quality Image**: One clear, well-lit photo per person is sufficient
2. **Automatic Variation Generation**: System automatically creates 5+ variations from single input
3. **Consistent Formatting**: Use consistent naming convention and image dimensions
4. **Regular Updates**: Refresh reference images periodically for better accuracy

### **System Configuration Tips**
1. **Cooldown Settings**: Adjust detection cooldown based on your use case (default: 5 seconds)
2. **Quality Thresholds**: Monitor quality scores and adjust recognition sensitivity as needed
3. **Memory Management**: System automatically cleans up expired cooldown entries
4. **Performance Monitoring**: Watch for system status updates in the web interface

### **Maintenance Recommendations**
1. **Database Cleanup**: Periodically clean old attendance records for optimal performance
2. **Model Updates**: Re-run encoding when adding new employees or updating photos
3. **Quality Monitoring**: Track recognition accuracy and adjust image quality as needed
4. **System Logs**: Monitor console output for detection and quality information

## 🎯 **Expected Performance Metrics**

With properly configured images following these standards:
- **Recognition Accuracy**: 95%+ with high-quality reference images
- **Processing Speed**: Real-time (30+ FPS) on standard CPU machines
- **False Positive Rate**: <1% with proper cooldown configuration
- **Memory Usage**: Efficient with automatic cleanup mechanisms
- **Scalability**: Handles 5+ simultaneous faces with adaptive processing

