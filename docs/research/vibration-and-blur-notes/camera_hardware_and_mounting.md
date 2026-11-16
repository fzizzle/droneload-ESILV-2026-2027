# Camera hardware, capture settings and mounting against vibration and motion blur on small multirotors

Research date: 2026-11-16. All prices are retailer snapshots of unknown date. Check them before relying on them.

## Global vs rolling shutter: measured effects, readout times, named global-shutter sensors and modules

### Takeaway
A rolling shutter exposes rows one after another. A typical rolling sensor takes about 15-30 ms to read a frame, which is longer than one period of prop vibration (about 5-10 ms). A frame therefore captures part of a vibration cycle or more, and that appears as jello and skew. Global-shutter sensors remove this. The usual embedded MIPI choices are OV9281/OV9282 (1 MP mono, roughly US$26-60), Sony IMX296 (1.6 MP, Raspberry Pi Global Shutter Camera, roughly £38-48) and onsemi AR0234 (2.3 MP, roughly US$93-100). None of them is confirmed on the Rubik Pi 3 / QCS6490 camera stack.

### Cited Findings
**Mechanism and vendor guidance**
- A rolling shutter scans the image row by row from top to bottom, which causes jello when the camera or object moves. A global shutter exposes all rows at the same moment and removes jello. Global-shutter sensors are "typically a lot more expensive at higher resolutions (above 1MP)." — [Luxonis, Shutter type](https://docs.luxonis.com/hardware/platform/sensors/shutter-type/)
- Luxonis recommends a global shutter for fast-moving cameras or objects and for stereo pairs, and a rolling shutter where higher resolution is needed and motion is slow. — [Luxonis](https://docs.luxonis.com/hardware/platform/sensors/shutter-type/)
- Row-time formula: `row_time = 1 / (maxFps × rows)`. Example: IMX378 at 1080p60 gives 1/(60×1080) ≈ 15.4 µs per row, so about 16.6 ms for the full 1080-row frame. Row time depends on the sensor mode, MIPI lanes and speed, and bit depth. — [Luxonis](https://docs.luxonis.com/hardware/platform/sensors/shutter-type/)
- Worked Luxonis example: a 50 cm box moving at 1 m/s, 2 m from an IMX378 camera, skews by about 1.16 px at 1080p and about 4.66 px at 4K. That example covers object translation only, not vibration. — [Luxonis](https://docs.luxonis.com/hardware/platform/sensors/shutter-type/)
- ArduPilot's camera page says jello is caused by vibration from unbalanced props and motors on CMOS (rolling-shutter) cameras such as GoPros. It can be reduced by mounting the camera on soft rubber, silicone or foam earplugs. — [ArduPilot, Cameras and Gimbals](https://ardupilot.org/copter/docs/common-cameras-and-gimbals.html)
- Tyto Robotics names prop and motor imbalance as the most common cause of drone jello: vibration combined with line-by-line readout. The page is qualitative and has no measurements. — [Tyto Robotics](https://www.tytorobotics.com/blogs/articles/jello-effect-in-drones)
- FRAMOS (camera vendor, marketing) says vibration-heavy, high-speed platforms favour a global shutter and stable platforms can tolerate a rolling shutter. — [FRAMOS](https://framos.com/articles/global-vs-rolling-shutter-uav-cameras/)

**Measured readout times (rolling shutter)**
- DJI Mavic 3: about 16 ms full-sensor readout, measured from 60 Hz light banding. The Mavic 4 Pro is described only as "a few milliseconds". — [Pix-Pro Mavic 3](https://www.pix-pro.com/blog/dji-mavic-3-rolling-shutter); [Pix-Pro Mavic 4](https://www.pix-pro.com/blog/mavic-4-rolling-shutter)
- The Gyroflow `rollingshutter` tool measures readout from LED-strobe banding (at 1 kHz, one band is 1 ms). Its sample output is about 15.7-15.85 ms. — [gyroflow/rollingshutter listing](https://awesome.ecosyste.ms/projects/github.com%2Fgyroflow%2Frollingshutter)
- Larger cameras for comparison: Sony VENICE 2 under 3 ms, ARRI ALEXA 35 about 7.9 ms, Sony FX2 27 ms in 4K full-frame mode, Sony A7 IV about 66.5 ms. — [CineD](https://cined.com/?p=115774); [YMCinema FX2](https://ymcinema.com/2025/05/31/sony-fx2-the-readout-speed-dilemma/); [Pix-Pro](https://www.pix-pro.com/blog/dji-mavic-3-rolling-shutter)
- No measured readout time was found for IMX219, IMX477 or IMX708 (the Rubik Pi 3 supported sensors). An NVIDIA forum thread gives the IMX477 pixel rate as 840 MHz and defines readout as CSI end minus CSI start, but gives no number. — [NVIDIA forum](https://forums.developer.nvidia.com/t/calculating-hq-camera-readout-speed-in-jetson-nano/165781/7)

**Research on rolling shutter in UAV vision**
- Rolling-shutter monocular visual odometry gives inaccurate ego-motion. Abrupt motion "such as the fast motion caused by vibration" stays hard to handle even with earlier RS-correction methods (2017). — [arXiv 1704.07163](https://arxiv.org/pdf/1704.07163.pdf)
- A rolling-shutter-aware direct VIO can approach global-shutter performance and comes with a dataset recorded with both shutter types at once (2019). Software modelling needs an accurate IMU and timing, which a marker detector does not have. — [arXiv 1911.01015](https://arxiv.org/pdf/1911.01015)
- Photogrammetry on a senseFly eBee: rolling-shutter models reach competitive accuracy, but global-shutter cameras are still better (2016). — [ISPRS Annals III-3/139/2016](https://isprs-annals.copernicus.org/articles/III-3/139/2016/)

**Named global-shutter sensors and modules**
| Sensor / module | Resolution, pixel, format | Frame rate | Price snapshot | Notes |
|---|---|---|---|---|
| OmniVision OV9281 (Arducam, Pi) | 1280×800 mono, 3 µm, 1/4″ | 120 fps at 1280×800 on 2-lane MIPI, 180 fps at VGA (datasheet). Arducam docs say 60 fps at 1-lane. | US$25.99 (Arducam), A$42.95 (Core Electronics), US$50-62 (RobotShop) | The official Pi V4L2 driver supports only RAW and manual exposure, and only on Rev.B. No hardware ISP/encode on the Pi. — [search summary of Arducam, Core Electronics, RobotShop datasheet](https://cdn.robotshop.com/media/a/adu/rb-adu-109/pdf/arducam-ov9281-1mp-mono-global-shutter-mipi-camera-raspberry-pi-datasheet.pdf); [Arducam OV9281 docs](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/Global-Shutter/1MP-OV9281-OV9282/) |
| OV9282 (Arducam, OAK FFC) | 1280×800 mono, 3 µm | n/a | US$44.99 | Used as the stereo pair in OAK-D products. — [Arducam OV9282 OAK](https://www.arducam.com/product/ov9282-mono-global-shutter-wide-angle-oak/) |
| Sony IMX296 (Raspberry Pi Global Shutter Camera, SC0926) | 1456×1088, 1.6 MP, 3.45 µm, 6.3 mm diagonal, RAW10 | n/a in the sources found | £37.59 ex VAT (Farnell), £48 (SB Components), about US$78-90 | C/CS lens mount. Exposures as short as 30 µs with enough light. Integrated IR-cut filter. — [Farnell](https://uk.farnell.com/raspberry-pi/sc0926/global-shutter-camera-computer/dp/4163984); [SB Components](https://shop.sb-components.co.uk/products/raspberry-pi-global-shutter-camera) |
| onsemi AR0234CS | 1920×1200, 2.3 MP, 1/2.6″, 4-lane MIPI | 120 fps at full resolution (sensor). Many modules are capped at 60 fps at full resolution and 120 fps at 720p. | Bare sensor US$27.93 at 2,100 units. TechNexion TEVS-AR0234-C US$97.50. TEVI-AR0234-C about US$100. | Luxonis calls it the highest-resolution global-shutter sensor it supports. — [Arrow](https://www.arrow.com/en/products/ar0234cssc00suka0-cp/on-semiconductor); [TechNexion TEVS-AR0234-C](https://www.technexion.com/shop/embedded-vision/mipi-csi2/tevs/tevs-ar0234-c/); [DigiKey TEVI-AR0234-C](https://www.digikey.my/en/products/detail/technexion/TEVI-AR0234-C/20498950); [Luxonis](https://docs.luxonis.com/hardware/platform/sensors/shutter-type/) |
| OV9281 USB UVC webcam | 720p mono | 100 fps (listing) | n/a | USB route with no MIPI driver needed. The listing is unverified. — [desertcart listing](https://www.desertcart.com.cy/products/348353753-100fps-mono-global-shutter-usb-camera-720p-ov9281-uvc-webcam) |

**Qualcomm / Rubik Pi 3 support (vendor doc)**
- The Thundercomm Rubik Pi 3 user manual (CSI page) lists only the Raspberry Pi HQ Camera (IMX477, M12 mount: 4056×3040 and 1920×1080), Camera Module 2 (IMX219, standard only, no wide or NoIR: 3280×2464, 1632×1224) and Camera Module 3 (IMX708, standard only: 4608×2592, **autofocus not supported in current software**). All three are rolling-shutter sensors. The connectors are 22-pin 0.5 mm FPC. The test pipeline is `qtiqmmfsrc camera=0 ! video/x-raw,format=NV12,width=1280,height=720,framerate=30/1`. The page says nothing about global-shutter or third-party sensors and points to a separate compatibility list. — [Thundercomm Rubik Pi 3 CSI](https://www.thundercomm.com/rubik-pi-3/en/docs/rubik-pi-3-user-manual/1.0.0-u/peripherals-and-interfaces/csi)
- RidgeRun has written a driver for the ams Mira220 sensor that captures through qtiqmmfsrc on the Rubik Pi 3, so third-party sensors are possible with driver work. Mira220 is a 2.2 MP global-shutter sensor, but that comes from training knowledge and was not confirmed in this research, so treat it as **unverified**. — [RidgeRun Mira220 for Rubik Pi 3](https://developer.ridgerun.com/wiki/index.php/Mira220_Camera_Driver_for_Rubik_Pi_3)
- Kernel patches from June-July 2026 add IMX219 device-tree overlays for qcs6490-rubikpi3. Their upstream status is unknown. — [LKML patch v2](https://lkml.iu.edu/2607.2/13635.html)
- Leopard Imaging has a product category for RB3 Gen 2 (QCS6490). Which sensors and shutter types it offers was not visible. **Unverified.** — [Leopard Imaging RB3 Gen 2](https://leopardimaging.com/product-category/platform-partners/qualcomm/rb3-gen-2/)

### Inferences
- Prop vibration on a 450-class frame is likely about 100-200 Hz (next section), a period of about 5-10 ms. A rolling sensor with a readout of about 16 ms spans roughly 1.6-3 vibration cycles per frame. Rows are then displaced by different, oscillating amounts, so a square marker's edges bend into waves (true jello), not just a uniform skew. That fits the team's simulation, where rolling-shutter wobble hurt more than blur. A global shutter turns the same vibration into a whole-frame shift plus blur within the exposure only.
- Every officially supported Rubik Pi 3 camera is rolling-shutter. A global-shutter camera on qtiqmmfsrc therefore means either a vendor-supplied driver/ISP tuning (as RidgeRun did for Mira220) or a USB UVC global-shutter camera that bypasses qtiqmmfsrc. Either path is unverified for the organisers' board, and the exact board model is still unconfirmed.
- A monochrome sensor (OV9281/OV9282) suits ArUco, which works on grayscale. With no Bayer filter it also collects more light per pixel, which helps short exposures. That is a general sensor property, not measured here.
- To reduce rolling-shutter skew without changing hardware, read out faster: use a mode with fewer rows (binning or crop) or a higher maximum fps. Readout time scales roughly as 1/(maxFps) for the sensor mode, per the Luxonis formula.

### Gaps
- No measured readout time was found for IMX219, IMX477 or IMX708 in any mode. The team could measure it with the Gyroflow LED-strobe method.
- No head-to-head study of rolling vs global shutter for fiducial or ArUco detection under real drone vibration was found.
- The IMX296 frame rate was not found in the sources fetched. Training knowledge suggests about 60 fps at full resolution, but this is **unverified**.
- No vendor document confirms any global-shutter sensor on QCS6490 qtiqmmfsrc, apart from the RidgeRun Mira220 page, whose shutter type was not checked. All Qualcomm-board claims here are **unverified** beyond the Thundercomm table.

## Exposure time, gain and frame rate trade-offs: blur length, max exposure, lighting, flicker

### Takeaway
Rotational blur in pixels ≈ angular rate (rad/s) × exposure (s) × focal length in pixels. Machine-vision practice treats more than about 1 px as blur. Synthetic tests show standard ArUco holds full detection up to blur of about 10% of the marker's width in pixels. Short exposure trades blur for noise (higher gain) and for frame-to-frame flicker under 100 Hz (Europe) arena lighting. The flicker-safe exposures (10 or 20 ms) are too long to stop blur.

### Cited Findings
- Linear-motion blur formula from machine vision: B = Vp × Te × Np / FOV (blur in pixels = speed × exposure × pixels across the field of view ÷ FOV width). Blur "becomes an issue past 1 pixel in most cases." — [1stVision, Calculating exposure time](https://www.1stvision.com/machine-vision-solutions/?p=946)
- Patent for limiting motion blur: image-plane motion = angular velocity × focal length × exposure, divided by pixel pitch. Small-angle form: blur_px ≈ ω·t·f/p. — [US 7509038](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7509038)
- ArUco blur tolerance (synthetic): linear blur of 2-40% of marker width, averaged over 100 angles. Standard ArUco kept full detection up to a blur ratio of about 10% of marker width (2026 preprint). — [arXiv 2607.13830, Recursive ArUco Markers](https://arxiv.org/pdf/2607.13830)
- With a moving marker, standard ArUco on a frame camera reached only 3% "pass detection" against 94% for an event-camera method. The authors blame ArUco's sensitivity to motion blur. — [arXiv 2012.06516](https://arxiv.org/pdf/2012.06516)
- A comparison of ARTag, AprilTag, ArUco and STag under simulated motion blur and shadows exists, but its blur results were not extracted. — [J. Intell. Robot. Syst., 10.1007/s10846-020-01307-9](https://link.springer.com/10.1007/s10846-020-01307-9)
- IMAV 2024 flight test of four cheap cameras for ArUco (IMX519 at 1920×1080 at 30 fps, Wanscam IP camera at 1280×720, OV2640/ESP32 at 1024×768, Foxeer analog). The test was outdoors, lux was measured, and exposure and shutter were not studied. Detection fell with altitude, with near-zero detection at 12 m for a 100 mm marker. The IP camera was the most consistent. The paper is not directly relevant to vibration. — [IMAV 2024 paper 21](https://www.imavs.org/papers/2024/21.pdf)
- The IMX296 Global Shutter Camera supports exposures as short as 30 µs "with adequate lighting". — [Farnell/SB Components listings](https://shop.sb-components.co.uk/products/raspberry-pi-global-shutter-camera)
- Flicker: mains-driven lighting flickers at twice mains frequency, 100 Hz (10 ms period) in 50 Hz regions such as France and 120 Hz (8.3 ms) in 60 Hz regions. It is most visible at short exposures. — [Vadzo via Newswire](https://www.newswire.com/news/vadzo-imaging-explains-led-flicker-mitigation-techniques-for-22791982); [US 6900834](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6900834)
- With a rolling shutter, rows catch different phases of the flicker or PWM cycle, which makes horizontal bands. A global shutter avoids banding, but brightness can still vary from frame to frame when exposure is shorter than one flicker cycle. — [ENTTEC](https://support.enttec.com/pixel/pixel-general-knowledge/why-do-leds-flicker-on-camera); [Vadzo](https://www.newswire.com/news/vadzo-imaging-explains-led-flicker-mitigation-techniques-for-22791982)
- Flicker-safe exposures are whole multiples of the flicker period (10 ms or 20 ms at 100 Hz). — [Vadzo](https://www.newswire.com/news/vadzo-imaging-explains-led-flicker-mitigation-techniques-for-22791982); [ENTTEC](https://support.enttec.com/pixel/pixel-general-knowledge/why-do-leds-flicker-on-camera)
- LED banding in one test appeared only when fixtures were dimmed. It depended on PWM frequency, and there was none at about 10 kHz PWM at 100% output. — [LEDs Magazine](https://www.ledsmagazine.com/14299599)
- Stack Overflow advice for ArUco on moving objects: a higher-resolution camera and shorter exposure (anecdotal). — [SO 63252399 mirror](https://kiwix.lema.org/stackoverflow.com_en_all_2023-11/questions/63252399/aruco-markers-pose-estimation-opencv-for-moving-objects)

### Inferences
- **Worked blur numbers** (the team's own arithmetic, from the formula above): take a 1280-px-wide sensor with a lens of about 70° horizontal FOV. Then f_px = 640 / tan(35°) ≈ 914 px.
  - A 30°/s body rotation (0.52 rad/s) gives 0.48 px at 1 ms, 0.95 px at 2 ms, 3.8 px at 8 ms and 15 px at 33 ms (auto-exposure in dim light).
  - A 100°/s fast correction gives 1.6 px at 1 ms and 13 px at 8 ms.
  - A narrower lens (larger f_px) or higher resolution scales blur up in proportion.
- **Exposure ceiling from the ArUco 10% rule:** a marker 60 px wide tolerates about 6 px of blur. At 100°/s with f_px ≈ 914, that allows t ≤ 6 / (1.745 × 914) ≈ 3.8 ms. For 30°/s it allows ≈ 12.6 ms. A fixed exposure of about 1-4 ms is therefore a reasonable range to test. Treat it as a starting point to verify with `testing.benchmark`, not a sourced recommendation.
- **The flicker conflict:** flicker-safe exposures (10 or 20 ms) blur far too much. At 1-4 ms with a global shutter, expect frame-to-frame brightness to change with 100 Hz lighting (if the arena lights are mains-driven or low-frequency PWM), not banding. The options are:
  1. accept it and use detector thresholds robust to it (ArUco's adaptive threshold helps),
  2. add onboard light (an LED ring on the drone powered from DC, so it does not flicker), or
  3. pick a frame rate that is a sub-multiple of 100 Hz (for example 50 or 25 fps) so each frame samples the same flicker phase. This is unsourced reasoning that only works if the camera clock is stable against mains, so it is unreliable.
- Short exposure needs more gain, which adds noise. A mono sensor with larger pixels (IMX296 3.45 µm, OV9281 3 µm, against IMX219 1.12 µm, from general knowledge) and a fast lens (low f-number) reduce the gain needed.
- A higher frame rate does not reduce blur by itself. Only exposure does. It does give more independent chances to detect per second, and it shortens rolling-shutter readout in high-fps modes.

### Gaps
- No source gave a lux level needed for 1-2 ms exposures on these sensors. This needs a test: measure arena lux with a phone luxmeter, then check image brightness at fixed exposure and gain.
- Whether the contest arena lights flicker at 100 Hz (or PWM-dim) is unknown. A slow-motion phone video or the Gyroflow strobe method could check it.
- No real flight data was found linking angular jitter amplitude (°/s RMS at the camera) to ArUco detection rate.

## Drone vibration: frequency bands, amplitudes and the link to image jitter

### Takeaway
The dominant vibration is at the motor rotation frequency and the blade-pass frequency (2× rotation for 2-blade props), plus harmonics. ArduPilot says that is roughly 100 Hz on larger copters and 200 Hz on smaller ones. For an F450 with 920 KV motors and 10″ props on 3S, the estimate is about 70-110 Hz shaft and 140-220 Hz blade pass (unsourced estimate). The Pixhawk's VIBE log gives acceleration levels (good below 15 m/s², problems above 30, almost always bad above 60). That measures airframe vibration, not camera angular jitter.

### Cited Findings
- ArduPilot: the main noise frequency comes from motors and props at flight speed. It is fairly high frequency with fairly low amplitude. — [ArduPilot Vibration Damping](https://ardupilot.org/copter/docs/common-vibration-damping.html)
- ArduPilot IMU batch sampler: the motor noise peak is "likely to be around 200Hz" on a smaller copter and "100Hz or so" on a larger copter or QuadPlane. A hover example shows a pronounced 180 Hz peak with a smaller second harmonic. An FFT cannot show frequencies above half the sample rate (500 Hz at 1 kHz), and higher noise aliases down. — [ArduPilot IMU Batch Sampling](https://ardupilot.org/copter/docs/common-imu-batchsampling.html)
- Patent hover measurement (laser vibrometry): motor shaft peak at 61 Hz and blade-pass peak at 122 Hz for a 2-blade prop. — [US 10112730](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10112730)
- A 2024 quadcopter hover study found strong blade-pass frequency and harmonics, plus asynchronous vibration from loosely fitted components. — [UTEC, Analysis of quadcopter body frame vibration during hovering flight](https://cris.utec.edu.pe/en/publications/analysis-of-quadcopter-body-frame-vibration-during-hovering-fligh/)
- Vibration is often worst at hover, when the motor or prop frequency matches the frame's natural frequency (forum). — [discuss.ardupilot.org vibration competition thread](https://discuss.ardupilot.org/t/dealing-with-vibrations-and-harmonics-a-competition/13619/17)
- F450-class drive data: Racerstar BR2212 920 KV with 1045 prop at 11.1 V gives 642 g thrust at 9.5 A, 105 W (vendor). — [racer.lt listing](https://racer.lt/item/racerstar-racing-edition-2212-br2212-920kv-2-4s-brushless-motor-for-350-380-400-frame-kit-3507.html)
- ArduPilot VIBE message: VibeX/Y/Z are the standard deviation of the primary accelerometer in m/s². Below 30 is normally acceptable, healthy logs are below 15 with occasional peaks near 30, above 30 may cause problems, and above 60 nearly always causes position or altitude hold problems. Clip0/1/2 count accelerometer saturation at 16 G and should ideally be 0. Under 100 is likely fine, and a steadily rising count means a serious problem. — [ArduPilot Measuring Vibration](https://ardupilot.org/copter/docs/common-measuring-vibration.html)
- PX4: vibration reduces performance and can cause sensor clipping and fly-aways. The fix is to remove the source first (balanced quality props, firm mounting) and filter in software last. Measurement goes through the Flight Review vibration plots. — [PX4 Vibration Isolation](https://docs.px4.io/main/en/assembly/vibration_isolation)
- Rolling-shutter jello is caused by vibration from unbalanced props and motors. — [ArduPilot Cameras and Gimbals](https://ardupilot.org/copter/docs/common-cameras-and-gimbals.html)

### Inferences
- **F450 frequency estimate (not measured):** 920 KV × 11.1 V ≈ 10,200 rpm no-load. A typical F450 all-up weight of about 1.2-1.6 kg needs about 300-400 g per motor, roughly half to two-thirds of the 642 g from the vendor thrust figure. Hover is then very roughly 4,500-6,500 rpm, which is 75-110 Hz shaft and 150-220 Hz blade pass. This matches the ArduPilot "100-200 Hz" band and the 61/122 Hz and 180 Hz examples. The real figure should come from the Pixhawk's own FFT or batch sampler log on the loan drone.
- **Mapping to images:** at 100-200 Hz the vibration period (5-10 ms) is much shorter than a 33 ms frame. With a global shutter and 1-2 ms exposure, each frame catches about 10-40% of a vibration cycle. The result is a small random shift between frames plus a little blur. With rolling-shutter readout of about 16 ms, the same vibration bends rows within the frame. Low-frequency motion (body attitude corrections, 1-10 Hz) causes larger angular rates during manoeuvres and dominates blur at longer exposures.
- VIBE measures linear acceleration at the flight controller, not camera rotation. A camera on a separate mount may vibrate more or less. Logging the companion computer's own IMU (if present) or a small IMU on the camera bracket would measure the real camera vibration. That is unverified for the board.

### Gaps
- No measured angular vibration amplitude (deg or deg/s) at a camera on a 450-class frame was found. Linear amplitude in m/s² does not convert directly to image jitter without knowing the mount's rotational response.
- No measured hover RPM or vibration spectrum was found for the exact F450 + Pixhawk 2 loan kit.

## Mechanical mitigation: soft mounts, gel, resonance, prop balancing, gimbals, ArduPilot measurement

### Takeaway
Fix the source first: balanced props and motors, tight arms and frame, concentric prop adapters. Then isolate the camera with gel or soft dampers tuned so their resonance sits well below the 100-200 Hz prop band. Too soft a mount resonates at low frequency and can amplify vibration. A 2-axis brushless gimbal (about 170-200 g, about €50-175) mainly removes low-frequency attitude motion, but it adds mass and failure modes.

### Cited Findings
- Goal of damping: reduce high and medium frequency vibration while still letting low-frequency board motion follow the airframe. Too much damping is as bad as too little. — [ArduPilot Vibration Damping](https://ardupilot.org/copter/docs/common-vibration-damping.html)
- Materials ranked by ArduPilot: Kyosho Zeal gel tape performs best. Alternatives are silicone gel tape (V10Z62MGT5), Moon Gel ("shown to fail in heat above 100 °F", about 38 °C), 3M, Du-Bro or HobbyKing foam squares of 1-2 cm per corner, O-ring suspension (silicone better than Buna-N), earplug mounts, and 30-durometer Sorbothane at 15-20% compression (it takes a permanent set and is less effective than gel). Sandwiching between pads at about 20% compression improves isolation. — [ArduPilot Vibration Damping](https://ardupilot.org/copter/docs/common-vibration-damping.html)
- Off-the-shelf damper mounts are typically designed for 5-10 times the mass of a flight controller of under 2 oz (57 g). Adding mass to the damped plate can improve damping. One user's 100 g-rated bulb dampers with half an earplug inside reduced vibration to about 0.05 G, and a later version to 0.02 G. — [ArduPilot Vibration Damping](https://ardupilot.org/copter/docs/common-vibration-damping.html)
- Sources to fix: arm and frame flex (rigid arms preferred), loose motor-arm and arm-hub joints, non-concentric prop adapters, unbalanced props and motors (tie-wrap and hot-glue balancing methods), and stiff wiring (use high-flex wire with strain relief). — [ArduPilot Vibration Damping](https://ardupilot.org/copter/docs/common-vibration-damping.html); [PX4](https://docs.px4.io/main/en/assembly/vibration_isolation)
- Camera mounts: isolate camera servos, and use ball joints and bearings with zero free play. Quality servos without slop are "a must" for precision camera work. — [ArduPilot Vibration Damping](https://ardupilot.org/copter/docs/common-vibration-damping.html)
- Mount the camera securely to the gimbal while damping motor vibration. — [ArduPilot Servo Gimbal](https://ardupilot.org/copter/docs/common-camera-gimbal.html)
- A passive mount has a resonance set by stiffness and mass. At resonance, damping does not work and can amplify vibration. Softer damping isolates high frequency better but is more prone to resonance (forum, Pixhawk 2). — [discuss.ardupilot.org](https://discuss.ardupilot.org/t/dealing-with-vibrations-and-harmonics-a-competition)
- Damping pads on a RealSense camera mount were recommended for jitter on a UAV (user forum). — [RealSense community](https://support.realsenseai.com/hc/en-us/community/posts/34240547705619/comments/34241716311699)
- Gimbals: a 2-axis brushless frame with Storm32 controller weighs 170 g, is designed for 60-100 g sports cameras and costs €49.45. The Tarot T-2D is about 195 g (one listing says 540 g, which is inconsistent), about US$87-174, and discontinued. The Feiyu Mini 2D is about US$100 and discontinued. — [openelab Storm32 2-axis](https://openelab.io/cs/products/2-axis-brushless-gimbal-frame); [HobbyKing Tarot T-2D](https://hobbyking.com/tarot-t-2d-v2-gopro-3-brushless-camera-gimbal-and-zyx22-controller.html); [B&H Feiyu Mini 2D](https://www.bhphotovideo.com/c/product/1163612-REG/feiyu_gm_2da_fy_mini_2d_2_axis_aircraft.html)
- Forum opinion: heavy notch or low-pass filtering on the flight controller can leave high-frequency noise reaching a gimbal. — [ArduPilot forum, harmonic notch](https://discuss.ardupilot.org/t/tuning-the-harmonic-notch/48836?page=26)

### Inferences
- **Resonance tuning (textbook vibration theory, not from the fetched sources):**
  - A mass-spring isolator has f_n = (1/2π)·√(k/m). It only attenuates above about √2·f_n and amplifies near f_n.
  - To isolate 100-200 Hz prop vibration, aim for f_n of roughly 20-40 Hz. That is low enough to attenuate the prop band and high enough to stay clear of the flight controller's attitude-control bandwidth (a few Hz to about 10 Hz).
  - In practice, choose dampers rated for the camera-plus-plate mass, or add mass to a light camera plate. A 10-30 g camera on dampers rated for 100+ g will be too stiff.
- A soft camera mount brings a **camera-to-body pose offset that changes in flight**. That matters if pixel positions are later converted using the flight controller's attitude. Logging only pixel positions, as the project does, limits the harm, but it is worth noting for future use.
- A brushless gimbal mainly cancels low-frequency attitude motion (tilt during translation). It does little against 100-200 Hz vibration, which the gimbal's own dampers handle. For a fixed-exposure global-shutter camera looking down, a gimbal's 170-200 g plus controller and wiring may cost more (flight time, payload, complexity, failure modes) than it gains. Servo gimbals add slop and are discouraged for precision work. Any gimbal that uses the Pixhawk's mount outputs would mean configuring a flight-controller peripheral, which counts as "talks to a flight controller" under project rules, so it needs a person's decision.
- **Measurement plan via VIBE:** compare VibeX/Y/Z and Clip counts (and, if enabled, batch-sampler or FFT spectra) between flights. Good targets are below 15 m/s² with Clip = 0. Image-side checks (marker-corner jitter per frame) are needed in addition, because VIBE does not see the camera mount.

### Gaps
- No measured transmissibility data was found for specific gel or damper products with camera-size masses (10-50 g).
- No measured comparison of detection with and without a camera soft mount on a 450 frame was found.
- No Moongel-specific damping data was found beyond the ArduPilot heat warning.

## Lens choice: focal length/FOV vs blur, rigid mounts, autofocus under vibration

### Takeaway
Blur and jitter in pixels scale with focal length in pixels: a wider FOV means less blur per degree of shake, but smaller markers in pixels. Autofocus (VCM) lenses are a poor fit for vibrating platforms, and fixed focus is the vendor recommendation. The Rubik Pi 3 software does not support autofocus on Camera Module 3 anyway.

### Cited Findings
- Autofocus uses a voice coil motor holding a free-moving lens. Under strong vibration "the lens vibrates all over the place". Luxonis advises fixed focus for drone-mounted cameras. The trade-off is that fixed-focus lenses are sharp from about 50 cm to infinity, against 10 cm to infinity for autofocus. — [Luxonis, Auto/Fixed Focus](https://docs.luxonis.com/hardware/platform/sensors/focus-type)
- Patent: UAV vibration can move the lens along the optical axis so focus is unstable during capture. — [USPTO 11092771](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11092771)
- Edmund Optics (application note, vendor): UAVs are harsher than factory machine vision, and conventional machine-vision and cheap consumer lenses "fall short" in these applications. — [Photonics Online / Edmund Optics](https://www.photonicsonline.com/doc/imaging-lenses-for-uavs-0001)
- A longer focal length magnifies motion blur in proportion (a 200 mm lens gives 4× the blur of a 50 mm lens for the same motion). — [motion blur calculator explainer](https://everycalculators.com/how-to-calculate-motion-blur.html)
- Rubik Pi 3: Camera Module 3 (IMX708) autofocus is not supported in the current software. The HQ Camera (IMX477) is listed with an M12 mount. — [Thundercomm Rubik Pi 3 CSI](https://www.thundercomm.com/rubik-pi-3/en/docs/rubik-pi-3-user-manual/1.0.0-u/peripherals-and-interfaces/csi)
- The IMX296 Pi Global Shutter Camera uses C/CS-mount lenses. Some OV9281 modules use M12 lenses, and wide-angle variants exist. — [Farnell](https://uk.farnell.com/raspberry-pi/sc0926/global-shutter-camera-computer/dp/4163984); [Arducam OV9281 wide-angle](https://www.arducam.com/blog/?p=89040)

### Inferences
- Blur in pixels ≈ ω·t·f_px, and marker size in pixels ≈ (marker size / distance)·f_px. So the **blur-to-marker-size ratio (what the 10% ArUco rule cares about) does not depend on focal length** for rotational shake. Focal length then sets detection range and pixels on the marker, while exposure time controls the blur ratio. This is the team's own derivation. It assumes rotation dominates over translation.
- Wide or fisheye lenses add distortion that ArUco corner detection handles poorly near the edges unless images are undistorted. The project already has a camera calibration feature (commit history), which helps.
- Choose fixed-focus lenses with a locked focus ring (thread-locker or set screw on M12 or CS). After focusing at the expected marker distance, a loose M12 lens can drift under vibration. That last point is general practice and was not found in a fetched source.
- Mass and rigidity: a heavy C/CS lens on a small board makes a pendulum that lowers the mount's resonant frequency. M12 lenses are lighter. This is unmeasured reasoning.

### Gaps
- No source quantified focus drift of M12 lenses under drone vibration.
- No sourced recommendation was found for a specific FOV for ArUco detection from a drone at the contest's flight heights. It depends on marker size and altitude, which is a contest-rules question not covered here.
