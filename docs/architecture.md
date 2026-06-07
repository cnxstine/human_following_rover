# Software Architecture Guide

This document outlines the software design, control algorithms, and vision processing pipeline of the Vision-Based Human Following Rover.

---

## 1. Modular Architecture

The repository is built around a decoupled object-oriented model:

```
+--------------------------------------------------------------------------------+
|                                  main.py (Orchestrator)                        |
|   Tracks loop timings, manages GUI windows, updates simulation physics.        |
+------------------------+-------------------------------+-----------------------+
                         |                               |
                         v                               v
+------------------------------------+       +-----------------------------------+
|    camera_tracker.py (Vision)      |       |  follow_controller.py (Control)   |
|   - ThreadedCamera (Picam2/OpenCV) |       |   - State Machine Manager         |
|   - MobileNet SSD (Target Detection)       |   - PD Heading Controller         |
|   - OpenCV Tracker (Target Lock)   |       |   - Proportional Speed Controller |
+------------------------------------+       +-------------------+---------------+
                                                                 |
                                 +-------------------------------+
                                 |
                                 v
+--------------------------------+-----------------------------------------------+
|                        Hardware Interfaces (Physical / Mocked)                 |
|   - motor_controller.py: Sets direction/speed for dual TB6612FNG drivers      |
|   - ultrasonic.py: Reads and filters distances from front/rear HC-SR04s       |
+-------------------------------------------------------------------------------+
```

---

## 2. The Hybrid Vision Pipeline

In a standard Raspberry Pi application, running heavy Convolutional Neural Networks (CNNs) for object detection on every frame leads to low frames-per-second (FPS) and sluggish control response. 

To overcome this, our pipeline splits tasks into two phases:
1. **Target Acquisition (MobileNet SSD)**: Run on initialization or when searching. It analyzes the frame to locate a "person" (Class 15) and draws a bounding box around them.
2. **High-Speed Tracking (OpenCV KCF/CSRT)**: On subsequent frames, instead of running the DNN, we feed the bounding box into a Kernelized Correlation Filter (KCF) tracker. The tracker updates target coordinates at 30 FPS using fraction-of-millisecond calculations.
3. **Drift Calibration**: Periodically (every 45 frames), the DNN is run to recalibrate the tracker's bounding box and eliminate coordinate drift.

---

## 3. Control System Equations

### 3.1 Proportional-Derivative (PD) Steering
The steering control loop regulates heading error (yaw). The target's center $x_{\text{target}}$ is normalized relative to the frame center:

$$e_{\text{steer}}(t) = \frac{x_{\text{target}} - x_{\text{center}}}{x_{\text{center}}}$$

The steering output is:

$$u(t) = K_p \cdot e_{\text{steer}}(t) + K_d \cdot \frac{de_{\text{steer}}(t)}{dt}$$

- **Proportional Gain ($K_p = 0.8$)**: Produces a steering correction proportional to the target's distance from the center.
- **Derivative Gain ($K_d = 0.2$)**: Smooths out rapid oscillation (overshoot) when turning, damping the response as the heading aligns.

### 3.2 Proportional Speed Control
Distance is estimated from the ratio of the target's bounding box height $h_{\text{target}}$ relative to the frame height $H$:

$$e_{\text{speed}}(t) = r_{\text{desired}} - \frac{h_{\text{target}}}{H}$$

The linear speed command is:

$$v(t) = K_{p\_speed} \cdot e_{\text{speed}}(t)$$

- **Moving Forward**: If $e_{\text{speed}}(t) > \text{deadzone}$, the human is far; $v(t) > 0$.
- **Moving Backward**: If $e_{\text{speed}}(t) < -\text{deadzone}$, the human is close; $v(t) < 0$.
- **Braking**: If error is within the deadzone ($\pm 5\%$), the speed is set to 0.

### 3.3 Differential Mixing & Friction Correction
The speed and steering outputs are mixed to calculate individual motor duty cycles:

$$\text{Speed}_{\text{left}} = v(t) + u(t)$$
$$\text{Speed}_{\text{right}} = v(t) - u(t)$$

Before sending these speeds to the drivers, we apply **Friction Correction**. DC motors have static friction and won't turn at low duty cycles (e.g. $< 15\%$). If any non-zero speed falls below $0.15$, we automatically boost it to $\pm 0.15$ to prevent motor stalling and ensure smooth movement at low speeds.

---

## 4. Finite State Machine (FSM)

The system state changes dynamically based on target presence and sensor readings:

1. **INITIALIZING**: Loads the OpenCV DNN Caffe model and starts background threads. Once success is confirmed, transitions to `SEARCHING`.
2. **SEARCHING**: Spins the rover slowly in place ($v_L = -0.3, v_R = 0.3$). Runs detection. If a human is found, transitions to `TRACKING`.
3. **TRACKING**: Stops the wheels. Verifies target lock stability. If the target is tracked successfully for 5 consecutive frames, transitions to `FOLLOWING`.
4. **FOLLOWING**: Activates the PD control loops to drive the motors. If target is lost, transitions to `LOST_TARGET`. If obstacle distance drops below 20 cm in direction of travel, transitions to `BLOCKED`.
5. **BLOCKED**: Halts the wheels ($0.0$). Stays in this state until obstacle distance exceeds 25 cm (hysteresis clearance), then returns to `SEARCHING`.
6. **LOST_TARGET**: Rotates in the last known direction of the target. If target is re-acquired, returns to `TRACKING`. If search exceeds a 10-second timeout, transitions back to `SEARCHING`.
7. **SHUTDOWN**: Stops all motors, closes files, stops camera threads, and safely exits.
