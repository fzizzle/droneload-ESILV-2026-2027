# Robust Fiducial-Marker Detection Under Motion Blur and Vibration (Detector Choice and Tuning)

Scope note: these notes cover detector-side choices only (OpenCV ArUco parameters, alternative marker systems, learned detectors, drone experience, and marker/print design). Camera hardware/mounting and temporal tracking are covered by other researchers. Source code facts were checked against OpenCV `4.x` branch files downloaded on 2026-11-16.

## 1. Which OpenCV ArUco DetectorParameters matter for blurred / low-contrast markers, and what values to use?

### Takeaway
The single most important finding for this team is a code fact, not a tuning guess. With `DICT_4X4_50` (maxCorrectionBits = 1) and the default `errorCorrectionRate = 0.6`, OpenCV computes `int(1 * 0.6) = 0`, so the detector does no bit error correction at all. One wrong bit from blur rejects the marker. Raising `errorCorrectionRate` to 1.0 enables 1-bit correction, but 4x4 dictionaries are the most false-positive-prone ArUco family, so that change must be paired with false-positive controls. Beyond that, the parameters that act on blurred markers are the adaptive-threshold window range, `minMarkerPerimeterRate`, `polygonalApproxAccuracyRate` (blurred corners round off), and the bit-sampling pair `perspectiveRemovePixelPerCell` / `perspectiveRemoveIgnoredMarginPerCell`. Corner refinement does not change the detection rate, except for `CORNER_REFINE_APRILTAG`, which replaces candidate detection.

### Cited Findings

