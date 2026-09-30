# AL-KASAV ASTROHEALTH 🚀

### Astronaut Health Monitoring System

**Al Kasav Innovation | NASA Space Apps Challenge 2026**

---

## 🌌 About the Project

**AL-KASAV ASTROHEALTH** is an AI-powered astronaut health monitoring prototype designed to support health awareness and risk monitoring during long-duration space missions.

The system combines:

* AI-based camera movement monitoring
* Simulated astronaut vital signs
* NASA ISS radiation data
* Health trend analysis
* Mission risk assessment
* Automatic health alerts
* ISS, Moon and Mars mission modes

The goal is to demonstrate how artificial intelligence, computer vision, NASA space data and health-monitoring software can work together to support astronauts during space missions.

---

## 🛰️ NASA Space Apps 2026 Challenge

**Challenge:**

> Create Health Monitoring Software for Astronauts on Space Missions

This project was developed as a prototype response to the NASA Space Apps Challenge 2026 challenge.

---

## 🧠 How It Works

The system follows this workflow:

```text
Camera
   ↓
AI Pose / Movement Detection
   ↓
Movement & Coordination Analysis
   ↓
Simulated Vital Signs
   ↓
NASA ISS Radiation Data
   ↓
Health Risk Analysis
   ↓
Overall Health Score
   ↓
Mission Status
   ↓
Alert / Action
```

---

## 🧑‍🚀 Main Features

### 1. AI Movement Monitoring

The system uses **MediaPipe Pose** and OpenCV to detect body landmarks through a webcam.

It monitors:

* Movement
* Balance
* Coordination
* Body activity

---

### 2. Astronaut Vital Signs

The prototype simulates astronaut sensor readings including:

* Heart Rate
* Oxygen Saturation
* Body Temperature

> These vital-sign values are simulated for demonstration purposes and are not real medical measurements.

---

### 3. NASA ISS Radiation Data

The project uses NASA's:

**NASA Open Science Data Repository (OSDR) – RadLab**

and ISS **DosTel** radiation measurements.

The system uses:

* Absorbed radiation dose rate
* Timestamp information

These measurements are displayed in the dashboard and used to demonstrate radiation monitoring.

NASA Data Source:

https://visualization.osdr.nasa.gov/radlab/

> The radiation value is converted into a demonstration risk indicator for visualization. It is not a clinical or official NASA radiation safety limit.

---

## 🌍 Mission Modes

The software includes three demonstration environments:

### 🛰️ ISS Mission

Represents a relatively controlled orbital mission environment.

### 🌙 Moon Mission

Simulates increased mission-related health challenges for lunar exploration.

### 🔴 Mars Mission

Simulates additional long-duration mission challenges such as isolation and increased mission stress.

These Moon and Mars health values are **simulation parameters**, not measurements from astronauts on those missions.

---

## 🚨 Health Risk Engine

The prototype analyses several indicators:

```text
Radiation Risk
Stress Risk
Isolation Risk
Bone Loss Risk
Cardiovascular Risk
Oxygen Level
Movement Activity
```

The system generates:

* LOW risk
* MEDIUM risk
* HIGH risk

and displays a mission health status such as:

* GOOD
* IMPROVING
* MODERATE
* SEVERE
* CRITICAL

---

## 🖥️ Technology Stack

### Programming Language

* Python

### AI / Computer Vision

* OpenCV
* MediaPipe

### GUI

* Tkinter
* Pillow

### NASA Data

* NASA Open Science Data Repository (OSDR)
* NASA RadLab
* ISS DosTel radiation data

### Networking

* Python Requests

---

## 📦 Installation

Clone this repository:

```bash
git clone https://github.com/YOUR-USERNAME/AL-KASAV-ASTROHEALTH.git
```

Enter the project directory:

```bash
cd AL-KASAV-ASTROHEALTH
```

Install the required packages:

```bash
pip install -r requirements.txt
```

---

## 📋 Requirements

Create a file named:

```text
requirements.txt
```

with:

```text
opencv-python
mediapipe
Pillow
requests
```

Python 3.10 or newer is recommended.

---

## ▶️ Run the Project

Run:

```bash
python astrohealth.py
```

Allow camera access when requested.

The system will open the **AL-KASAV ASTROHEALTH** dashboard.

---

## 📷 Demonstration

The dashboard provides:

```text
LIVE CAMERA
      +
AI MOVEMENT MONITOR
      +
ASTRONAUT VITAL SIGNS
      +
NASA RADIATION DATA
      +
HEALTH ANALYSIS
      +
MISSION RISK
      +
ALERT SYSTEM
```

Add project screenshots to the repository inside:

```text
screenshots/
```

Example:

```text
screenshots/dashboard.png
screenshots/nasa-data.png
screenshots/mars-mode.png
```

---

## 🔬 Scientific Scope

This project is an educational and hackathon prototype.

It demonstrates a possible software architecture for integrating:

* Human movement monitoring
* Simulated physiological data
* Space-environment data
* Risk analysis
* Mission health awareness

It is **not a medical device** and should not be used for clinical diagnosis or treatment.

---

## 🔮 Future Development

Future versions could include:

* Real wearable sensor integration
* Real-time heart-rate monitoring
* SpO₂ sensor integration
* Temperature sensors
* ECG integration
* Advanced AI anomaly detection
* Astronaut health history database
* Long-term health trend graphs
* Radiation exposure forecasting
* Offline mission mode
* Ground-control communication
* AI-generated mission recommendations
* More NASA datasets
* Spacecraft environmental sensors

---

## 👨‍🚀 Team

### Al Kasav Innovation

**Lead Developer:**
Al Kasav

**Country:**
Bangladesh

**Focus Areas:**

* Artificial Intelligence
* Computer Vision
* Coding
* Robotics
* Space Science
* Data Analysis
* Astronaut Health Monitoring

---

## 🏆 NASA Space Apps 2026

This project was created for:

**NASA Space Apps Challenge 2026**

Challenge:

**Create Health Monitoring Software for Astronauts on Space Missions**

---

## 📚 Data & Resources

NASA Open Science Data Repository:

https://osdr.nasa.gov/

NASA RadLab:

https://visualization.osdr.nasa.gov/radlab/

NASA Space Apps Challenge:

https://www.spaceappschallenge.org/2026/

---

## 📄 License

This project is provided for educational, research and hackathon purposes.

You are welcome to study, modify and improve the project with appropriate attribution.

---

# 🚀 AL-KASAV ASTROHEALTH

### Monitor → Analyze → Detect Risk → Alert → Act

**Al Kasav Innovation**
**Bangladesh 🇧🇩**
