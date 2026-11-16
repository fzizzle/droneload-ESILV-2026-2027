# Temporal (multi-frame) tracking to keep fiducial-marker detections reliable under shake and blur

Scope note: the problem is a fixed 40 px jump gate in a 3-of-5 confirmation tracker. Under simulated moderate shake (mean 43 px/frame) it cuts the reported rate from 63.8% raw to 32.6%. Sources are mostly primary papers and official docs. Statements tagged "(training knowledge, unverified here)" were not confirmed by a fetched source in this session.

## 1. Motion-predicted gating: Kalman filters, Mahalanobis/chi-square gates, MOT frameworks, and whether known IDs make gating unnecessary

### Takeaway
Standard MOT trackers do not use a fixed pixel gate. They gate on a Kalman-predicted position with a statistical (Mahalanobis, chi-square) threshold, or on a threshold scaled by object size, and confirm tracks after about 3 hits. ArUco IDs are unique, so association is already solved by ID. A gate is then needed only to reject rare false ID decodes, and it should be loose and motion-aware, never a tight fixed radius.

### Cited Findings
- SORT/DeepSORT-family trackers model image-plane motion with a discrete Kalman filter and a constant-velocity model. SORT's state is `[xc, yc, s, a, ẋc, ẏc, ṡ]`. Later trackers use an 8-tuple `[xc, yc, a, h, ẋc, ẏc, ȧ, ḣ]`. BoT-SORT found that estimating w and h directly works better. — [BoT-SORT, Aharon et al. 2022](https://arxiv.org/pdf/2206.14651)
- DeepSORT gates by "thresholding the Mahalanobis distance at a 95% confidence interval computed from the inverse χ² distribution". For the 4-D measurement space the threshold is t(1) = 9.4877. — [DeepSORT, Wojke et al. 2017](https://arxiv.org/html/1703.07402v1)
- In DeepSORT, new tracks stay "tentative during their first three frames" and are deleted if they fail to associate in that window. Tracks unmatched for longer than a maximum age (30 frames in the experiments) are deleted. — [DeepSORT](https://arxiv.org/html/1703.07402v1)
- DeepSORT (and BoT-SORT, which follows it) makes the noise covariances proportional to the object's size rather than constant: Q_k = diag((σp·w)², (σp·h)², …, (σv·w)², …), R_k = diag((σm·w)², …). The values are σp = 0.05, σv = 0.00625 and σm = 0.05, "since our frame rate is also 30 FPS". This makes the gate scale with apparent object size. — [BoT-SORT](https://arxiv.org/pdf/2206.14651)
- BoT-SORT notes that when detections go missing in high-frame-rate use, "track extrapolations can be perform[ed] using the KF's prediction step, which may cause more continuous viewing of tracks with slightly higher MOTA". — [BoT-SORT](https://arxiv.org/pdf/2206.14651)
- ByteTrack's key idea is to associate nearly every detection box, low-score ones included, matching low-score boxes against existing tracklets to "recover true objects and filter out background detections". Added to 9 other trackers, it gave "consistent improvement on IDF1 score ranging from 1 to 10 points". It scored 80.3 MOTA, 77.3 IDF1 and 63.1 HOTA on the MOT17 test set at 30 FPS on a V100. — [ByteTrack, Zhang et al. 2021](https://arxiv.org/abs/2110.06864)
- Norfair (a lightweight Python tracker) needs a user-set `distance_threshold` ("maximum distance that can constitute a match"). It uses a hit counter (`hit_counter_max`, default 15) that rises on a match and falls otherwise, and the object is destroyed below 0. `initialization_delay` defaults to `hit_counter_max/2`. The default filter is `OptimizedKalmanFilterFactory()`. `Tracker.update(coord_transformations=...)` accepts a camera-motion transform from its `MotionEstimator`. — [Norfair Tracker reference](https://tryolabs.github.io/norfair/2.2/reference/tracker/)
- A 2025 analysis looks specifically at Kalman-filter-based trackers on fast-moving tiny objects. It was found in search, but its results were not read. — [arXiv 2509.18451](https://arxiv.org/pdf/2509.18451)

### Inferences
- **Why the 40 px gate fails:** at a mean of 43 px per frame, a gate smaller than the typical move rejects roughly half of true detections. The 3-of-5 rule then fails to confirm, which matches 63.8% → 32.6%. Since ArUco IDs are unique per marker, the gate does no association work. It only guards against false ID decodes, so a tight gate costs recall for almost no gain.
- **A constant-velocity Kalman filter alone will not fix shake.** Vibration is oscillatory and roughly zero-mean, so velocity flips sign every few frames. A CV prediction can be worse than "last position" right after a reversal. The useful part of a Kalman filter here is the innovation covariance S. With Q sized to the measured shake, the chi-square gate (d² = νᵀS⁻¹ν < 5.99 for a 2-D centre or 9.49 for 4-D, 95%) grows on its own when motion is large. Camera-motion compensation (section 2) is what removes the shake itself.
- **Cheapest fix to test first:** for an ID-matched detection, accept it unless the jump exceeds a loose, scaled gate, for example k × marker side length or a fraction of the frame diagonal. A sanity check is still worth keeping: a similar side length and a convex quad. Re-run the vibration test with gate values of 40, 80 and 120 px and with no gate, to measure how much recall the gate costs and how many false IDs it actually blocks.
- **Track state:** a per-marker 2-D centre filter `[x, y, ẋ, ẏ]` is enough, with corners carried as offsets, or 8 corner coordinates with shared velocity. The Hungarian assignment and IoU of SORT, ByteTrack and BoT-SORT are unnecessary when IDs are known. Only their Kalman prediction, gate statistics and track lifecycle (tentative or confirmed, max age) carry over.
- Adding Norfair or a SORT package would need team approval as a dependency. A 4-state Kalman filter is about 30 lines of NumPy, or `cv2.KalmanFilter` with OpenCV already present.

### Gaps
- No source found with numbers for ArUco-specific false-ID rates under blur, which is what decides whether any position gate is needed. The ArUco dictionary's inter-marker distance and error-correction settings govern this, but no figure was retrieved.
- No published comparison of fixed-pixel vs Mahalanobis gating on shaky drone footage was found.

## 2. Global-motion compensation: per-frame camera motion from sparse flow or gyro, applied before gating (BoT-SORT CMC)

### Takeaway
BoT-SORT's camera-motion compensation (CMC) is the established recipe. It tracks background keypoints with sparse optical flow, fits a RANSAC affine, and warps the Kalman prediction (state and covariance) into the new frame before gating. This is the most direct fix for shake-induced gate failures, and it runs in plain OpenCV Python.

### Cited Findings
- BoT-SORT: in a dynamic camera, "the bounding box location in the image plane can shift dramatically, which might result in increasing ID switches or false negatives". Static cameras are also affected "due to motion by vibrations or drifts caused by the wind". — [BoT-SORT](https://arxiv.org/pdf/2206.14651)
- Method: "With the lack of additional data on camera motion (e.g. navigation, IMU, etc.) … image registration between two adjacent frames is a good approximation to the projection of the rigid motion of the camera onto the image plane." It follows OpenCV's Video Stabilization global motion estimation with an affine model: "extraction of image keypoints … followed by sparse optical flow for feature tracking with translation-based local outlier rejection. The affine matrix A ∈ R^{2×3} was solved using RANSAC." Sparse registration "allows ignoring the dynamic objects in the scene based on the detections". — [BoT-SORT](https://arxiv.org/pdf/2206.14651)
- Applying it: x̂′ = M̃·x̂ + T̃ and P′ = M̃·P·M̃ᵀ, where M is the 2×2 scale/rotation part and T the translation. The translation part affects only the centre. The corrected prediction and covariance then go into the normal KF update. "In high velocities scenarios, full correction of the state vector, including the velocities term, is essential." — [BoT-SORT](https://arxiv.org/pdf/2206.14651)
- Ablation on the MOT17 validation set (ByteTrack baseline → +KF → +CMC): MOTA 77.66 → 77.67 → 78.31, IDF1 79.77 → 79.89 → 81.51, HOTA 67.88 → 68.12 → 69.06. CMC gives the largest single gain. The cMOTA plot on the rotating-camera sequence MOT17-13 shows MOTA "drops rapidly from frame 400 to 470" from camera rotation, and CMC preserves it. — [BoT-SORT](https://arxiv.org/pdf/2206.14651)
- The original CMC code was based on OpenCV contrib's C++ VideoStab, which had no Python binding at the time. Roboflow's `trackers` reimplementation offers sparseOptFlow, ORB, SIFT and ECC backends, describes estimating a homography (unlike the paper's affine), and enables CMC by default. — [Roboflow trackers BoT-SORT docs](https://trackers.roboflow.com/latest/trackers/botsort/)
- Norfair exposes the same idea as a `MotionEstimator` whose transform is passed to `Tracker.update(coord_transformations=...)`. — [Norfair](https://tryolabs.github.io/norfair/2.2/reference/tracker/)

### Inferences
- **Concrete pipeline (pure OpenCV, about 2–5 ms at 320×240 grey on ARM; timing unverified):**
  1. `cv2.goodFeaturesToTrack` on a downscaled grey frame, with marker quads masked out so they do not bias the estimate. Use around 200 corners and refresh every N frames or when the count drops.
  2. `cv2.calcOpticalFlowPyrLK` from the previous frame to the current one with `maxLevel` 3 or more. Pyramids are needed because shake moves points about 40 px, beyond a single-level window. Keep only points with status 1, and optionally apply a forward-backward check.
  3. `cv2.estimateAffinePartial2D(prev, curr, method=cv2.RANSAC)`, which fits a 4-DoF similarity and is more robust than a full affine with few points.
  4. Warp each track's predicted position with A (velocity with M only), then gate the residual.
- With compensation, the residual motion of a static marker is only parallax and model error, likely a few px. A gate of a few tens of px then works again, and the 3-of-5 confirmation would track raw detection closely.
- The vibration test applies a synthetic global shake, so CMC should recover most of the 63.8% vs 32.6% gap in that test. Real flights add rolling-shutter wobble and parallax, so real-footage validation is needed.
- **Gyro alternative:** with calibrated intrinsics K and camera rotation R from integrated gyro, the image motion is the infinite homography H = K·R·K⁻¹. This needs time sync and camera-IMU extrinsics (section 4). Visual GMC needs neither, so it is the better first step.
- Over a textureless floor (a contest arena), KLT may find few features. Fall back to the translation implied by the detected markers themselves, or to the plain Kalman prediction.

### Gaps
- No measured runtime for the KLT + estimateAffinePartial2D pipeline on a Qualcomm ARM board was found.
- No source tested BoT-SORT CMC on vibration-dominated (high-frequency) drone video. MOT17 camera motion is slow, so the ablation gain probably understates the effect for shake.

## 3. Recovering markers in frames where detection fails: KLT corners, template/correlation tracking, ROI re-detection, refineDetectedMarkers, ArUco3

### Takeaway
There are three practical recovery routes. (a) Propagate the last detected corners with pyramidal KLT for a few frames. (b) Re-run `detectMarkers` on an upscaled ROI around the motion-compensated prediction. (c) The ArUco library's discriminative-correlation-filter (DCF) tracker, which is built for blur but is GPL and outside OpenCV. `refineDetectedMarkers` needs a known board layout. ArUco3 mainly speeds detection and does not add blur robustness.

### Cited Findings
- Romero-Ramirez, Muñoz-Salinas and Medina-Carnicer (2021) state that "marker detection is affected by noise and blur": small camera movements blur images enough to prevent detection. Their method estimates marker locations with a set of discriminative correlation filters. It reports more than 200 fps on HD images on a single CPU thread and outperforms "state-of-the-art methods for marker detection and standard DCFs in terms of speed, precision, and sensitivity". It ships as part of the ArUco library. — [Tracking fiducial markers with DCF, Image and Vision Computing 107 (2021)](https://burjcdigital.urjc.es/handle/10115/42238); [UCO AVA group page](https://uco.es/investiga/grupos/ava/?p=1463)
- The ArUco library is GPLv3 for personal, research and educational use (licensing as summarised from the ArUco page in search results; unverified). — [search summary of ArUco DCF paper](https://burjcdigital.urjc.es/items/c884dfa5-b1f5-4a46-807b-8477686fdc5b/full)
- ArUco3 ("Speeded up detection of squared fiducial markers", IVC 76, 2018) uses a multiresolution approach plus temporal information to reduce computation. It reports being "up to 40 times faster" than the state of the art, reaching over 1000 fps on 4K images without parallelisation. — [Romero-Ramirez et al. 2018](https://hdl.handle.net/10115/42233)
- In OpenCV, `DetectorParameters.useAruco3Detection` enables this strategy (default false). `minMarkerLengthRatioOriginalImg` (range 0–1, default 0; "for a FullHD video a good value to start with is 0.1") sets the smallest marker searched. `minSideLengthCanonicalImg` (default 32) is the side length of the downscaled canonical image used for contour search. — [OpenCV DetectorParameters](https://docs.opencv.org/4.7.0/d1/dcd/structcv_1_1aruco_1_1DetectorParameters.html); [OpenCvSharp mirror](https://shimat.github.io/opencvsharp/api/OpenCvSharp.Aruco.DetectorParameters.html)
- `ArucoDetector::refineDetectedMarkers` tries to find undetected markers "after detecting some markers in the image". Its `RefineParameters` include `minRepDistance` (default 10), the "minimum distance between the corners of the rejected candidate and the reprojected marker in order to consider it as a correspondence". They also include `errorCorrectionRate` (default 3, −1 disables the step) and `checkAllOrders` (default true). The free-function version is deprecated. — [OpenCV RefineParameters](https://docs.opencv.org/4.x/d5/d09/structcv_1_1aruco_1_1RefineParameters.html)

### Inferences
- `refineDetectedMarkers` takes a `Board` argument and reprojects missing markers from the board layout (training knowledge; the full doc page returned 403). It helps only if the contest markers are laid out as a known rigid board, or if a custom one-marker board is built per marker. For isolated markers it does not recover blurred frames.
- **KLT corner propagation:** after a detection, track the 4 corners with `calcOpticalFlowPyrLK` (pyramidal, forward-backward check). Accept the result if all 4 pass and the quad stays convex with a near-constant side ratio. Limit this to a few frames, for example 5. KLT also degrades under strong motion blur, so it works best for intermittent misses between sharp frames.
- **ROI re-detection:** crop around the CMC-warped prediction (e.g. 2–3× the marker size), optionally upscale 2× for small markers, and call `detectMarkers` on the crop. This is a real detection, not an extrapolation, so it keeps logged positions unbiased. It is cheap because the crop is small.
- **ArUco3 in a tracker:** set `minMarkerLengthRatioOriginalImg` each frame from the last detected marker size (for example 0.7× the last side divided by the image side). This copies the temporal trick of the ArUco3 paper and speeds up detection. It does not add robustness to blur.
- **Logging must keep provenance:** frames filled by KLT or prediction are estimates. They should be marked as such (a source or status flag) and never mixed silently with detections. Adding a column changes the CSV format, which needs team approval under `AGENTS.md`.
- The ArUco DCF tracker is the most directly relevant published method for blur. Using it would need a dependency decision (C++ library, GPL) and Python bindings, which are unverified.

### Gaps
- The exact `refineDetectedMarkers` doc text (board requirement) could not be fetched (HTTP 403).
- No quantitative comparison found of KLT vs template matching vs DCF on blurred ArUco frames, beyond the DCF paper's own claims. Its full-text numbers were not read.
- No source found on whether Python bindings for the ArUco library's DCF tracker exist.

## 4. Gyro/IMU fusion for visual tracking on drones: sync, calibration, MAVLink latency, evidence

### Takeaway
Gyro-aided feature tracking is well established (Hwangbo, Kim and Kanade, 2009/2011). The evidence for its gain over good visual-only initialisation is mixed, and it brings real costs: time sync, camera-IMU calibration, and MAVLink rate and latency limits. Visual GMC should come first. The gyro is a later option that needs team approval.

### Cited Findings
- Hwangbo, Kim and Kanade (IROS 2009) used a low-cost MEMS gyroscope to give KLT a better initial estimate, with an affine photometric model. The journal version (IJRR 30(14), 2011) adds online camera-gyro auto-calibration and a GPU implementation. — [IJRR record](https://bvbvf1.bib-bvb.de/vufind/PrimoRecord/cdi_proquest_miscellaneous_1010883234); [hgpu summary](https://hgpu.org/?p=2454)
- Poling and Lerman report that gyro-predicted KLT initialisation shows no clear advantage over a careful optical-only initialisation. They use gyro data instead to regularise the tracking energy. — [Enhancing Feature Tracking With Gyro Regularization, arXiv 1511.01508](https://ar5iv.arxiv.org/html/1511.01508)
- Huang and Liu (IEEE TIM 2021) propose a pixel-aware IMU-aided variant that predicts flow per feature instead of one homography for all points. — [TIM 2021 PDF](https://robotics.pkusz.edu.cn/static/papers/TIM2021-weibohuang.pdf)
- Camera-IMU time offsets arise from triggering and transmission delays. Kalibr does offline batch spatiotemporal calibration (Furgale et al., IROS 2013; Rehder, Siegwart and Furgale, T-RO 2016) and needs a calibration target. Online temporal calibration methods (e.g. Qin and Shen 2018) are faster. — [Online Temporal Calibration for Monocular VI Systems, arXiv 1808.00692](https://arxiv.org/pdf/1808.00692)
- Kalibr's initial time-offset guess comes from correlating absolute angular velocity seen by the camera and by the IMU. `--timeoffset-padding` bounds the offset search when `--time-calibration` is used. — [Kalibr wiki](https://github.com/adujardin/kalibr/wiki/Multi-IMU-and-IMU-intrinsic-calibration)
- OpenVINS recommends Kalibr for offline calibration, with online estimation of extrinsics and time offset as an alternative. — [OpenVINS calibration docs](https://docs.ros.org/en/api/ov_core/html/gs-calibration.html)
- MAVLink IMU streaming in practice: PX4 users asking for HIGHRES_IMU at 200 Hz got about 185–189 Hz. The rate is limited by `MAV_x_RATE` and link bandwidth (e.g. 80,000 B/s). — [PX4 forum: HIGHRES_IMU stream rate](https://discuss.px4.io/t/increase-stream-rate-of-highres-imu-message/4789)
- A PX4 write-up says the IMU output rate is set by ATTITUDE or ATTITUDE_QUATERNION streams, which take precedence, and advises against streaming HIGHRES_IMU through the stream command. — [TLab UAV notes: MAVLink IMU](https://tlab-uav.github.io/tech-details/docs/hardware/px4-firmware/mavlink-imu)
- ArduPilot's ROS guide recommends TIMESYNC at 10 Hz and SYSTEM_TIME at 1 Hz so both sides can align timestamps. — [ArduPilot ROS timesync](https://ardupilot.org/dev/docs/ros-timesync.html)
- One user found MAVLink message latency of the same order as the TIMESYNC-measured delay for some messages, but not for GPS_RAW_INT (anecdotal). — [ArduPilot forum: sensor-to-MAVLink delay](https://discuss.ardupilot.org/t/sensor-read-to-mavlink-tx-delay-companion-computer/54324)
- PX4 precision landing runs a `landing_target_estimator` Kalman filter on target measurements. `LTEST_MODE` selects a moving (0, default) or stationary (1) target, and only stationary mode feeds the measurements into EKF2/LPE. `LTEST_SCALE_X/Y` scale the measurements in the sensor frame. Slow sideways oscillation in stationary mode means the scale is too high. — [PX4 Precision Landing docs](https://docs.px4.io/main/en/advanced_features/precland)

### Inferences
- For the 2-D marker pixel use case, the gyro would be used through H = K·R·K⁻¹ to warp the prediction. At 30 fps, a 10 ms timing error during a 5 rad/s shake is a 0.05 rad error. At a focal length of about 600 px that is about 30 px, as large as the shake itself. Sub-frame time sync is therefore essential, and MAVLink timestamps over UART/USB without hardware triggering make this hard. All numbers here are illustrative.
- The Pixhawk gyro at about 185 Hz gives roughly 6 samples per 30 fps frame. That is enough to integrate inter-frame rotation if timestamps are good.
- Reading MAVLink is read-only and does not command the drone. It still counts as talking to the flight controller under `AGENTS.md`, so it needs a person's approval.
- No study found shows a gain specifically for fiducial-marker tracking from gyro fusion versus visual GMC. Poling and Lerman suggest the gain over good visual initialisation is small.

### Gaps
- No measured end-to-end Pixhawk 2 → companion MAVLink latency or jitter figure was found in a primary source.
- No evidence was found on whether the unconfirmed Qualcomm companion's camera stack exposes frame-capture timestamps on the same clock as MAVLink TIMESYNC.
- The PX4 landing-target estimator's internal process-noise and gating parameters were not retrieved.

## 5. Smoothing without bias or lag: One-Euro, alpha-beta, Kalman smoothing, and lag-vs-jitter evaluation

### Takeaway
Any causal smoother trades jitter for lag. The One-Euro filter adapts its cutoff to speed so that lag is small during fast motion, which makes it the standard cheap choice for display or control. For logged positions that must be unbiased, log the raw detections and apply any smoothing offline, or log it as a separate field.

### Cited Findings
- The 1€ filter (Casiez, Roussel and Vogel, CHI '12, pp. 2527–2530) is a first-order low-pass filter whose cutoff rises with speed. At low speed a low cutoff reduces jitter at the cost of lag. At high speed the higher cutoff reduces lag at the cost of jitter. — [1€ filter page](https://cristal.univ-lille.fr/~casiez/1euro); [HAL paper](https://hal.archives-ouvertes.fr/hal-00670496)
- Tuning procedure: start with beta = 0 and min-cutoff around 1 Hz. Lower min-cutoff to remove jitter at rest, then raise beta until lag in fast motion is acceptable. — [1€ filter page](https://cristal.univ-lille.fr/~casiez/1euro)
- In the authors' comparison, the 1€ filter had less lag than other filters at a reference amount of jitter reduction. — [Casiez et al. 2012, CORE PDF](https://core.ac.uk/download/49919969.pdf)
- A PyPI `OneEuroFilter` package exists (would be a dependency). — [libraries.io OneEuroFilter](https://libraries.io/pypi/OneEuroFilter/0.2.0)
- DeepSORT/BoT-SORT Kalman filters with size-proportional R (σm = 0.05 × size) weight the measurement by its expected noise. — [BoT-SORT](https://arxiv.org/pdf/2206.14651)

### Inferences
- **Bias sources:** (1) Lag. Any causal filter of a moving signal is biased toward past positions, and under shake the true marker pixel moves 43 px/frame, so heavy smoothing would log the wrong place. (2) Smoothing in world terms when the target is image pixels. The logged pixel position of a static marker really moves with shake, so "smoothing out the shake" changes the answer if raw pixels are wanted. Decide whether the contest wants pixel positions per frame (no smoothing) or stabilised positions (smooth after CMC).
- **Recommended:** log raw detected corners unchanged. Use the Kalman filter only for gating and prediction, and to fill gaps that are clearly flagged. If a smoothed output is needed, use a causal 1€ filter in compensated coordinates for live use. For logs, use an offline forward-backward smoother (Rauch–Tung–Striebel, or zero-phase `scipy.signal.filtfilt`), which has no lag (training knowledge, unverified here). SciPy may already be a dependency; check before assuming.
- An alpha-beta filter is a steady-state constant-velocity Kalman filter with fixed gains (training knowledge). It is a lighter option than `cv2.KalmanFilter` but loses the innovation covariance needed for chi-square gating.
- **Lag vs jitter evaluation:** on the generated video with known ground truth, measure (a) jitter as the RMS frame-to-frame deviation while the true marker is static, and (b) lag as the mean signed error along the motion direction, or the cross-correlation peak offset in frames, during known motion. Report error against ground truth for raw, filtered and offline-smoothed signals. This follows the 1€ authors' approach of fixing jitter reduction and comparing lag.

### Gaps
- The exact lag and jitter figures from Casiez et al.'s comparison table were not read in this session.
- No source was found on smoothing bias specifically for fiducial-marker pixel logs.