**Defaults (OpenCV 4.x `aruco_detector.hpp`)**
- Defaults: `adaptiveThreshWinSizeMin=3`, `Max=23`, `Step=10` (giving three windows: 3, 13, 23), `adaptiveThreshConstant=7`, `minMarkerPerimeterRate=0.03`, `maxMarkerPerimeterRate=4.0`, `polygonalApproxAccuracyRate=0.03`, `minCornerDistanceRate=0.05`, `minDistanceToBorder=3`, `minMarkerDistanceRate=0.125` (changed from 0.05 after 4.8.1), `cornerRefinementMethod=CORNER_REFINE_NONE`, `cornerRefinementWinSize=5`, `relativeCornerRefinmentWinSize=0.3`, `cornerRefinementMaxIterations=30`, `cornerRefinementMinAccuracy=0.1`, `markerBorderBits=1`, `perspectiveRemovePixelPerCell=4`, `perspectiveRemoveIgnoredMarginPerCell=0.13`, `maxErroneousBitsInBorderRate=0.35`, `minOtsuStdDev=5.0`, `errorCorrectionRate=0.6`, `useAruco3Detection=false`, `minSideLengthCanonicalImg=32`, `minMarkerLengthRatioOriginalImg=0.0`, `validBitIdThreshold=0.49`, `detectInvertedMarker=false`. The AprilTag-related defaults are `aprilTagQuadDecimate=0`, `aprilTagQuadSigma=0`, `aprilTagMinClusterPixels=5`, `aprilTagMaxNmaxima=10`, `aprilTagCriticalRad=10°`, `aprilTagMaxLineFitMse=10`, `aprilTagMinWhiteBlackDiff=5` and `aprilTagDeglitch=0` — [OpenCV aruco_detector.hpp (4.x)](https://raw.githubusercontent.com/opencv/opencv/4.x/modules/objdetect/include/opencv2/objdetect/aruco_detector.hpp)
- `relativeCornerRefinmentWinSize`: the header says values of 0.4–0.5 suit distant markers and 0.1–0.2 suit closely spaced ones. The final window is `min(cornerRefinementWinSize, averageModuleSize*relativeCornerRefinmentWinSize)` — [OpenCV aruco_detector.hpp](https://raw.githubusercontent.com/opencv/opencv/4.x/modules/objdetect/include/opencv2/objdetect/aruco_detector.hpp); [OpenCV ArUco tutorial source](https://raw.githubusercontent.com/opencv/opencv/4.x/doc/tutorials/objdetect/aruco_detection/aruco_detection.markdown)

**errorCorrectionRate: the key code fact**
- `DICT_4X4_50` is built as `Dictionary(..., 4, (4-1)/2)`, i.e. `maxCorrectionBits = 1`. By comparison, `DICT_5X5_50` has 3, `DICT_6X6_50` has 6 and `DICT_APRILTAG_16h5` has 2 — [OpenCV aruco_dictionary.cpp](https://raw.githubusercontent.com/opencv/opencv/4.x/modules/objdetect/src/aruco/aruco_dictionary.cpp)
- `Dictionary::identify` computes `int maxCorrectionRecalculed = int(double(maxCorrectionBits) * maxCorrectionRate);` and accepts a code only `if(currentMinDistance <= maxCorrectionRecalculed)`. For 4X4_50 at the default 0.6 this is `int(0.6) = 0`, so only exact matches are accepted. The value must reach 1.0 to allow a 1-bit error — [OpenCV aruco_dictionary.cpp, identify()](https://raw.githubusercontent.com/opencv/opencv/4.x/modules/objdetect/src/aruco/aruco_dictionary.cpp)
- The OpenCV tutorial says `errorCorrectionRate` "is useful to reduce the error correction capabilities in order to avoid false positives". It also says that if `maxCorrectionBits` "is too high, it can lead to a high number of false positives" — [OpenCV ArUco tutorial source](https://raw.githubusercontent.com/opencv/opencv/4.x/doc/tutorials/objdetect/aruco_detection/aruco_detection.markdown)
- False positives at full error correction on 15,620 marker-free indoor images (317,741 square candidates), from Table 3 of the STag paper:
  - ArUco 4X4_50 (1 correction bit): 2,349 false positives
  - 4X4_100: 3,250
  - 4X4_250: 13,018
  - ARUCO_ORIGINAL (0 bits): 785
  - 5X5_50 (3 bits): 269
  - 6X6_100: 177
  - 7X7_100: 2
  - STag HD-family: 2–38 out of 57,893 candidates
  
  STag's "validation failure probability" for 4X4_50 is 7.4E-05, the worst of all libraries tested — [Benligiray et al., STag (arXiv 1707.06292)](https://arxiv.org/pdf/1707.06292)
- STag's perspective-based candidate validation removed a significant share of false positives at maximum error correction. For example, HD23 fell from 98 to 38 and HD11 from 15 to 7 — [STag (arXiv 1707.06292), Table 4](https://arxiv.org/pdf/1707.06292)
- The DeepArUco++ authors built their Shadow-ArUco ground truth by running classic ArUco with error-correction bits set to zero "to get only the detections with the highest confidence, as this weeds out most false detections" — [Berral-Soler et al., DeepArUco++ (arXiv 2411.05552)](https://arxiv.org/pdf/2411.05552)

**Border and bit-sampling parameters**
- `maxErroneousBitsInBorderRate` is multiplied by `markerSize²`. For 4x4 this gives `int(16*0.35) = 5` allowed wrong border cells, out of 20 border cells with a 1-bit border — [OpenCV aruco_detector.cpp](https://raw.githubusercontent.com/opencv/opencv/4.x/modules/objdetect/src/aruco/aruco_detector.cpp)
- `minOtsuStdDev`: if cell pixel standard deviation is below this value, Otsu is skipped and all bits are set by comparing the mean to 128. This is a low-contrast failure mode — [OpenCV ArUco tutorial source](https://raw.githubusercontent.com/opencv/opencv/4.x/doc/tutorials/objdetect/aruco_detection/aruco_detection.markdown)
- `perspectiveRemoveIgnoredMarginPerCell` exists because "white cells can invade some pixels of black cells (and vice versa)". The default 0.13 ignores a 13% margin of each cell. `perspectiveRemovePixelPerCell`: "A higher value ... can improve the bits extraction process (up to some degree), however it can penalize the performance" — [OpenCV ArUco tutorial source](https://raw.githubusercontent.com/opencv/opencv/4.x/doc/tutorials/objdetect/aruco_detection/aruco_detection.markdown)

**Thresholding and candidate-shape parameters**
- Adaptive threshold windows: "Low values of window size can 'break' the marker border if the marker size is too large... too large values can produce the same effect if the markers are too small, and can also reduce the performance". The tutorial also says "it is usually better to use a range of values for the window size, although many thresholding steps can also reduce the performance considerably". On `adaptiveThreshConstant` it says "Its default value is a good option in most cases" — [OpenCV ArUco tutorial source](https://raw.githubusercontent.com/opencv/opencv/4.x/doc/tutorials/objdetect/aruco_detection/aruco_detection.markdown)
- `minMarkerPerimeterRate` is relative to the largest image dimension. At 640 px, 0.03 means a minimum perimeter of about 19 px. "If the minMarkerPerimeterRate is too low, detection performance can be significantly reduced, as many more contours will be considered" — [OpenCV ArUco tutorial source](https://raw.githubusercontent.com/opencv/opencv/4.x/doc/tutorials/objdetect/aruco_detection/aruco_detection.markdown)
- `polygonalApproxAccuracyRate`: "In most cases, the default value works fine, but higher error values could be necessary for highly distorted images" — [OpenCV ArUco tutorial source](https://raw.githubusercontent.com/opencv/opencv/4.x/doc/tutorials/objdetect/aruco_detection/aruco_detection.markdown)

**Corner refinement**
- Corner refinement runs after detection and identification. It "only makes sense if the positions of the marker corners have to be accurate... It is usually a time-consuming step and therefore is disabled by default" — [OpenCV ArUco tutorial source](https://raw.githubusercontent.com/opencv/opencv/4.x/doc/tutorials/objdetect/aruco_detection/aruco_detection.markdown)
- The enum documentation says `CORNER_REFINE_APRILTAG` means "Tag and corner detection uses the AprilTag 2 approach". It is therefore the only refinement option that changes which candidates are found — [OpenCV aruco_detector.hpp](https://raw.githubusercontent.com/opencv/opencv/4.x/modules/objdetect/include/opencv2/objdetect/aruco_detector.hpp)

**ArUco3 mode**
- `useAruco3Detection`: when it is true, the code forces `cornerRefinementMethod = CORNER_REFINE_SUBPIX` ("only CORNER_REFINE_SUBPIX implement correctly for useAruco3Detection"). It also asserts that `minSideLengthCanonicalImg` and `minMarkerLengthRatioOriginalImg` are not both 0. It detects on a downscaled image (scale factor `fxfy = minSideLengthCanonicalImg / (minSideLengthCanonicalImg + maxDim*minMarkerLengthRatioOriginalImg)`) and then refines on a pyramid — [OpenCV aruco_detector.cpp](https://raw.githubusercontent.com/opencv/opencv/4.x/modules/objdetect/src/aruco/aruco_detector.cpp)
- The ArUco3 paper (Romero-Ramirez et al., Image and Vision Computing 76, 2018) reports being "up to 40 times faster" than the state of the art, at over 1000 fps on 4K images without parallelisation. It picks the best scale for detection, identification and corner estimation, and uses temporal information — [URJC repository record](https://burjcdigital.urjc.es/handle/10115/42233)

**Refinement of rejected candidates (`refineDetectedMarkers`)**
- `RefineParameters` defaults are `minRepDistance=10`, `errorCorrectionRate=3` (−1 skips the code check) and `checkAllOrders=true`. It re-tests rejected candidates near reprojected board markers, so it applies only to boards with known layout — [OpenCV aruco_detector.hpp](https://raw.githubusercontent.com/opencv/opencv/4.x/modules/objdetect/include/opencv2/objdetect/aruco_detector.hpp)

### Inferences
- **errorCorrectionRate.** Setting `errorCorrectionRate` to 1.0 on DICT_4X4_50 is the only way to get any bit-error tolerance. Values from 0.0 to 0.99 all behave identically (no correction). This change is likely to raise both recall and the existing 26.6% unmatched rate. STag's numbers suggest 4X4_50 at 1-bit correction gives about 0.15 false positives per cluttered image. The team uses only IDs 0–9, so it could build a custom `cv2.aruco.Dictionary` holding only the first 10 codes of DICT_4X4_50. The IDs, labels and bit patterns stay the same, but a smaller library means fewer chance matches, roughly ×10/50 if false positives scale with library size. This may still count as a "dictionary change" under the team's rules, so confirm with the team. Any IDs 10–49 detected now are by definition false positives and can be filtered out at once.
- **Threshold windows.** Blur smears edges over several pixels and lowers local contrast. More threshold scales help, e.g. `Min=3, Max=33–53, Step=4–6` instead of three scales. This costs runtime roughly in proportion to the number of scales, since the code loops over `nScales`. Lowering `adaptiveThreshConstant` (e.g. 7 → 3–5) helps low-contrast markers survive binarisation but adds candidates and false positives. These are tuning hypotheses; the team's benchmark must check them.
- **Bit sampling.** Raising `perspectiveRemoveIgnoredMarginPerCell` (e.g. 0.13 → 0.2–0.3) samples only cell centres. That is where blur affects bits least, because bleed from neighbouring cells is largest near cell edges. Raising `perspectiveRemovePixelPerCell` from 4 to about 8–10 gives a finer sample for those centres.
- **Candidate shape.** Raising `polygonalApproxAccuracyRate` to about 0.05–0.08 should help blurred, rounded quads pass the square test.
- **Detection rate vs pixel accuracy.** Corner refinement (SUBPIX or CONTOUR) does not change the detection rate. The output is only logged pixel positions, so refinement matters only for sub-pixel accuracy, and SUBPIX on blurred corners may move corners wrongly. Deep ChArUco's learned refiner also got worse under motion blur (see section 3).
- **ArUco3 is a speed tool, not a blur tool.** Downscaling slightly reduces the effective blur length in pixels, which may help detection a little, but it also removes small markers. Its main value is freeing CPU time on a Qualcomm companion board for more threshold scales.

### Gaps
- I found no published sweep of DetectorParameters against blur length for OpenCV ArUco. All value recommendations above other than defaults are inferences and need the team's benchmark.
- I could not find a primary source on runtime cost per method for SUBPIX vs CONTOUR vs APRILTAG refinement. The tutorial only says refinement is "time-consuming".
- I did not verify the minimum Hamming distance among the first 10 codes of DICT_4X4_50. If it is larger than the 50-code minimum, a custom 10-code dictionary could also justify a higher `maxCorrectionBits`.

## 2. Published comparisons of ArUco, AprilTag 3, STag, ChArUco, CCTag, RUNE-Tag, TopoTag etc. under blur, noise and low resolution

### Takeaway
No single study gives clean detection-rate versus blur-length curves for all major systems. Two patterns hold across the evidence. First, markers with fewer, physically larger bit cells survive blur better: standard ArUco holds 100% detection up to blur of 10% of marker width, while Fractal markers drop after 4%. Second, circular/ring designs (CCTag) score best in real moving-camera tests. Classic ArUco and AprilTag all lose roughly 35–63% of detections once a camera moves fast.

### Cited Findings

**Recursive ArUco paper (2026, ArUco authors)**
- Simulated linear motion blur, kernel 2–40% of marker width, averaged over 100 random angles, 4K renders. Standard ArUco used DICT_APRILTAG_16h5 (a 4x4-bit code).
  - Standard ArUco was "the most resilient to blur, sustaining 100% detection up to a 10% blur ratio, since their bits are physically larger and lack internal recursive subdivisions"
  - Fractal markers "drop off rapidly after 4% blur"
  - Recursive ArUco held 100% to 6% and partial detection to 10%
  
  — [Muñoz-Salinas, Romero-Ramirez, Garrido-Jurado, Recursive ArUco Markers (arXiv 2607.13830)](https://arxiv.org/pdf/2607.13830)
- In the same paper, over a distance/angle grid of 0.5–100 m and 0–80°, standard ArUco ran at about 85 FPS, Fractal at about 76 FPS and RArUco at about 185 FPS. Fractal's overall TPR was 27.78% (13.10 ms) and RArUco's 48.33% (5.39 ms) — [arXiv 2607.13830](https://arxiv.org/pdf/2607.13830)

**U.P.B. Sci. Bull. 2023 (CCTag vs ArUco vs AprilTag)**
- Setup: Raspberry Pi 4B camera on a servo rotating at 45–180°/s to create blur. Markers were 10×10 cm ArUco DICT_6X6_50, AprilTag tag36h11 and CCTag.
- Static frames: all three reached 100%. CCTag failed beyond 200 cm (37.5% at 250 cm).
- Moving-frame detection rates:

  | Marker | 50 cm | 100 cm | 150 cm |
  |---|---|---|---|
  | ArUco | 64.35% | 49.92% | 42.71% |
  | AprilTag | 59.02% | 45.71% | 37% |
  | CCTag | 74.64% | 56.14% | 41.5% |

  — [Fiducial marker systems overview and empirical analysis of ArUco, AprilTag and CCTag, U.P.B. Sci. Bull. Series C 85(2), 2023](https://www.scientificbulletin.upb.ro/static/pdfs/full7bc_966141.pdf)
- The same paper cites earlier work in which CCTag "had the highest detection rate of all in terms of distance, occlusion, and motion blur" against RUNE-Tag and ARToolKit Plus, but "the slowest detection algorithm" — [U.P.B. Sci. Bull. 2023](https://www.scientificbulletin.upb.ro/static/pdfs/full7bc_966141.pdf)
- The STag paper notes that CCTag's "main contribution is robustness against motion blur" — [STag (arXiv 1707.06292)](https://arxiv.org/pdf/1707.06292)

**STag (2017)**
- Runtime on 1280×720 with one marker: ARToolKit+ 2.6 ms, ArUco 10.0 ms, STag 18.1 ms, RUNE-Tag 579.9 ms — [STag (arXiv 1707.06292), Table 7](https://arxiv.org/pdf/1707.06292)
- STag is designed for pose stability (jitter), not blur. RUNE-Tag fails at distance because "its coding circles appear too small to be detected". Systems with a thick outer border "can be detected from a distance" — [STag (arXiv 1707.06292)](https://arxiv.org/pdf/1707.06292)

**Kalaitzakis et al. (JIRS 2021)**
- The study compares ARTag, AprilTag, ArUco and STag on accuracy, detection rate and computation, including simulated shadow noise and motion blur. Per summary snippets, AprilTag had the best detection rate and ARTag a consistently low one — [Kalaitzakis et al., Fiducial Markers for Pose Estimation, JIRS 101 (2021)](https://link.springer.com/article/10.1007/s10846-020-01307-9); [ResearchGate entry](https://www.researchgate.net/publication/350418791_Fiducial_Markers_for_Pose_Estimation_Overview_Applications_and_Experimental_Comparison_of_the_ARTag_AprilTag_ArUco_and_STag_Markers)

**Other comparisons**
- FMAC (2026) compares ArUco, AprilTag, STag and TopoTag with ray-traced synthetic images. Its authors note that robustness is usually tested against occlusion, defocus and motion blur. I did not verify its numbers — [Laurent & Sandoz, FMAC (arXiv 2601.07723)](https://arxiv.org/html/2601.07723v1)
- A thesis on a moving ArUco board reports 71% detection with blurry images included and 92% without — [DiVA thesis, Camera pose estimation with moving Aruco-board](https://www.diva-portal.org/smash/get/diva2:1505194/FULLTEXT01.pdf)

**AprilTag 3 tuning guidance (README)**
- "Increasing the quad_decimate parameter will increase the speed of the detector at the cost of detection distance."
- "If your image is somewhat noisy, increasing the quad_sigma parameter can increase speed."
- "If the border of your tag is not being detected as a quadrilateral, decrease quad_decimate... If the border of the tag is detected then experiment with changing decode_sharpening."
- tagStandard41h12 is recommended "for the vast majority of applications".

— [AprilRobotics/apriltag README](https://github.com/AprilRobotics/apriltag)

### Inferences
- **Blur length per bit cell.** "10% of marker width" for a 4x4-bit marker with a 1-bit border (6 cells across) is about 0.6 of a cell. Detection therefore stays reliable while blur length is below about half a bit cell. This is the planning rule to use: blur length (px) ≲ 0.5 × marker side (px) / 6 for 4x4.
- **Real-motion losses.** In the servo test, classic ArUco lost 36–57% of detections under real motion blur, comparable to the team's 56.4% real-footage result. That suggests the team's numbers are typical rather than a bug.
- **CCTag** is the strongest blur-tolerant classic design, but it requires changing the marker system, which needs team approval, and it is slow. It is not a practical swap within the current constraints.

### Gaps
- I could not access the Kalaitzakis full text, so its blur kernel sizes and per-marker detection percentages are missing.
- I found no TopoTag or ChArUco-vs-ArUco blur numbers beyond Deep ChArUco's OpenCV baseline (section 3).
- The exact RArUco Fig. 11 values beyond 10% blur are in a plot and could not be extracted from text.

## 3. Deep-learning fiducial detectors robust to blur (DeepTag, Deep ChArUco, YOLO-based, Shadow-ArUco, learned refinement)

### Takeaway
Learned detectors raise recall a lot under blur and bad lighting: Deep ChArUco gets 78% good poses vs 27% for OpenCV on real motion sequences, and DeepArUco++ finds 95% vs 53% on Shadow-ArUco. Classic ArUco keeps the best precision and the lowest corner error. The published runtimes all use desktop GPUs (GTX 1080, RTX 3090, Quadro), so embedded Qualcomm performance is unverified. A lightweight deblurring front end (Ghost-DeblurGAN) roughly doubles detection on blurred frames, from 32% to 59%, at 37 ms per frame on a desktop GPU.

### Cited Findings

**Deep ChArUco (2018)**
- Synthetic horizontal blur: OpenCV detection drops to 0% at kernel size ≥ 6 px, while Deep ChArUco keeps about 94% "even under extreme blur" — [Hu et al., Deep ChArUco (arXiv 1812.03247)](https://arxiv.org/html/1812.03247v2)
- Real sequences:
  - Motion blur: 78% good-pose frames vs 27% for OpenCV
  - Shadows: 100% vs 36%
  - Below 1 lux: OpenCV returns nothing
  - Overall, over 26,000 frames: 97.4% vs 68.8%
  
  — [Deep ChArUco](https://arxiv.org/html/1812.03247v2)
- RefineNet (a learned sub-pixel corner refiner) reduces error in most sequences but makes motion-blur sequences worse: 1.591 vs 0.786 px reprojection error. The true corner often falls outside its 8×8 refinement region — [Deep ChArUco](https://arxiv.org/html/1812.03247v2)
- Runtime at 320×240 on a GTX 1080: ChArUcoNet + RefineNet 66.5 FPS, ChArUcoNet alone 100.7 FPS, OpenCV + cornerSubPix 99.4 FPS. Model sizes are 4.8 MB and 4.1 MB — [Deep ChArUco](https://arxiv.org/html/1812.03247v2)

**DeepArUco++ (2024/25)**
- Pipeline: a YOLOv8n/s marker detector, then a corner-refinement CNN (direct regressor or heatmap), then a decoder CNN. Training data is Flying-ArUco v2, with DICT_6X6_250 markers on COCO backgrounds and blur and colour augmentation. Code: github.com/AVAuco/deeparuco — [Berral-Soler et al., DeepArUco++ (arXiv 2411.05552)](https://arxiv.org/pdf/2411.05552)
- Shadow-ArUco test set: 8,652 frames at 800×600, six viewpoints, markers on walls in a dark room with moving shadows and light patterns projected over them — [DeepArUco++](https://arxiv.org/pdf/2411.05552)
- Table 2 results on Shadow-ArUco:

  | Method | AUC | Matched (4-corner) | Corners within 5 px + correct ID | Corner error (px) |
  |---|---|---|---|---|
  | yolov8s + heatmap | 0.709 | 95.1% | 80.9% | 2.04 |
  | yolov8n + heatmap | 0.712 | 94.2% | 79.7% | 2.11 |
  | Classic ArUco | 0.505 | 53.3% | 43.6% | 0.72 (best) |
  | DeepTag | 0.254 | 39.8% | 29.3% | 1.40 |

  The authors note "in terms of precision, the classic ArUco is unmatched at the cost of a much-reduced recall" — [DeepArUco++](https://arxiv.org/pdf/2411.05552)
- The best detector augmentation was blur plus colour shift. Training from yolov8n with that augmentation gave AUC 0.9485 for the detector stage. The heatmap refiner was "significantly" better than direct regression — [DeepArUco++](https://arxiv.org/pdf/2411.05552)
- Runtime at 800×600 with about 11 markers per image, on an i7-11700F and RTX 3090: yolov8n+direct 26.9 ms (37.8 FPS), yolov8s+heatmap 29.9 ms (33.9 FPS), classic ArUco 8.6 ms (130.5 FPS), DeepTag 142.8 ms (28.7 FPS, high variance). Decoding alone takes about 13 ms — [DeepArUco++, Table 5](https://arxiv.org/pdf/2411.05552)

**Ghost-DeblurGAN + YorkTag (2021)**
- YorkTag provides paired sharp/blurred images with AprilTags and ArUcos (1,577 training pairs). Sharp images come from an iPhone 12 on a gimbal, and blur is synthesised from them — [Liu et al., Application of Ghost-DeblurGAN to Fiducial Marker Detection (arXiv 2109.03379)](https://arxiv.org/pdf/2109.03379)
- Detected markers on the YorkTag test set (AprilTag 3 + ArUco):

  | Image set | Detected | Rate |
  |---|---|---|
  | Sharp | 9,761 | 100% (reference) |
  | Blurred | 3,123 | 31.99% |
  | Deblurred with HINet | 6,118 | 62.68% (602 ms, 354 MB) |
  | Deblurred with Ghost-DeblurGAN | 5,769 | 59.10% (37 ms, 6.08 MB) |

  Timings are on an NVIDIA Quadro RTX 4000 — [arXiv 2109.03379](https://arxiv.org/pdf/2109.03379)

**YoloTag (2024)**
- A YOLOv8 marker detector for UAV navigation on a Parrot Bebop2, 856×480 at 30 FPS. It ran at 55 FPS on an NVIDIA Quadro P2200, vs 24 FPS for AprilTag and 3 FPS for DeepTag with 8 markers. The authors say the AprilTag detector "frequently failed to detect all markers and was more susceptible to motion blur and noise". Trajectory Hausdorff distance was 0.246 vs 0.386 (spiral) — [Raxit et al., YoloTag (arXiv 2409.02334)](https://arxiv.org/pdf/2409.02334)

**DeepTag and DeepFormableTag**
- DeepTag (TPAMI) trains with Gaussian/motion blur and noise augmentation. The authors report it "consistently achieves equal or higher recall and precision" than the original detectors and is more robust to synthesised noise and motion blur. Exact values are in figures only — [Zhang et al., DeepTag (arXiv 2105.13731)](https://arxiv.org/pdf/2105.13731)
- DeepFormableTag reportedly shows AprilTag detection falling from about 99.9% under smooth camera motion to about 76% under dynamic motion. This comes from a search summary and was not verified in the PDF — [DeepFormableTag (arXiv 2206.08026)](https://arxiv.org/pdf/2206.08026)

### Inferences
- **Hybrid design.** A YOLO-nano detector trained with blur augmentation could serve as a candidate proposer. Classic ArUco decoding/refinement (or the existing pipeline) would then run on crops. That keeps ArUco's precision and pushes recall toward DeepArUco++ levels. On a Qualcomm NPU this is plausible but unverified, since every published timing is on a desktop GPU.
- **Learned refiners under blur.** Deep ChArUco's RefineNet got worse under blur, which suggests any learned corner refiner needs real-blur training data.
- **Deblurring front end.** A deblurring front end doubles detections on blurred frames, but 37 ms on a desktop GPU likely means more than 100 ms on an embedded CPU (unverified). It is probably only viable on a Qualcomm NPU/GPU.

### Gaps
- I found no published runtimes of DeepArUco++, YoloTag or Ghost-DeblurGAN on Qualcomm/Snapdragon or other embedded ARM hardware.
- I found no learned detector trained specifically on DICT_4X4_50. DeepArUco++ uses 6x6 codes, though its detector stage is code-agnostic and the decoder could be retrained.

## 4. Drone-specific experience: precision landing on ArUco/AprilTag under flight vibration

### Takeaway
Drone literature confirms that blur from vibration and fast manoeuvres is a known failure mode, but it rarely reports detection rate against measured vibration. The documented fixes are to keep bit cells large relative to blur, use nested or multi-scale markers for range, use learned detectors where a GPU exists, and filter or track over time. The OpenCV ArUco detector is about 2× faster than AprilTag in a UAV setting, which leaves headroom for heavier tuning.

### Cited Findings
- The Recursive ArUco authors write that UAV landings "are frequently characterized by sudden maneuvers, vibrations, and high-speed descents, which introduce severe motion blur". Their flight test used a DJI Mini 4 Pro over a 30×30 cm pad, 0–15 m altitude, 30 fps, about 900 frames. There were no detections in the first 125 frames because the pad was too close, acquisition came at frame 130, and tracking became unstable above about 12–15 m, where the marker fell below the minimum pixel resolution — [Recursive ArUco Markers (arXiv 2607.13830)](https://arxiv.org/pdf/2607.13830)
- In an MDPI Electronics 2026 study (3 series × 10 landings each for GPS, AprilTag and ArUco), the OpenCV ArUco detector processed about 710 detections/s vs about 363/s for AprilTag. The accuracy gap between the two markers was small relative to the gain over GPS. This comes from a search summary; the full paper was not read — [Experimental Evaluation of Precision Positioning in Unmanned Aerial Systems Using Fiducial Markers, Electronics 15(8):1582](https://www.mdpi.com/2079-9292/15/8/1582)
- Ghost-DeblurGAN's examples include frames from a manoeuvring UAV (Quanser QDrone) and a low-cost CSI camera on a moving UGV. The work is motivated by marker loss from motion blur on such platforms — [arXiv 2109.03379](https://arxiv.org/pdf/2109.03379)
- YoloTag on a Bebop2 UAV: AprilTag "frequently failed to detect all markers and was more susceptible to motion blur and noise". The YOLO detector gave smoother trajectories at 55 FPS on a GPU — [YoloTag (arXiv 2409.02334)](https://arxiv.org/pdf/2409.02334)
- An evaluation exists of AprilTag and WhyCode for precision landing with a gimbal-mounted camera on a Raspberry Pi, but I could not retrieve its numbers — [ResearchGate: Evaluation of April Tag and WhyCode Fiducial Systems for Autonomous Precision Drone Landing with a Gimbal-Mounted Camera](https://www.researchgate.net/publication/359390509_Evaluation_of_April_Tag_and_WhyCode_Fiducial_Systems_for_Autonomous_Precision_Drone_Landing_with_a_Gimbal-Mounted_Camera)

### Inferences
- The flight evidence points to the marker's pixel size and resolution as the dominant failure cause at altitude, with blur dominant during manoeuvres. Both argue for larger printed markers relative to flight height.

### Gaps
- I found no PX4/ArduPilot landing-target or IMAV team report giving detection rate against measured vibration. Search results were blog-level or anecdotal (e.g. a Medium post), so they are excluded.
- I did not verify a search result labelled "AprilTag 2" that appeared to describe a BlobBoards Pixhawk study reporting 58–80% detection.

## 5. Marker design and print choices that raise blur tolerance

### Takeaway
Blur tolerance scales with the size of a bit cell in pixels. Larger printed markers and fewer bits per side (4x4 is already the best ArUco option) give the most tolerance. Keep a white quiet zone of at least one bit cell, print matte, and choose the smallest dictionary that covers the IDs in use. A smaller dictionary has larger inter-marker distance and fewer false positives, though 4x4 trades away error-correction capacity.

### Cited Findings
- Standard ArUco markers resist blur better than nested designs "since their bits are physically larger". Fractal markers' small central cells "are easily washed out" after 4% blur — [Recursive ArUco Markers (arXiv 2607.13830)](https://arxiv.org/pdf/2607.13830)
- OpenCV: "it is recommended to choose the smallest [dictionary] that fits your application... The smaller the dictionary, the higher the inter-marker distance" — [OpenCV ArUco tutorial source](https://raw.githubusercontent.com/opencv/opencv/4.x/doc/tutorials/objdetect/aruco_detection/aruco_detection.markdown)
- Error-correction capacity grows with bits: 4X4_50 has 1 bit, 5X5_50 has 3 and 6X6_50 has 6. False positives at full correction fall sharply with bit count: 2,349 for 4X4_50, 269 for 5X5_50 and 979 for 6X6_50 on 15,620 images — [OpenCV aruco_dictionary.cpp](https://raw.githubusercontent.com/opencv/opencv/4.x/modules/objdetect/src/aruco/aruco_dictionary.cpp); [STag Table 3](https://arxiv.org/pdf/1707.06292)
- The OpenCV docs say the white space around a marker matters for corner location and detection. The border makes the strong black/white gradient the contour stage needs. Community advice (non-authoritative) suggests a quiet zone of at least one module, with half a module marginal. One forum test found single-marker detection best when the white margin was at least the black border width. The VIVE guide suggests a margin of at least 1/5 of the marker size — [answers.opencv.org](https://answers.opencv.org/questions/196297/revisions/); [VIVE: tips for creating ArUco markers](https://business.vive.com/au/support/vive-lbss/category_howto/tips-for-creating-aruco-markers.html)
- Varjo recommends matte paper and matte ink for markers, with inkjet or pigment printing over glossy laser toner. Glossy surfaces cause glare that hinders reading — [Varjo Markers docs](https://developer.varjo.com/docs/v3.7.0/get-started/varjo-markers); [Fujifilm: uncoated vs matte vs glossy paper](https://print-us.fujifilm.com/news-updates/different-types-printer-paper/)
- AprilTag 3 recommends tagStandard41h12 for most uses. Its layout has improved small-tag detection "at the cost of a slight decrease in detection distance" — [AprilRobotics/apriltag README](https://github.com/AprilRobotics/apriltag)

### Inferences
- **Keep 4x4.** DICT_4X4 already has the biggest cells per marker size of any ArUco family. Moving to 5x5 or 6x6 would cut blur tolerance per printed size but add error correction (3–6 bits) and far fewer false positives. That trade-off is a team/organiser decision, and the markers may be organiser-supplied.
- **Markers you print.** For markers the team prints, a wider white margin (e.g. 2 cells), matte stock and a thicker black border via `markerBorderBits=2` would raise robustness. `markerBorderBits=2` must match the detector parameter and cuts the bit-cell size for a fixed print size. Contest markers may not be under the team's control.

### Gaps
- I found no controlled study measuring detection rate against quiet-zone width or matte vs glossy under blur. The quiet-zone and print advice comes from vendor docs and forums, not peer-reviewed work.
- The contest rules (not researched here) determine whether marker size, print and dictionary are fixed by organisers.
