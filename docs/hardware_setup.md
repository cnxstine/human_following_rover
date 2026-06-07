# Hardware Setup & Wiring Guide

This document specifies the electrical connections, GPIO mappings, and power distribution layout for the Vision-Based Human Following Rover.

---

## 1. GPIO Pin Mapping Table

| Component | Pin Function | Raspberry Pi GPIO Pin (Physical Pin) | Notes |
| :--- | :--- | :--- | :--- |
| **TB6612 #1**<br>*(Left Motors)* | PWMA | GPIO 12 (Pin 32) | Hardware PWM Channel 0 |
| | AIN1 | GPIO 5 (Pin 29) | Digital Output |
| | AIN2 | GPIO 6 (Pin 31) | Digital Output |
| | PWMB | GPIO 13 (Pin 33) | Hardware PWM Channel 1 |
| | BIN1 | GPIO 16 (Pin 36) | Digital Output |
| | BIN2 | GPIO 20 (Pin 38) | Digital Output |
| | STBY | GPIO 21 (Pin 40) | Driver Enable |
| **TB6612 #2**<br>*(Right Motors)*| PWMA | GPIO 18 (Pin 12) | Hardware PWM Channel 0 (Alt) |
| | AIN1 | GPIO 23 (Pin 16) | Digital Output |
| | AIN2 | GPIO 24 (Pin 18) | Digital Output |
| | PWMB | GPIO 19 (Pin 35) | Hardware PWM Channel 1 (Alt) |
| | BIN1 | GPIO 25 (Pin 22) | Digital Output |
| | BIN2 | GPIO 26 (Pin 37) | Digital Output |
| | STBY | GPIO 14 (Pin 8) | Driver Enable |
| **Front Ultrasonic** | TRIG | GPIO 17 (Pin 11) | Trigger Pulse |
| | ECHO | GPIO 27 (Pin 13) | Input Echo |
| **Rear Ultrasonic** | TRIG | GPIO 22 (Pin 15) | Trigger Pulse |
| | ECHO | GPIO 4 (Pin 7) | Input Echo |
| **Pi Camera** | CSI | Ribbon Cable Interface | Picamera2 OV5647 5MP |

---

## 2. Power Distribution Architecture

> [!IMPORTANT]
> **Logic Power vs. Motor Power Separation**
> To prevent voltage drops (brownouts) and high-frequency electrical noise from resetting the Raspberry Pi, it is critical to separate the power sources:
> 1. **Pi & Logic Power**: 5V/3A buck converter powered from a 2S/3S LiPo battery, or a dedicated 5V power bank connected via USB-C.
> 2. **Motor Power (VM)**: Connect VM pins on both TB6612FNG drivers directly to a 2S LiPo battery (7.4V - 8.4V) or 6x AA rechargeable batteries.
> 3. **Common Ground**: All grounds (GND) from the batteries, Raspberry Pi, and motor drivers **MUST** be connected together to form a common electrical reference frame.

---

## 3. TB6612FNG Driver Layout

```
                        TB6612FNG Pinout Connection
                     +-------------------------------+
       (Pi GPIO 5)   | AIN1                     VM   | <-- Battery Motor Power (7.4V - 8.4V)
       (Pi GPIO 6)   | AIN2                    VCC   | <-- Pi 5V Logic Power
       (Pi GPIO 12)  | PWMA                    GND   | <-- Common Ground
  (Left Motor Front) | AO1                    AO1    | <-- (Left Motor Front)
  (Left Motor Front) | AO2                    AO2    | <-- (Left Motor Front)
  (Left Motor Rear)  | BO2                    BO2    | <-- (Left Motor Rear)
  (Left Motor Rear)  | BO1                    BO1    | <-- (Left Motor Rear)
       (Pi GPIO 13)  | PWMB                    GND   | <-- Common Ground
       (Pi GPIO 16)  | BIN1                    VM    | <-- Battery Motor Power
       (Pi GPIO 20)  | BIN2                    VCC   | <-- Pi 5V Logic Power
       (Pi GPIO 21)  | STBY                    GND   | <-- Common Ground
                     +-------------------------------+
```

---

## 4. Ultrasonic Sensor Voltage Dividers

> [!CAUTION]
> **5V Sensor Echo to 3.3V Pi GPIO Protection**
> The HC-SR04 sensors are powered by 5V and output a 5V logic signal on their ECHO pin. Connecting this directly to the Raspberry Pi's 3.3V GPIO pins can permanently damage the Pi.
> Use a simple voltage divider circuit for the **ECHO** pin of both sensors:
> 
> ```
> HC-SR04 ECHO Pin (5V) --- [ 1k Ohm Resistor ] ---+--- GPIO Pin (3.3V)
>                                                  |
>                                          [ 2k Ohm Resistor ]
>                                                  |
> HC-SR04 GND Pin   -------------------------------+--- RPi GND Pin
> ```
