---
name: acoustic-diarization
description: Acoustic speaker diarization using fundamental pitch (F0), spectral centroid, and conversational continuity priors.
---

# Acoustic Diarization Skill

## Biometric Clustering Algorithm
1. **Pitch Profiling ($F_0$)**: Compute autocorrelation or harmonic product spectrum on 30ms Hamming-windowed frames.
2. **Spectral Centroid ($SC$)**: Calculate center of mass of power spectrum:
   $$SC = \frac{\sum f \cdot |X(f)|}{\sum |X(f)|}$$
3. **Conversational Continuity Prior**:
   If time delta between adjacent turns $\le 1.5\text{s}$, $\Delta F_0 \le 28\text{ Hz}$, and $\Delta SC / SC \le 15\%$, preserve speaker continuity to eliminate false phantom speaker segmentation.
4. **Biometric Memory**: Maintain rolling speaker profile vectors across all dialogue turns.
