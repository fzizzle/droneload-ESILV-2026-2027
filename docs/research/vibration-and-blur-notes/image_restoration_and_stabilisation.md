# Image restoration and stabilisation before or during fiducial-marker detection

Scope: deblurring (classical, gyro-aided, learned), rolling-shutter (RS) correction, electronic/digital stabilisation, and simple pre-processing, judged by (a) evidence that marker or feature detection improves and (b) cost on embedded hardware. Research date 2026-11-16. Several PDFs were read in full (Ghost-DeblurGAN, DeepGyro, Samsung edge-deblur paper, SlimDeblurGAN); other items come from search abstracts and are flagged as such.

## Q1. Classical deblurring (Wiener, Richardson-Lucy, blind deconvolution) and IMU/gyro-aided non-blind deblurring

### Takeaway
Classical deconvolution needs an accurate blur kernel and produces ringing; on its own, no study I found shows it raising ArUco/AprilTag detection rates. Gyro-aided kernel estimation is well established on phones (2010-2019) and can run in real time, and the strongest result (DeepGyro, a CNN given a gyro-derived blur field) also improved feature-detector repeatability. All of it depends on tight camera-IMU time sync and known exposure and readout times.

### Cited Findings
- Wiener and Richardson-Lucy (RL) "introduce undesirable ringing artifacts" and are non-blind (they need the kernel), which the authors say limits their use for 2D barcode deblurring — [Fast linear motion deblurring for 2D barcode, Optik 2020 (abstract)](https://www.sciencedirect.com/science/article/abs/pii/S0030402620307385)
- A barcode-processing patent says RL and Wiener give nearly the same result at low noise or small motion, that RL works better when the kernel is known but the noise is not, and that Wiener can suit low-power devices because its cost does not depend on the noise. It also says that without deblurring a barcode is often undecodable at about 10 px of motion, while its own method decodes up to 80 px (patent claim, not peer reviewed) — [US8750637B2](https://patents.google.com/patent/US8750637B2/en)
- An older QR study reports RL deblurring producing readable QR codes for blur lengths of 10-40 px, and RL beating Wiener on speed (low-profile paper, treat with caution) — [Deblurring, Localization and Geometry Correction of 2D QR Bar Codes Using RL](https://www.academia.edu/8946882/Deblurring_Localization_and_Geometry_Correction_of_2D_QR_Bar_Codes_Using_Richardson_Lucy_Method)
- Robust linear-motion deblurring recommends Wiener filtering followed by a few iterations of robust, regularised RL as a hybrid — [Fast and Robust Linear Motion Deblurring, arXiv 1212.2245](https://arxiv.org/pdf/1212.2245)
- Real-time QR recovery using fractional-order deblurring has been published (title and abstract only seen) — [ResearchGate 330475367](https://www.researchgate.net/publication/330475367_Real-time_Recovery_and_Recognition_of_Motion_Blurry_QR_Code_Image_Based_on_Fractional_Order_Deblurring_Method)
- **DeepGyro (Mustaniemi et al., WACV 2019).** It computes a per-pixel blur field from gyroscope rotation over the exposure, modelling the rolling shutter explicitly: row y starts exposing at t_f + t_r·y/N, where t_r is the readout time and t_e the exposure time. A U-Net then takes the blurred image plus the blur field. The authors note that t_f, t_r and t_e "can be typically obtained via the API" on phones — [DeepGyro PDF](https://cmp.felk.cvut.cz/~matas/papers/mustaniemi-2019-gyro_deblur-wacw.pdf)
  - It was trained with t_e = 30 ms, t_r drawn at random from 0-30 ms (0 is a global shutter), and synthetic gyro noise plus camera-IMU delay, so that it tolerates inaccurate blur fields — same source
  - Runtime is about 35 ms per 270×480 frame on a GTX 1080 GPU. It handled "extreme and spatially-variant" blur better than the blind DeepBlind and the gyro-based FastGyro, which the authors say "produce[s] a grid-like pattern". It improved the repeatability and matching scores of existing feature detectors and descriptors on blurred images — same source
  - The authors say inertial blur estimates fail through "noisy IMU readings, temporal misalignment between the camera and IMU", and translation matters when the scene is close. When the blind method already did well, "the information from the gyroscope seems to be redundant" — same source
- Hu et al. (CVPR 2016) synthesise local blur kernels from smartphone gyro readings, calibrate the camera-IMU time delay online and refine the kernels — [Image Deblurring using Smartphone Inertial Sensors](https://faculty.ucmerced.edu/mhyang/papers/cvpr16_mobile_deblurring.pdf)
- Multi-frame visual-inertial deblurring (ETH Zurich) estimates piecewise-uniform kernels from gyro data and extends Krishnan-Fergus fast non-blind deconvolution to non-uniform blur — [ETH, WSCG 2015](https://vs.inf.ethz.ch/publ/papers/soeroesg-wscg2015-GyroDeblur.pdf)
- A mesh-grid method estimates a non-uniform point-spread function (PSF) per grid cell from the IMU and says this is computationally much cheaper than blind estimation — [PeerJ CS 2540 (abstract)](https://peerj.com/articles/cs-2540/)
- For gimbal IR cameras, the authors estimate the kernel in advance from motion data and then deblur non-blindly "for real-time performance" — [IR Motion Deblurring, arXiv 2111.11734](https://arxiv.org/pdf/2111.11734)
- A real-time "Deep-Wiener-Network" exists for blind deblurring (title only seen) — [arXiv 2211.16356](https://arxiv.org/pdf/2211.16356)
- An ORB-SLAM variant uses inertial attitude data to estimate the blur kernel for Wiener deconvolution. It reports better tracking and positioning on TUM "while ensuring real-time performance" (abstract only) — [IEEE 10928419](https://ieeexplore.ieee.org/document/10928419/)

### Inferences
- ArUco thresholds the image adaptively and then reads bits from the warped cell centres. Ringing creates light and dark halos parallel to edges, which can split or merge contours and flip bits near cell borders. That makes classical deconvolution with a wrong kernel risky. With the right kernel and mild regularisation (Wiener, or a few RL iterations), the main benefit is restoring the black border's step edge, which is what quad detection needs.
- Vibration blur on a multirotor is mostly rotational, at high frequency, and often non-linear within one exposure. That suits gyro-derived kernels (rotation only) better than blind estimation. The Pixhawk 2 IMU over MAVLink is probably too coarse in rate and timestamps for per-exposure kernels (see Gaps). The camera's own exposure and readout metadata would also be needed.
- A uniform-kernel Wiener filter in the frequency domain is two FFTs per frame. On a 640×480 greyscale crop, that is probably a few milliseconds on an ARM CPU with OpenCV (`cv2.dft`), but I found no measured number for QCS6490-class hardware. Applying it only to a region of interest (ROI) around a predicted marker would cut the cost further.

### Gaps
- I found no paper measuring ArUco or AprilTag detection rate after Wiener/RL deconvolution, or quantifying binarisation failures caused by ringing. The barcode and QR evidence is the nearest analogue.
- I found no measured gyro-to-kernel deblurring latency on an ARM or Qualcomm SoC. The phone papers predate today's SoCs or report GPU timings.
- I did not establish whether Pixhawk 2 MAVLink IMU messages (RAW_IMU / HIGHRES_IMU) give a rate and timestamp precision good enough for kernel estimation. A researcher covering IMU/MAVLink should confirm this.

## Q2. Learned deblurring (DeblurGAN-v2, MPRNet, NAFNet, Restormer, lightweight variants): edge speed, quantisation and task-driven evidence

### Takeaway
Task-driven evidence exists and is positive. On the YorkTag dataset, AprilTag 3 and ArUco detection on motion-blurred images rose from 32% to 59-63% after deblurring. In a drone-landing study, F1 rose from 0.49 to 0.61. The gain only appeared with networks trained or fine-tuned on marker imagery, and some lightweight variants made detection worse. Speed is the obstacle: heavy models such as NAFNet take about 150-180 ms on a flagship Qualcomm NPU. The only sub-20 ms embedded number is a heavily pruned GAN at 256×256 on a Jetson TX2.

### Cited Findings
- **Ghost-DeblurGAN (Liu et al., 2021, YorkTag dataset).** Motion blur breaks marker detection in two ways: quad detection fails when line and quad features are destroyed, or the decoded payload is corrupted and rejected — [arXiv 2109.03379](https://arxiv.org/pdf/2109.03379)
  - On the YorkTag test set, AprilTag 3 and ArUco together found 9,761 markers on sharp images, 3,123 (**31.99%**) on blurred images, 6,118 (**62.68%**) after HINet and 5,769 (**59.10%**) after Ghost-DeblurGAN. Both networks were trained on YorkTag from scratch — same source
  - HINet trained only on GoPro (generic scenes) recovered markers poorly in their example, which is why they built a marker dataset. Domain-specific training mattered — same source
  - GPU time on an NVIDIA Quadro RTX 4000 with GoPro-size images: DeblurGAN-v2 (MobileNetV2) 60 ms, 43.75 GFLOPs, PSNR 28.40. Ghost-DeblurGAN-v4 37 ms, 20.51 GFLOPs (53% fewer), PSNR 28.75, model 6.08 MB. HINet 602 ms, 354 MB — same source
- **SlimDeblurGAN (Sensors 2020, drone landing).** These markers are landing pads detected with YOLOv2, not ArUco — [PMC7411990](https://pmc.ncbi.nlm.nih.gov/articles/PMC7411990/)
  - On real motion-blurred drone frames (RMBD-DB1), F1 was 0.487 with no deblurring, 0.515 with DeepDeblur, 0.577 with DeblurGAN, 0.592 with DeblurGAN (MobileNet) and **0.606** with SlimDeblurGAN — same source
  - On synthetic blur, DeblurGAN (MobileNet) **lowered** F1 to 0.467 from 0.545 and DeepDeblur lowered it to 0.509. The authors note ghosting artefacts left markers blurred. Deblurring can hurt detection — same source
  - Deblurring time per image (deblurring at 256×256; frames 1280×720): SlimDeblurGAN 10.2 ms on a GTX 1070 and **18.3 ms on a Jetson TX2**; DeblurGAN 349 ms and DeblurGAN-MobileNet 215 ms on the TX2. The full pipeline with YOLOv2 ran at 49.3 ms (20.3 FPS) on the TX2. Channel pruning cut parameters from 11.39 M to 1.64 M, and pruning further collapsed PSNR — same source
- **DeblurGAN-v2 (ICCV 2019).** The MobileNet variants are "up to 100 times faster" than the heavy models; MobileNet-DSC takes about 0.04 s per image on a desktop GPU — [arXiv 1908.03826](https://arxiv.org/abs/1908.03826)
- **NAFNet on a Qualcomm NPU (Samsung, arXiv 2601.11685, 2026).** Base NAFNet (17.1 M params, 107 MB, GoPro PSNR 35.80) ran in **177 ms on the NPU of a Galaxy S24 Ultra**. A hardware-aware variant ran in 147 ms in Table 3, but the text says 140 ms, an internal inconsistency, with a PSNR drop to 33.76. The authors note that FLOPs and parameter counts "do not correlate with latency" on NPUs, and that channel-attention modules are NPU-unfriendly. Restormer needs about 140 GMACs against 68 GMACs for their model. The input resolution for the latency figures was not stated in the text I extracted — [arXiv 2601.11685](https://arxiv.org/pdf/2601.11685)
- An unverified blog post reports "NAFNet Unblur" at about 140 ms on a MediaTek Dimensity 9200+ — [DEV Community](https://dev.to/nabil_aman_/running-real-esrgan-and-nafnet-on-android-engineering-a-100-on-device-ai-video-upscaler-5c1o)
- **Lower bound for a tiny restoration CNN on a QCS6490-class NPU.** Qualcomm AI Hub lists INT8 super-resolution nets on the QCS6490 / RB3 Gen 2 (proxy) NPU. QuickSRNetSmall takes 0.977 ms (QNN) or 2.488 ms (TFLite), and XLSR takes 1.076 ms (QNN) or 2.437 ms (TFLite). XLSR as ONNX w8a8 on the CPU takes 12.18 ms. These are Qualcomm-published but separate releases; the input resolution is on the model card. I did not verify them on hardware — [QuickSRNetSmall-Quantized card](https://huggingface.co/qualcomm/QuickSRNetSmall-Quantized/blob/4fa37dbdc70f6a0208c58999a6386cb01709231c/README.md); [XLSR-Quantized card](https://huggingface.co/qualcomm/XLSR-Quantized); [XLSR card](https://huggingface.co/qualcomm/XLSR); [AI Hub job j5wq0xw35](https://aihub.qualcomm.com/jobs/j5wq0xw35)
- The QCS6490 Hexagon tensor processor (HTP) supports INT8 and INT16 through AI Hub, with TFLite and QNN runtimes. YOLOv8-Detection at w8a8 is listed at about 3.6-4.7 ms, and at w8a16 at about 18.7 ms (Qualcomm figures, unverified) — [Qualcomm AI Hub docs](https://docs.qualcomm.com/doc/80-70017-15B/topic/ai-hub.html); [qualcomm/YOLOv8-Detection](https://huggingface.co/qualcomm/YOLOv8-Detection)
- The SLAM literature also uses selective deblurring. DeblurSLAM detects blurred frames and removes the blur inside ORB-SLAM2 (abstract) — [IEEE 9483818](https://ieeexplore.ieee.org/document/9483818). A DeblurGANv2 + ORB-SLAM2 pipeline that deblurs only frames judged insufficiently sharp reported 7.22 cm total RMSE on EuRoC (from a search summary, primary source not opened) — possibly [IEEE 10761281](https://ieeexplore.ieee.org/document/10761281/)

### Inferences
- The task-driven evidence (YorkTag; SlimDeblurGAN on real drone footage) supports roughly doubling detections under heavy blur only when the network is trained on marker-like content. A generic GoPro-trained model may not help and can hurt. A team would need to fine-tune on its own shaken footage, for example from the project's vibration test.
- Running a full-frame learned deblurrer at camera rate on a QCS6490-class NPU is plausible only for very small, fully convolutional, INT8 networks (XLSR or QuickSRNet scale, about 1-2 ms published). The marker-validated models (Ghost-DeblurGAN at 20 GFLOPs, NAFNet) are 10-100× heavier, and their QCS6490 latency is unknown. On QCS6490, NAFNet is probably well above 177 ms, since that figure is from a newer flagship NPU (Snapdragon 8 Gen 3); this is unverified.
- Quantising restoration networks to INT8 can cost PSNR. LayerNorm and channel attention, as in NAFNet and Restormer, are known NPU pain points, consistent with the Samsung paper. GAN generators built from plain convolutions (DeblurGAN-v2 with a MobileNet or Ghost backbone) are likelier to map well to the HTP. This is unverified.
- The cheapest deployment pattern is: detect on raw frames → if a marker is lost or the frame is blurred, crop an ROI around the predicted marker → run a small deblur net on the ROI → detect again. That bounds the NPU cost to a small tile.

### Gaps
- I found no measured latency for any deblurring network on QCS6490 / RB3 Gen 2 or a Qualcomm robotics SoC. Treat all Qualcomm NPU performance claims here as unverified for this board.
- I found no MPRNet, Restormer or NAFNet evaluation scored by ArUco detection rate. Only Ghost-DeblurGAN and HINet (YorkTag) and SlimDeblurGAN (YOLO landing pads) have task-driven numbers.
- I found no data on INT8 quantisation's effect on downstream marker detection, as opposed to PSNR.
- Learned deblurring could also shift corner positions; I found no study measuring marker corner localisation error after it.

## Q3. Rolling-shutter correction: gyro-based per-row correction and learned RS correction

### Takeaway
Gyro-based RS correction plus stabilisation has run in real time on phones since 2011 (Karpenko et al., iPhone 4). It needs calibrated camera-gyro delay, readout time and focal length. Learned single-image RS correction exists and is IMU-assisted in some papers, but I found no published real-time timings. For markers, a global-shutter camera avoids the problem entirely, while software correction adds calibration burden.

### Cited Findings
- Karpenko, Jacobs, Baek and Levoy (Stanford 2011) use gyroscope data alone, after calibrating the gyro and camera from a single capture, to stabilise video and correct rolling shutter with one warp model. It was implemented on the iPhone 4 and designed to run in real time on phone sensors — [Stanford project page](https://graphics.stanford.edu/papers/stabilization/); [paper PDF](https://formaurbis.stanford.edu/papers/stabilization/karpenko_gyro.pdf) (fetch failed; details from search summary)
- Bell, Troccoli and Pulli (ECCV 2014) extend gyro-based stabilisation and RS correction with a non-linear filter on mobile devices — [NVIDIA Research](https://research.nvidia.com/node/2763); [PDF](https://research.nvidia.com/sites/default/files/pubs/2014-09_A-Non-Linear-Filter/bell_troccoli_pulli_eccv2014.pdf)
- Camera-gyro timestamp calibration and synchronisation on phones is a research problem in its own right — [UT Austin autocalibration 2015](https://users.ece.utexas.edu/~bevans/papers/2015/autocalibration/index.html)
- DeepGyro models RS row timing (readout time t_r) inside its gyro blur field, so blur and RS can be handled jointly — [DeepGyro PDF](https://cmp.felk.cvut.cz/~matas/papers/mustaniemi-2019-gyro_deblur-wacw.pdf)
- Mo, Islam and Sattar (CoRL 2021, PMLR 164) refine row-wise poses with IMU data through an LSTM for single-view RS correction. They evaluate by downstream DSO odometry accuracy and report no runtime. Code is at github.com/IRVLab/unrolling — [PMLR v164 mo22a](https://proceedings.mlr.press/v164/mo22a.html); [arXiv 2011.03106](https://arxiv.org/pdf/2011.03106)
- Learning Adaptive Warping (2022) introduced the BS-RSC real-world RS dataset (abstract only) — [arXiv 2204.13886](https://arxiv.deeppaper.ai/papers/2204.13886v1)
- Single-image RS removal with diffusion models (2024) needs no gyroscope at inference — [arXiv 2407.02906](https://arxiv.org/pdf/2407.02906). Diffusion models are far too slow for real-time embedded use; this is an inference, not stated in the snippet.

### Inferences
- With rotation-only RS correction, each image row y gets a homography K·R(t_y)·K⁻¹. On a CPU this is cheap: per-row `cv2.remap` with a precomputed map, or a mesh of about 10-20 strips, each with a homography. The cost is dominated by the remap, which is likely a few milliseconds at VGA, though I found no measured number on ARM. The hard part is calibration: gyro-camera delay must be accurate to about 1 ms, and t_r must be known for the specific sensor.
- For pixel-position logging, correcting RS skew moves the marker corners. To log positions in raw-image coordinates, either detect on the raw frame or map the corrected-image corners back through the inverse per-row warp.
- Vibration on a quadcopter at frame rate (motor harmonics, tens to hundreds of Hz) produces "jello" RS wobble that a gyro sampled below about 2× that frequency cannot capture. That makes the IMU rate requirement stricter for RS correction than for frame-level stabilisation.

### Gaps
- I found no real-time (ms per frame) figures for learned RS-correction networks, and no study of RS correction's effect on fiducial detection rate or corner accuracy.
- The Karpenko PDF could not be fetched (TLS error), so per-frame timings from the original paper are not recorded here.

## Q4. Digital/electronic stabilisation (EIS, gyro-based, OpenCV videostab, feature-based warp): does it help detection, and what does warping do to pixel coordinates?

### Takeaway
I found no quantitative study showing that stabilisation raises fiducial-marker or object detection rates. Stabilisation removes inter-frame motion, not intra-frame blur, so per-frame detection gains should be small. Its real value is temporal (tracking and prediction across frames), and warping changes marker pixel coordinates, so logged positions must be inverse-mapped.

### Cited Findings
- Older aerial-surveillance work argues that moving-object detection run *after* stabilisation "doesn't work well" and builds detection into the stabilisation step instead (abstract) — [Multimedia Tools and Applications 2014](https://link.springer.com/article/10.1007/s11042-014-1928-z)
- Drone dataset papers stabilise mainly to keep stationary objects in place in image coordinates: "video jitter causes positional deviations of stationary targets across frames because all detection outputs are defined in the image coordinate system" — [VRUD, arXiv 2604.01134](https://arxiv.org/pdf/2604.01134). Another aligns frames to a reference using ORB features and a perspective warp to aid later detection and tracking, with no measured gain — [DRIFT, arXiv 2504.11019](https://arxiv.org/pdf/2504.11019)
- Drone stabilisation papers evaluate with interframe transformation fidelity (ITF) and detection ratio — [Video Stabilization for Drone Surveillance Systems (ResearchGate)](https://www.researchgate.net/publication/390193303_Video_Stabilization_for_Drone_Surveillance_Systems)
- A patent combines EIS and horizon keeping with video analytics so tracking works on gimbal-less drones (patent claim, no independent evaluation) — [USPTO 11258949](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11258949)
- Gyro-based stabilisation and RS correction on phones: see Q3 — [Karpenko et al.](https://graphics.stanford.edu/papers/stabilization/)

### Inferences
- A stabilising warp W (a homography or per-row map) applied before detection gives corners p' = W(p). The log must record W⁻¹(p'), or the logged positions become a "virtual camera" coordinate that drifts with the smoothing filter. Each warp also resamples (bilinear interpolation softens edges) and crops or pads borders, which can cut off markers near the frame edge.
- A safer design for this use: detect on the raw frame for logging, and use stabilisation or IMU motion only to predict where markers should be (a search ROI for re-detection or ROI deblurring). Coordinates stay untouched and the benefit of temporal context is kept.
- OpenCV's `videostab` module (feature-based, offline or one-pass) is built for viewing quality and adds latency through a smoothing window. It is not suited to low-latency detection. This comes from general knowledge of the module, as I did not fetch its docs.

### Gaps
- I found no before/after study of detection rate with stabilisation, for fiducials or for objects (VisDrone or similar).
- I found no data on corner-localisation error introduced by EIS resampling.
- I did not fetch the OpenCV videostab docs, so its latency is unsourced.

## Q5. Simple pre-processing for blurred markers: sharpening, CLAHE, adaptive threshold tuning, sharpness-based frame selection

### Takeaway
I found no published study of unsharp masking, CLAHE or variance-of-Laplacian gating in front of ArUco. These are cheap (sub-millisecond to a few ms on CPU) and best treated as tunable experiments measured with the project's own benchmark. The best-supported cheap lever is the detector itself: ArUco is known to be blur-sensitive, its adaptive-threshold and bit-reading parameters can be tuned, and frame and ROI gating avoids wasted work.

### Cited Findings
- ArUco is highly sensitive to motion blur. In fast pass-by sequences, conventional ArUco detected markers in only about 3% of frames, which motivated an event-camera detector — [arXiv 2012.06516](https://arxiv.org/pdf/2012.06516)
- In a simulated linear-blur test, standard ArUco kept full detection up to about a 10% blur ratio, while a recursive variant held to about 6% — [Recursive ArUco Markers, arXiv 2607.13830](https://arxiv.org/pdf/2607.13830)
- Kalaitzakis et al. (JINT 2021) compare ARTag, AprilTag, ArUco and STag on accuracy, detection rate and compute, including simulated motion blur and shadows. The blur ranking needs the full text, which I did not read — [Springer 10.1007/s10846-020-01307-9](https://link.springer.com/10.1007/s10846-020-01307-9)
- In the authors' own test, the deformable learned marker DeepFormableTag reached 99.83% detection under dynamic camera motion against 76.11% for AprilTag — [arXiv 2206.08026](https://arxiv.org/html/2206.08026)
- A 2015 UAV paper used accelerometer data to predict blurred frames and skip them to save processing. This is IMU-based gating rather than image sharpness — [AEEE vol. 13 no. 4, article 1492](https://advances.vsb.cz/index.php/AEEE/article/view/1492)
- ORB-SLAM2 with entropy-based frame selection and image sharpening reported no tracking loss under fast-motion blur in one sequence (match-count evidence only) — [Luo et al., Math. Problems in Eng. 2020](https://onlinelibrary.wiley.com/doi/10.1155/2020/4724310)
- ORB-SLAM suffers significant frame drops on blurred TUM sequences, which motivated blur-aware odometry (MBA-VO) — [arXiv 2103.13684](https://arxiv.org/pdf/2103.13684)
- OpenCV 4.10.0 ArUco `DetectorParameters` defaults, read directly from the installed library: adaptiveThreshWinSizeMin=3, Max=23, Step=10; adaptiveThreshConstant=7.0; minMarkerPerimeterRate=0.03; polygonalApproxAccuracyRate=0.03; cornerRefinementMethod=0 (NONE); cornerRefinementWinSize=5; perspectiveRemovePixelPerCell=4; perspectiveRemoveIgnoredMarginPerCell=0.13; maxErroneousBitsInBorderRate=0.35; errorCorrectionRate=0.6; useAruco3Detection=False — [OpenCV DetectorParameters reference](https://docs.opencv.org/4.x/d1/dcd/structcv_1_1aruco_1_1DetectorParameters.html) (the doc page returned 403, so the values come from `cv2.aruco.DetectorParameters()` in the project venv)

### Inferences
- **Threshold tuning.** Blur widens the edge ramp and lowers local contrast, so the fixed adaptiveThreshConstant=7 may drop border pixels. Testing a lower constant, larger window sizes (Max above 23 for big markers) and a higher polygonalApproxAccuracyRate (blur rounds corners) is cheap. Raising perspectiveRemoveIgnoredMarginPerCell above 0.13 samples bits nearer cell centres, where blur smears least. Every change must be checked against the false-positive rate as well as the found rate. DICT_4X4_50 has a large inter-marker distance, which gives some room for errorCorrectionRate.
- **Corner refinement.** CORNER_REFINE_SUBPIX or CONTOUR improves logged pixel accuracy on sharp frames, but on blurred edges sub-pixel refinement can wander. If enabled, compare corner jitter on clean and shaken footage.
- **Sharpening.** An unsharp mask raises edge slope but also amplifies noise and creates halos similar to deconvolution ringing. A mild mask (sigma about 1-2 px, amount 0.5-1) is a cheap test. CLAHE helps low contrast and uneven lighting, not blur, and can amplify noise in flat regions.
- **Frame selection.** Variance of Laplacian (`cv2.Laplacian(...).var()`) costs well under 1 ms on a downsampled frame. Its absolute value depends on scene texture, so a threshold must be relative, such as a ratio to a running median, or computed on the marker ROI. Discarding blurred frames cuts wasted detection and false positives but cannot recover markers that are only visible in blurred frames. Under continuous vibration it may discard most frames. With an IMU, angular rate × exposure time × focal length gives a direct predicted blur length in pixels, which is a better gate than image sharpness.
- **Exposure.** The cheapest "deblurring" is a shorter exposure, with gain or lighting traded for it. Blur length scales linearly with exposure time. This is camera-side and hardware-dependent, but probably the most effective lever overall.

### Gaps
- I found no published measurement of unsharp masking, CLAHE or Laplacian-variance gating improving ArUco or AprilTag detection rates under blur. The project's own benchmark and vibration test are the only way to quantify these.
- AprilTag 3 has a `decode_sharpening` option. I did not source its documentation or any evaluation of it in this session.
- I did not obtain the Kalaitzakis et al. blur results (paywalled full text).
