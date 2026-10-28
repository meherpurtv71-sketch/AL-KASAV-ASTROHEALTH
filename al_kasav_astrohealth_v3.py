"""
AL KASAV INNOVATION
AL-KASAV ASTROHEALTH V3 • AI DIGITAL TWIN
NASA SPACE APPS CHALLENGE 2026

NASA DATA SOURCE: NASA OSDR - RadLab - ISS - DosTel

Install:  pip install opencv-python mediapipe pillow requests

NOTE: Demo / educational software. NOT a medical diagnostic device.
      Simulated values are not real measurements. The "Health Count"
      is a gamified demo indicator (vitals score + exercise bonus).
"""

import csv
import io
import math
import random
import threading
import time
import datetime
from collections import deque
import tkinter as tk
from tkinter import messagebox, filedialog

import cv2
import mediapipe as mp
import requests
from PIL import Image, ImageTk

# ============================================================
# COLORS / FONT
# ============================================================
BG = "#050d18"
PANEL = "#0b2036"
PANEL2 = "#0a2540"
CARD = "#09182b"
BORDER = "#1c4a6e"
TRACK = "#0f2a44"
CYAN = "#22d3ee"
TXT = "#e2e8f0"
MUTED = "#94a3b8"
GREEN = "#4ade80"
YELLOW = "#facc15"
RED = "#f87171"
BLUE = "#38bdf8"
FONT = "Segoe UI"

# ============================================================
# MAIN WINDOW
# ============================================================
root = tk.Tk()
root.title("AL-KASAV ASTROHEALTH V3 | AI DIGITAL TWIN | NASA Space Apps 2026")
root.geometry("1560x920")
root.configure(bg=BG)
try:
    root.state("zoomed")
except Exception:
    pass

# ============================================================
# EXERCISE DEFINITIONS
# ============================================================
EXERCISES = [
    ("arm", "ARM RAISE", "Raise BOTH arms above your shoulders, then lower"),
    ("knee", "HIGH KNEE", "Lift one knee up to hip height, then lower"),
    ("squat", "SQUAT / LEG BEND", "Bend both knees, then stand straight"),
    ("bend", "SIDE BEND", "Lean your upper body left or right, then centre"),
]
EX_KEYS = [e[0] for e in EXERCISES]
# (up-threshold, down-threshold) on a 0-100 smoothed signal
EX_THRESH = {"arm": (70, 25), "knee": (70, 25), "squat": (55, 20), "bend": (40, 12)}

# ============================================================
# STATE VARIABLES
# ============================================================
heart = tk.IntVar(value=76)
spo2 = tk.IntVar(value=95)
temperature = tk.DoubleVar(value=36.7)
stress = tk.IntVar(value=20)
fatigue = tk.IntVar(value=15)
movement = tk.IntVar(value=0)
isolation = tk.IntVar(value=20)
bone = tk.IntVar(value=20)
cardio = tk.IntVar(value=20)
radiation = tk.DoubleVar(value=0.0)

bp_sys_val = {"v": None}
bp_dia_val = {"v": None}

health = tk.DoubleVar(value=0.0)          # vitals-based score
total_health = tk.DoubleVar(value=0.0)    # vitals + exercise bonus ("Health Count")
ex_pct = tk.DoubleVar(value=0.0)
stage = tk.StringVar(value="GOOD")
risk = tk.StringVar(value="LOW")
alert = tk.StringVar(value="System ready.")
mission = tk.StringVar(value="ISS MISSION")
data_mode = tk.StringVar(value="SIMULATION")
recommend = tk.StringVar(value="")
banner = tk.StringVar(value="")

nasa_status = tk.StringVar(value="NASA OSDR: CONNECTING...")
nasa_dose = tk.StringVar(value="NASA Dose: Loading...")
nasa_time = tk.StringVar(value="NASA Timestamp: --")
nasa_count = tk.StringVar(value="Readings: 0")
conn_summary = tk.StringVar(value="NOT CONNECTED • NO VERIFIED READING")
camera_status = tk.StringVar(value="AI CAMERA: STARTING...")
human_detected = {"v": False}

# profile
p_name = tk.StringVar(value="Astronaut Demo")
p_id = tk.StringVar(value="AK-001")
p_age = tk.StringVar(value="35")
p_height = tk.StringVar(value="175")
p_weight = tk.StringVar(value="70")
p_bmi = tk.StringVar(value="BMI: --")

# header clocks
clock_utc = tk.StringVar(value="UTC --:--:--")
clock_met = tk.StringVar(value="MET 00:00:00")
APP_START = time.time()

# exercise state
ex_target = tk.IntVar(value=10)
ex_count = {k: 0 for k in EX_KEYS}
ex_phase = {k: "down" for k in EX_KEYS}
ex_signal = {k: 0.0 for k in EX_KEYS}
ex_state = {"active": False, "t0": 0.0, "acc": 0.0, "achieved": False}
ex_status = tk.StringVar(value="READY")

# history / logs
HIST = 90
hr_hist = deque(maxlen=HIST)
spo2_hist = deque(maxlen=HIST)
health_hist = deque(maxlen=HIST)
temp_hist = deque(maxlen=HIST)
csv_rows = []
alert_log = []
last_alert = {"v": ""}
log_box = None          # created later
report_box = None       # created later


def get_target():
    try:
        return max(1, min(int(ex_target.get()), 99))
    except Exception:
        return 10


def log_event(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"{ts}  {msg}"
    alert_log.append(line)
    if len(alert_log) > 300:
        alert_log.pop(0)
    if log_box is not None:
        log_box.insert(0, line)
        if log_box.size() > 300:
            log_box.delete(300, "end")


# ============================================================
# NASA RADLAB
# ============================================================
NASA_API = "https://visualization.osdr.nasa.gov/radlab/api/"
NASA_PARAMS = {
    "spacecraft": "ISS",
    "instrument": "DosTel",
    "timestamp>": "2022-04-01T23:00",
    "timestamp<": "2022-04-02T01:05",
    "absorbed_dose_rate": "",
    "format": "csv",
}
nasa_readings = []
nasa_index = {"i": 0, "job": None}


def download_nasa_data():
    global nasa_readings
    try:
        r = requests.get(NASA_API, params=NASA_PARAMS, timeout=15)
        r.raise_for_status()
        text = r.text.strip()
        if not text:
            raise Exception("NASA API returned empty data.")
        reader = csv.DictReader(io.StringIO(text))
        readings = []
        for row in reader:
            dose, ts = None, ""
            for k in row:
                if k.lower() == "absorbed_dose_rate":
                    try:
                        dose = float(row[k])
                    except Exception:
                        pass
                if k.lower() == "timestamp":
                    ts = row[k]
            if dose is not None:
                readings.append({"dose": dose, "timestamp": ts})
        if not readings:
            raise Exception("No radiation readings found.")
        nasa_readings = readings
        root.after(0, nasa_success)
    except Exception as e:
        print("NASA DATA ERROR:", e)
        root.after(0, nasa_failed)


def nasa_success():
    nasa_status.set("NASA OSDR: CONNECTED")
    nasa_status_label.config(fg=GREEN)
    nasa_count.set(f"NASA DosTel readings: {len(nasa_readings)}")
    nasa_index["i"] = 0
    if nasa_index["job"]:
        root.after_cancel(nasa_index["job"])
    log_event(f"NASA RadLab data loaded ({len(nasa_readings)} readings)")
    update_nasa_reading()


def nasa_failed():
    nasa_status.set("NASA OSDR: OFFLINE")
    nasa_status_label.config(fg=RED)
    nasa_dose.set("NASA data unavailable")
    nasa_time.set("Using demonstration fallback")
    nasa_count.set("Readings: 0")
    radiation.set(round(random.uniform(10, 60), 2))
    log_event("NASA data offline - demo fallback radiation value used")
    refresh_all()


def update_nasa_reading():
    if not nasa_readings:
        return
    i = nasa_index["i"] % len(nasa_readings)
    d = nasa_readings[i]
    # Visualization score only - NOT a medical radiation limit.
    radiation.set(round(min(100, max(0, d["dose"] * 20)), 2))
    nasa_dose.set(f"NASA Absorbed Dose: {d['dose']:.4f} μGy/h")
    nasa_time.set(f"NASA Timestamp: {d['timestamp']}")
    nasa_count.set(f"NASA DosTel readings: {len(nasa_readings)}  •  sample {i + 1}")
    nasa_index["i"] = i + 1
    refresh_all()
    nasa_index["job"] = root.after(3000, update_nasa_reading)


def refresh_nasa():
    nasa_status.set("NASA OSDR: CONNECTING...")
    nasa_status_label.config(fg=YELLOW)
    threading.Thread(target=download_nasa_data, daemon=True).start()


# ============================================================
# HELPERS
# ============================================================
def clamp(v, lo=0, hi=100):
    return max(lo, min(v, hi))


def range_score(v, lo, hi, slope):
    if lo <= v <= hi:
        return 100
    d = lo - v if v < lo else v - hi
    return clamp(100 - d * slope)


def risk_color(v):
    return "#16c60c" if v < 40 else ("#eab308" if v < 70 else "#ef4444")


def level_color(v):
    return GREEN if v >= 65 else (YELLOW if v >= 45 else RED)


# ============================================================
# EXERCISE ENGINE
# ============================================================
def exercise_pct():
    t = get_target()
    return sum(min(ex_count[k] / t, 1.0) for k in EX_KEYS) / len(EX_KEYS) * 100


def exercise_signals():
    return {
        "arm": min(part_scores["LEFT ARM RAISE"], part_scores["RIGHT ARM RAISE"]),
        "knee": max(part_scores["LEFT KNEE LIFT"], part_scores["RIGHT KNEE LIFT"]),
        "squat": min(part_scores["LEFT LEG BEND"], part_scores["RIGHT LEG BEND"]),
        "bend": part_scores["TORSO MOVEMENT"],
    }


def ex_elapsed():
    t = ex_state["acc"]
    if ex_state["active"]:
        t += time.time() - ex_state["t0"]
    return t


def detect_reps():
    """Counts a repetition when the signal passes the UP threshold after
    having been below the DOWN threshold."""
    sig = exercise_signals()
    for k in EX_KEYS:
        ex_signal[k] = sig[k]
        hi, lo = EX_THRESH[k]
        if ex_phase[k] == "down" and sig[k] >= hi:
            ex_phase[k] = "up"
            ex_count[k] += 1
            if ex_count[k] == get_target():
                log_event(f"Exercise goal reached: {dict((e[0], e[1]) for e in EXERCISES)[k]}")
        elif ex_phase[k] == "up" and sig[k] <= lo:
            ex_phase[k] = "down"


def start_exercise():
    if not ex_state["active"]:
        sig = exercise_signals()
        for k in EX_KEYS:
            # begin in "up" if the body is already in that position,
            # so no false repetition is counted at the start
            ex_phase[k] = "up" if sig[k] > EX_THRESH[k][1] else "down"
        ex_state["t0"] = time.time()
        ex_state["active"] = True
        ex_status.set("● ACTIVE")
        log_event("Exercise session started")
    refresh_all()


def pause_exercise():
    if ex_state["active"]:
        ex_state["acc"] += time.time() - ex_state["t0"]
        ex_state["active"] = False
        ex_status.set("❚❚ PAUSED")
        log_event("Exercise session paused")
    refresh_all()


def reset_exercise():
    ex_state.update(active=False, acc=0.0, t0=0.0, achieved=False)
    for k in EX_KEYS:
        ex_count[k] = 0
        ex_phase[k] = "down"
    for n in PART_NAMES:
        part_scores[n] = 0.0
    movement.set(0)
    ex_status.set("READY")
    banner.set("")
    log_event("Exercise counters reset")
    refresh_all()


def exercise_kcal():
    # very rough demonstration estimate only
    return sum(ex_count.values()) * 0.4


# ============================================================
# HEALTH ENGINE
# ============================================================
def calculate_health():
    scores = [
        range_score(heart.get(), 60, 100, 3),
        clamp((spo2.get() - 85) / 15 * 100),
        range_score(temperature.get(), 36.1, 37.5, 40),
        100 - stress.get(),
        100 - fatigue.get(),
        100 - min(radiation.get(), 100),
    ]
    if bp_sys_val["v"] is not None and bp_dia_val["v"] is not None:
        scores.append(range_score(bp_sys_val["v"], 90, 129, 3))
        scores.append(range_score(bp_dia_val["v"], 60, 84, 3))
    if human_detected["v"]:
        scores.append(movement.get())

    score = round(sum(scores) / len(scores), 1)
    health.set(score)

    # ---- exercise bonus -> total "Health Count"
    pct = exercise_pct()
    ex_pct.set(round(pct, 1))
    if pct >= 99.99:
        total = 100.0
    else:
        total = round(score + (100 - score) * pct / 100, 1)
    total_health.set(total)

    if score < 25:
        stage.set("CRITICAL")
    elif score < 45:
        stage.set("SEVERE")
    elif score < 65:
        stage.set("MODERATE")
    elif score < 85:
        stage.set("IMPROVING")
    else:
        stage.set("GOOD")

    alerts = []
    if heart.get() > 100:
        alerts.append("High heart rate")
    elif heart.get() < 60:
        alerts.append("Low heart rate")
    if spo2.get() < 94:
        alerts.append("Low SpO₂")
    if temperature.get() > 37.8:
        alerts.append("Raised temperature")
    elif temperature.get() < 35.5:
        alerts.append("Low temperature")
    if bp_sys_val["v"] is not None and (bp_sys_val["v"] >= 140 or bp_sys_val["v"] < 90):
        alerts.append("Blood pressure out of range")

    mx = max(stress.get(), fatigue.get(), isolation.get(),
             bone.get(), cardio.get(), radiation.get())
    if mx >= 70 or len(alerts) >= 2:
        risk.set("HIGH")
        alert.set("WARNING: " + (", ".join(alerts) if alerts else
                                 "Mission health indicators require attention."))
    elif mx >= 40 or alerts:
        risk.set("MEDIUM")
        alert.set("CAUTION: " + (", ".join(alerts) if alerts else
                                 "Continue astronaut health monitoring."))
    else:
        risk.set("LOW")
        alert.set("No major simulated alert.")

    if alert.get() != last_alert["v"]:
        last_alert["v"] = alert.get()
        log_event(f"[{risk.get()}] {alert.get()}")

    recommend.set(build_recommendations())

    # ---- 100% achievement
    if pct >= 99.99 and not ex_state["achieved"]:
        ex_state["achieved"] = True
        banner.set("★ 100% HEALTH COUNT ACHIEVED — EXERCISE GOAL COMPLETE ★")
        log_event("100% Health Count achieved (exercise goal complete)")
        try:
            root.bell()
        except Exception:
            pass
    elif pct < 99.99 and ex_state["achieved"]:
        ex_state["achieved"] = False
        banner.set("")


def build_recommendations():
    tips = []
    if heart.get() > 100:
        tips.append("Heart rate is high: rest a few minutes and re-measure.")
    if spo2.get() < 94:
        tips.append("SpO₂ is low: check the sensor fit and cabin air / ventilation.")
    if temperature.get() > 37.8:
        tips.append("Temperature is raised: hydrate, rest and monitor.")
    if bone.get() >= 40:
        tips.append("Bone-loss risk: schedule resistance / weight-bearing exercise.")
    if cardio.get() >= 40:
        tips.append("Cardio risk: add aerobic exercise sessions.")
    if stress.get() >= 40:
        tips.append("Stress: breathing exercises, short breaks, crew contact.")
    if isolation.get() >= 40:
        tips.append("Isolation: schedule calls with family / ground team.")
    if fatigue.get() >= 50:
        tips.append("Fatigue: keep a regular sleep schedule.")
    if radiation.get() >= 40:
        tips.append("Radiation score elevated: use shielded areas, track dose.")
    if ex_pct.get() < 100:
        tips.append("Complete the exercise goal to raise the Health Count to 100%.")
    if not tips:
        tips.append("All indicators are within the demo normal range. Keep it up!")
    return "\n".join("• " + t for t in tips[:6]) + "\n(Demo guidance — not medical advice.)"


def refresh_all():
    calculate_health()
    update_ui()


# ============================================================
# SIMULATION & MISSIONS
# ============================================================
MISSION_RANGES = {
    "ISS MISSION": dict(stress=(5, 45), fatigue=(5, 40), isolation=(5, 50), bone=(5, 60), cardio=(5, 60)),
    "MOON MISSION": dict(stress=(10, 65), fatigue=(10, 60), isolation=(15, 75), bone=(20, 80), cardio=(10, 70)),
    "MARS MISSION": dict(stress=(25, 85), fatigue=(20, 80), isolation=(30, 95), bone=(30, 90), cardio=(20, 85)),
}

MISSION_INFO = {
    "ISS MISSION": [
        ("GRAVITY", "Microgravity (≈ 0 g felt)"),
        ("DISTANCE", "≈ 400 km altitude • ~90 min per orbit"),
        ("COMMUNICATION", "Near real-time (relay satellites)"),
        ("TYPICAL DURATION", "~6 months (some ~1 year)"),
        ("RADIATION", "Low Earth orbit, partly shielded by Earth's magnetosphere"),
        ("MAIN HEALTH RISKS", "Bone & muscle loss, fluid shift, cardio deconditioning"),
    ],
    "MOON MISSION": [
        ("GRAVITY", "≈ 0.16 g (one-sixth of Earth)"),
        ("DISTANCE", "≈ 384,400 km from Earth"),
        ("COMMUNICATION", "≈ 1.3 s one-way delay"),
        ("TYPICAL DURATION", "Days to weeks (Artemis-class missions)"),
        ("RADIATION", "No magnetosphere: higher cosmic-ray / solar-particle exposure"),
        ("MAIN HEALTH RISKS", "Lunar dust, radiation, reduced gravity, stress"),
    ],
    "MARS MISSION": [
        ("GRAVITY", "≈ 0.38 g (about 38% of Earth)"),
        ("DISTANCE", "≈ 55 to 400 million km (varies)"),
        ("COMMUNICATION", "≈ 3 to 22 min one-way delay"),
        ("TYPICAL DURATION", "~2–3 years round trip (planned concepts)"),
        ("RADIATION", "Cosmic rays + solar events; thin atmosphere, little shielding"),
        ("MAIN HEALTH RISKS", "Isolation, long microgravity transit, radiation, bone loss"),
    ],
}
mission_info_vars = {k: tk.StringVar(value="--") for k, _ in MISSION_INFO["ISS MISSION"]}


def update_mission_info():
    for k, v in MISSION_INFO[mission.get()]:
        mission_info_vars[k].set(v)


def apply_mission_risks():
    r = MISSION_RANGES[mission.get()]
    stress.set(random.randint(*r["stress"]))
    fatigue.set(random.randint(*r["fatigue"]))
    isolation.set(random.randint(*r["isolation"]))
    bone.set(random.randint(*r["bone"]))
    cardio.set(random.randint(*r["cardio"]))


def generate_simulated_vitals():
    data_mode.set("SIMULATION")
    bp_sys_val["v"] = None
    bp_dia_val["v"] = None
    heart.set(random.randint(60, 100))
    spo2.set(random.randint(94, 99))
    temperature.set(round(random.uniform(36.1, 37.5), 1))
    apply_mission_risks()
    conn_summary.set("NOT CONNECTED • NO VERIFIED READING")
    log_event("Simulated vitals generated")
    refresh_all()


def set_mission(name):
    mission.set(name)
    apply_mission_risks()
    update_mission_info()
    log_event(f"Mission mode: {name}")
    refresh_all()


def sim_tick():
    """Slow drift of simulated vitals (only in SIMULATION mode)."""
    if data_mode.get() == "SIMULATION":
        heart.set(int(clamp(heart.get() + random.randint(-2, 2), 58, 105)))
        spo2.set(int(clamp(spo2.get() + random.choice([-1, 0, 0, 1]), 93, 99)))
        temperature.set(round(clamp(temperature.get() + random.uniform(-0.1, 0.1), 36.1, 37.6), 1))
        stress.set(int(clamp(stress.get() + random.randint(-3, 3))))
        fatigue.set(int(clamp(fatigue.get() + random.randint(-3, 3))))
    root.after(2000, sim_tick)


# ============================================================
# POSE (MediaPipe)
# ============================================================
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, model_complexity=1,
                    min_detection_confidence=0.6, min_tracking_confidence=0.6)
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

PART_NAMES = [
    "LEFT ARM RAISE", "RIGHT ARM RAISE", "LEFT KNEE LIFT", "RIGHT KNEE LIFT",
    "LEFT LEG BEND", "RIGHT LEG BEND", "TORSO MOVEMENT", "FULL BODY MOBILITY",
]
part_scores = {n: 0.0 for n in PART_NAMES}


def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def angle(a, b, c):
    ab = (a.x - b.x, a.y - b.y)
    cb = (c.x - b.x, c.y - b.y)
    dot = ab[0] * cb[0] + ab[1] * cb[1]
    n = math.hypot(*ab) * math.hypot(*cb)
    if n == 0:
        return 180
    return math.degrees(math.acos(clamp(dot / n, -1, 1)))


def vis(*pts):
    return all(p.visibility > 0.4 for p in pts)


def arm_raise(sh, el, wr):
    if not vis(sh, wr):
        return 0
    length = dist(sh, el) + dist(el, wr)
    if length == 0:
        return 0
    v = (sh.y - wr.y) / length
    return clamp((v + 1) * 50)


def knee_lift(hip, knee):
    if not vis(hip, knee):
        return 0
    L = dist(hip, knee)
    if L == 0:
        return 0
    return clamp((1 - (knee.y - hip.y) / L) * 100)


def leg_bend(hip, knee, ank):
    if not vis(hip, knee, ank):
        return 0
    return clamp((180 - angle(hip, knee, ank)) / 90 * 100)


def smooth(name, value, a=0.35):
    part_scores[name] = part_scores[name] * (1 - a) + value * a
    return part_scores[name]


def process_pose(lm):
    L = mp_pose.PoseLandmark
    g = lambda p: lm[p.value]
    ls, rs = g(L.LEFT_SHOULDER), g(L.RIGHT_SHOULDER)
    le, re = g(L.LEFT_ELBOW), g(L.RIGHT_ELBOW)
    lw, rw = g(L.LEFT_WRIST), g(L.RIGHT_WRIST)
    lh, rh = g(L.LEFT_HIP), g(L.RIGHT_HIP)
    lk, rk = g(L.LEFT_KNEE), g(L.RIGHT_KNEE)
    la, ra = g(L.LEFT_ANKLE), g(L.RIGHT_ANKLE)

    smooth("LEFT ARM RAISE", arm_raise(ls, le, lw))
    smooth("RIGHT ARM RAISE", arm_raise(rs, re, rw))
    smooth("LEFT KNEE LIFT", knee_lift(lh, lk))
    smooth("RIGHT KNEE LIFT", knee_lift(rh, rk))
    smooth("LEFT LEG BEND", leg_bend(lh, lk, la))
    smooth("RIGHT LEG BEND", leg_bend(rh, rk, ra))

    sx, sy = (ls.x + rs.x) / 2, (ls.y + rs.y) / 2
    hx, hy = (lh.x + rh.x) / 2, (lh.y + rh.y) / 2
    torso_len = math.hypot(sx - hx, sy - hy) or 1
    tilt = abs(sx - hx) / torso_len
    smooth("TORSO MOVEMENT", clamp(tilt * 250))

    limbs = [part_scores[n] for n in PART_NAMES[:7]]
    smooth("FULL BODY MOBILITY", sum(limbs) / len(limbs))
    movement.set(int(part_scores["FULL BODY MOBILITY"]))

    if ex_state["active"]:
        detect_reps()


# ============================================================
# REPORT / EXPORT
# ============================================================
def bmi_text():
    try:
        h = float(p_height.get()) / 100
        w = float(p_weight.get())
        b = w / (h * h)
        cat = ("Underweight" if b < 18.5 else "Normal" if b < 25
               else "Overweight" if b < 30 else "Obese range")
        return f"BMI: {b:.1f} ({cat})"
    except Exception:
        return "BMI: --"


def build_report():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bp = "--"
    if bp_sys_val["v"] is not None and bp_dia_val["v"] is not None:
        bp = f"{bp_sys_val['v']:.0f}/{bp_dia_val['v']:.0f} mmHg"
    m, s = divmod(int(ex_elapsed()), 60)
    names = dict((e[0], e[1]) for e in EXERCISES)
    L = [
        "AL-KASAV ASTROHEALTH V3 • HEALTH REPORT",
        "=" * 52,
        f"Date/Time   : {now}",
        f"Astronaut   : {p_name.get()} ({p_id.get()})  Age {p_age.get()}",
        f"Body        : {p_height.get()} cm / {p_weight.get()} kg  •  {bmi_text()}",
        f"Mission     : {mission.get()}",
        f"Data mode   : {data_mode.get()}",
        "",
        "VITAL SIGNS",
        f"  Heart rate   : {heart.get()} BPM",
        f"  SpO2         : {spo2.get()} %",
        f"  Temperature  : {temperature.get()} °C",
        f"  Blood press. : {bp}",
        "",
        "RISK INDICATORS (0-100)",
        f"  Stress       : {stress.get()}",
        f"  Fatigue      : {fatigue.get()}",
        f"  Isolation    : {isolation.get()}",
        f"  Bone loss    : {bone.get()}",
        f"  Cardio       : {cardio.get()}",
        f"  Radiation    : {radiation.get():.1f}   ({nasa_dose.get()})",
        f"  Movement     : {movement.get()} %",
        "",
        f"EXERCISE  (target {get_target()} reps each)  time {m:02d}:{s:02d}",
    ]
    for k in EX_KEYS:
        L.append(f"  {names[k]:<18}: {ex_count[k]} / {get_target()}")
    L += [
        f"  Exercise complete : {ex_pct.get():.0f} %",
        "",
        f"VITALS HEALTH SCORE : {health.get():.1f}  ({stage.get()})",
        f"HEALTH COUNT        : {total_health.get():.1f} %",
        f"RISK LEVEL          : {risk.get()}",
        f"ALERT               : {alert.get()}",
        "",
        "RECOMMENDATIONS",
        recommend.get(),
        "",
        "NOTE: Demo / educational tool. Simulated values are not real",
        "measurements and this report is NOT a medical diagnosis.",
    ]
    return "\n".join(L)


def refresh_report():
    if report_box is not None:
        report_box.config(state="normal")
        report_box.delete("1.0", "end")
        report_box.insert("1.0", build_report())
        report_box.config(state="disabled")


def save_report():
    p = filedialog.asksaveasfilename(defaultextension=".txt",
                                     filetypes=[("Text file", "*.txt")])
    if p:
        with open(p, "w", encoding="utf-8") as f:
            f.write(build_report())
        messagebox.showinfo("Saved", "Report saved.")


def export_csv():
    if not csv_rows:
        messagebox.showwarning("No data", "No samples recorded yet.")
        return
    p = filedialog.asksaveasfilename(defaultextension=".csv",
                                     filetypes=[("CSV file", "*.csv")])
    if p:
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["time", "mode", "mission", "heart_bpm", "spo2", "temp_c",
                        "stress", "fatigue", "radiation", "movement",
                        "vitals_health", "health_count", "exercise_pct"])
            w.writerows(csv_rows)
        messagebox.showinfo("Saved", f"{len(csv_rows)} samples exported.")


def show_report():
    show_page("ai")
    refresh_report()


def show_safety():
    messagebox.showinfo(
        "SAFETY",
        "This software is a demonstration / educational prototype.\n\n"
        "• Simulated data are NOT real measurements.\n"
        "• The radiation score is only a visualization indicator,\n"
        "  not a medical radiation limit.\n"
        "• The Health Count is a gamified demo value\n"
        "  (vitals score + exercise bonus).\n"
        "• Do not use it for diagnosis or treatment decisions.")


def show_about():
    messagebox.showinfo(
        "SYSTEM",
        "AL-KASAV ASTROHEALTH V3 • AI DIGITAL TWIN\n"
        "AL KASAV INNOVATION\nNASA Space Apps Challenge 2026\n\n"
        "NASA data: OSDR • RadLab • ISS • DosTel")


def close_app():
    try:
        cap.release()
        pose.close()
        cv2.destroyAllWindows()
    except Exception:
        pass
    root.destroy()


# ============================================================
# REUSABLE WIDGETS
# ============================================================
def heading(parent, text, color="white", size=14):
    return tk.Label(parent, text=text, font=(FONT, size, "bold"), fg=color,
                    bg=parent["bg"], anchor="w")


def flat_button(parent, text, cmd, bg, fg="black", size=10, padx=12, pady=6):
    return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                     font=(FONT, size, "bold"), relief="flat", padx=padx, pady=pady,
                     activebackground=bg, cursor="hand2")


class Bar:
    def __init__(self, parent, label, bg, label_w=19, track="white", height=22,
                 fill="#16c60c", padx=12):
        self.fill = fill
        self.h = height
        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x", padx=padx, pady=3)
        tk.Label(row, text=label, width=label_w, anchor="w", font=(FONT, 8, "bold"),
                 fg="white", bg=bg).pack(side="left")
        self.cv = tk.Canvas(row, height=height, bg=track, highlightthickness=0)
        self.cv.pack(side="left", fill="x", expand=True, padx=6)
        self.pl = tk.Label(row, text="0%", width=6, font=(FONT, 8, "bold"), fg=CYAN, bg=bg)
        self.pl.pack(side="left")

    def set(self, v, color=None, text=None):
        w = self.cv.winfo_width()
        self.cv.delete("all")
        if v > 1 and w > 4:
            self.cv.create_rectangle(2, 2, 2 + (w - 4) * min(v, 100) / 100, self.h - 2,
                                     fill=color or self.fill, outline="")
        self.pl.config(text=text or f"{int(v)}%",
                       fg=GREEN if v >= 90 else (YELLOW if v >= 30 else CYAN))


def draw_gauge(cv, value, label, color):
    cv.delete("all")
    w = int(cv["width"])
    h = int(cv["height"])
    pad = 16
    box = (pad, pad, w - pad, h - pad)
    cv.create_oval(*box, outline="#12324f", width=14)
    if value > 0.1:
        cv.create_arc(*box, start=90, extent=-min(359.9, 3.599 * value),
                      style="arc", outline=color, width=14)
    shown = "100%" if value >= 99.95 else f"{math.floor(value)}%"
    cv.create_text(w / 2, h / 2 - 8, text=shown, fill="white", font=(FONT, 28, "bold"))
    cv.create_text(w / 2, h / 2 + 24, text=label, fill=MUTED, font=(FONT, 8, "bold"))


def draw_chart(cv, data, lo, hi, color, title, unit=""):
    cv.delete("all")
    w, h = cv.winfo_width(), cv.winfo_height()
    if w < 30 or h < 30:
        return
    for i in range(1, 4):
        y = h * i / 4
        cv.create_line(0, y, w, y, fill="#12324f")
    cv.create_text(8, 6, anchor="nw", text=title, fill=MUTED, font=(FONT, 8, "bold"))
    if len(data) < 2:
        return
    step = w / (HIST - 1)
    n = len(data)
    pts = []
    for i, v in enumerate(data):
        x = w - (n - 1 - i) * step
        y = (h - 8) - (clamp(v, lo, hi) - lo) / (hi - lo) * (h - 30)
        pts += [x, y]
    cv.create_line(*pts, fill=color, width=2, smooth=True)
    cv.create_text(w - 8, 6, anchor="ne", text=f"{data[-1]:.1f}{unit}".replace(".0", ""),
                   fill=color, font=(FONT, 10, "bold"))


def draw_radar(cv):
    cv.delete("all")
    w, h = cv.winfo_width(), cv.winfo_height()
    if w < 60 or h < 60:
        return
    cx, cy = w / 2, h / 2
    r = min(w, h) / 2 - 38
    labels = ["STRESS", "FATIGUE", "ISOLATION", "BONE", "CARDIO", "RADIATION"]
    vals = [stress.get(), fatigue.get(), isolation.get(), bone.get(), cardio.get(),
            radiation.get()]
    n = len(labels)

    def pt(i, frac):
        a = -math.pi / 2 + 2 * math.pi * i / n
        return cx + r * frac * math.cos(a), cy + r * frac * math.sin(a)

    for ring in (0.25, 0.5, 0.75, 1.0):
        pts = []
        for i in range(n):
            pts += list(pt(i, ring))
        cv.create_polygon(*pts, outline="#1c4a6e", fill="")
    for i in range(n):
        x, y = pt(i, 1.0)
        cv.create_line(cx, cy, x, y, fill="#1c4a6e")
        lx, ly = pt(i, 1.2)
        cv.create_text(lx, ly, text=labels[i], fill=MUTED, font=(FONT, 8, "bold"))
    pts = []
    for i, v in enumerate(vals):
        pts += list(pt(i, clamp(v) / 100))
    col = risk_color(max(vals))
    cv.create_polygon(*pts, outline=col, fill=col, stipple="gray25", width=2)


# ============================================================
# MENU
# ============================================================
menubar = tk.Menu(root)

m_file = tk.Menu(menubar, tearoff=0)
m_file.add_command(label="Save Health Report", command=save_report)
m_file.add_command(label="Export Data (CSV)", command=export_csv)
m_file.add_separator()
m_file.add_command(label="Exit", command=close_app)
menubar.add_cascade(label="FILE", menu=m_file)

m_dash = tk.Menu(menubar, tearoff=0)
m_dash.add_command(label="Open Dashboard", command=lambda: show_page("dash"))
m_dash.add_command(label="Generate Simulated Vitals", command=generate_simulated_vitals)
menubar.add_cascade(label="DASHBOARD", menu=m_dash)

m_ex = tk.Menu(menubar, tearoff=0)
m_ex.add_command(label="Open Exercise Page", command=lambda: show_page("ex"))
m_ex.add_command(label="Start", command=start_exercise)
m_ex.add_command(label="Pause", command=pause_exercise)
m_ex.add_command(label="Reset Counters", command=reset_exercise)
menubar.add_cascade(label="EXERCISE", menu=m_ex)

m_mis = tk.Menu(menubar, tearoff=0)
m_mis.add_command(label="Mission Info Page", command=lambda: show_page("mis"))
m_mis.add_separator()
m_mis.add_command(label="ISS Mission", command=lambda: set_mission("ISS MISSION"))
m_mis.add_command(label="Moon Mission", command=lambda: set_mission("MOON MISSION"))
m_mis.add_command(label="Mars Mission", command=lambda: set_mission("MARS MISSION"))
menubar.add_cascade(label="MISSION", menu=m_mis)

m_ai = tk.Menu(menubar, tearoff=0)
m_ai.add_command(label="Analyze / Health Report", command=show_report)
menubar.add_cascade(label="AI ANALYSIS", menu=m_ai)

m_saf = tk.Menu(menubar, tearoff=0)
m_saf.add_command(label="Safety Notice", command=show_safety)
menubar.add_cascade(label="SAFETY", menu=m_saf)

m_sys = tk.Menu(menubar, tearoff=0)
m_sys.add_command(label="Refresh NASA Data", command=refresh_nasa)
m_sys.add_command(label="About", command=show_about)
menubar.add_cascade(label="SYSTEM", menu=m_sys)
root.config(menu=menubar)

# ============================================================
# SCROLLABLE PAGE
# ============================================================
outer = tk.Canvas(root, bg=BG, highlightthickness=0)
vsb = tk.Scrollbar(root, orient="vertical", command=outer.yview)
outer.configure(yscrollcommand=vsb.set)
vsb.pack(side="right", fill="y")
outer.pack(side="left", fill="both", expand=True)

page = tk.Frame(outer, bg=BG)
page_win = outer.create_window((0, 0), window=page, anchor="nw")
page.bind("<Configure>", lambda e: outer.configure(scrollregion=outer.bbox("all")))
outer.bind("<Configure>", lambda e: outer.itemconfig(page_win, width=e.width))


def on_wheel(e):
    # do not scroll the page while the pointer is over the alert-log list
    if isinstance(e.widget, tk.Listbox) or isinstance(e.widget, tk.Text):
        return
    outer.yview_scroll(int(-e.delta / 120), "units")


root.bind_all("<MouseWheel>", on_wheel)

# ============================================================
# HEADER
# ============================================================
head = tk.Frame(page, bg=BG)
head.pack(fill="x", padx=28, pady=(14, 0))
hl = tk.Frame(head, bg=BG)
hl.pack(side="left")
tk.Label(hl, text="AL-KASAV ASTROHEALTH V3 • AI DIGITAL TWIN",
         font=(FONT, 28, "bold"), fg=CYAN, bg=BG, anchor="w").pack(anchor="w")
tk.Label(hl, text="ASTRONAUT HEALTH • AI MONITORING • NASA DATA • MISSION CONTROL",
         font=(FONT, 11), fg=MUTED, bg=BG, anchor="w").pack(anchor="w")
hr_ = tk.Frame(head, bg=BG)
hr_.pack(side="right")
tk.Label(hr_, textvariable=clock_utc, font=("Consolas", 15, "bold"), fg=TXT, bg=BG).pack(anchor="e")
tk.Label(hr_, textvariable=clock_met, font=("Consolas", 12), fg=BLUE, bg=BG).pack(anchor="e")
tk.Label(hr_, textvariable=mission, font=(FONT, 10, "bold"), fg=YELLOW, bg=BG).pack(anchor="e")

# ---- navigation
nav = tk.Frame(page, bg=BG)
nav.pack(fill="x", padx=28, pady=(10, 6))
nav_buttons = {}
PAGES = {}


def show_page(key):
    for k, f in PAGES.items():
        f.pack_forget()
    PAGES[key].pack(fill="both", expand=True)
    for k, b in nav_buttons.items():
        b.config(bg=CYAN if k == key else CARD, fg="black" if k == key else TXT)
    if key == "ai":
        refresh_report()
    refresh_all()


for key, label in (("dash", "DASHBOARD"), ("ex", "EXERCISE"),
                   ("mis", "MISSION"), ("ai", "AI ANALYSIS")):
    b = tk.Button(nav, text=label, font=(FONT, 11, "bold"), relief="flat", bg=CARD, fg=TXT,
                  padx=22, pady=7, cursor="hand2", activebackground=CYAN,
                  command=lambda k=key: show_page(k))
    b.pack(side="left", padx=(0, 6))
    nav_buttons[key] = b
flat_button(nav, "SAFETY", show_safety, "#7f1d1d", fg="white", size=11, padx=22, pady=7).pack(side="left")

body = tk.Frame(page, bg=BG)
body.pack(fill="both", expand=True, padx=18, pady=4)
body.columnconfigure(0, weight=5)
body.columnconfigure(1, weight=3)
left = tk.Frame(body, bg=PANEL)
left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
right = tk.Frame(body, bg=PANEL)
right.grid(row=0, column=1, sticky="nsew")

pg_dash = tk.Frame(left, bg=PANEL)
pg_ex = tk.Frame(left, bg=PANEL)
pg_mis = tk.Frame(left, bg=PANEL)
pg_ai = tk.Frame(left, bg=PANEL)
PAGES.update(dash=pg_dash, ex=pg_ex, mis=pg_mis, ai=pg_ai)

# ============================================================
# DASHBOARD PAGE
# ============================================================
heading(pg_dash, "LIVE ASTRONAUT TELEMETRY", size=16).pack(fill="x", padx=18, pady=(14, 8))
cards_frame = tk.Frame(pg_dash, bg=PANEL)
cards_frame.pack(fill="x", padx=12)
for c in range(3):
    cards_frame.columnconfigure(c, weight=1, uniform="c")
card_value_labels = {}


def make_card(r, c, name, unit):
    f = tk.Frame(cards_frame, bg=CARD, highlightbackground=BORDER, highlightthickness=2)
    f.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)
    tk.Label(f, text=name, font=(FONT, 10, "bold"), fg=MUTED, bg=CARD).pack(pady=(10, 0))
    holder = tk.Frame(f, bg=CARD)
    holder.pack(pady=4)
    val = tk.Label(holder, text="--", font=(FONT, 26, "bold"), fg=CYAN, bg=CARD)
    tk.Label(f, text=unit, font=(FONT, 9), fg=MUTED, bg=CARD).pack(pady=(0, 8))
    card_value_labels[name] = val
    return holder, val


hr_holder, hr_val = make_card(0, 0, "HEART RATE", "BPM")
tk.Label(hr_holder, text="♥", font=(FONT, 16), fg="#ef4444", bg=CARD).pack(side="left", padx=(0, 6))
ecg = tk.Canvas(hr_holder, width=140, height=46, bg=CARD, highlightthickness=0)
ecg.pack(side="left")
hr_val.pack(side="left", padx=(8, 0))
for (r, c, n, u) in ((0, 1, "SpO₂", "%"), (0, 2, "TEMPERATURE", "°C"), (1, 0, "STRESS", "%"),
                     (1, 1, "FATIGUE", "%"), (1, 2, "MOVEMENT", "%")):
    make_card(r, c, n, u)[1].pack()

ecg_state = {"x": 0}
ECG_PATTERN = {0: 0, 1: 2, 2: 4, 3: 2, 4: 0, 9: -4, 10: -16, 11: 18, 12: 4, 13: -6,
               18: 3, 19: 6, 20: 8, 21: 6, 22: 3}


def draw_ecg():
    ecg.delete("all")
    pts = []
    for px in range(0, 141, 2):
        y = 23 - ECG_PATTERN.get(((px // 2) + ecg_state["x"]) % 36, 0) * 1.1
        pts += [px, y]
    ecg.create_line(*pts, fill="#22ff88", width=2)
    ecg_state["x"] = (ecg_state["x"] + 1) % 36
    root.after(int(clamp(60000 / max(heart.get(), 40) / 12, 40, 140)), draw_ecg)


# ---- overall health row
orow = tk.Frame(pg_dash, bg=PANEL)
orow.pack(fill="x", padx=14, pady=(10, 4))
orow.columnconfigure(0, weight=1, uniform="o")
orow.columnconfigure(1, weight=1, uniform="o")
orow.columnconfigure(2, weight=2, uniform="o")

c1 = tk.Frame(orow, bg=CARD, highlightbackground=BORDER, highlightthickness=2)
c1.grid(row=0, column=0, sticky="nsew", padx=4)
tk.Label(c1, text="OVERALL HEALTH SCORE", font=(FONT, 10, "bold"), fg=MUTED, bg=CARD).pack(pady=(12, 0))
health_label = tk.Label(c1, text="0.0", font=(FONT, 40, "bold"), fg=GREEN, bg=CARD)
health_label.pack(pady=(6, 0))
stage_label = tk.Label(c1, textvariable=stage, font=(FONT, 16, "bold"), fg=GREEN, bg=CARD)
stage_label.pack()
tk.Label(c1, text="vitals-based", font=(FONT, 8), fg=MUTED, bg=CARD).pack(pady=(0, 10))

c2 = tk.Frame(orow, bg=CARD, highlightbackground=BORDER, highlightthickness=2)
c2.grid(row=0, column=1, sticky="nsew", padx=4)
gauge_dash = tk.Canvas(c2, width=190, height=190, bg=CARD, highlightthickness=0)
gauge_dash.pack(pady=(6, 0))
tk.Label(c2, text="exercise raises it to 100%", font=(FONT, 8), fg=MUTED, bg=CARD).pack(pady=(0, 8))

c3 = tk.Frame(orow, bg=CARD, highlightbackground=BORDER, highlightthickness=2)
c3.grid(row=0, column=2, sticky="nsew", padx=4)
tk.Label(c3, text="MISSION STATUS", font=(FONT, 10, "bold"), fg=MUTED, bg=CARD).pack(pady=(12, 0))
tk.Label(c3, textvariable=mission, font=(FONT, 14, "bold"), fg=BLUE, bg=CARD).pack()
rr = tk.Frame(c3, bg=CARD)
rr.pack(pady=2)
tk.Label(rr, text="RISK:", font=(FONT, 11), fg=MUTED, bg=CARD).pack(side="left")
risk_label = tk.Label(rr, textvariable=risk, font=(FONT, 16, "bold"), fg=YELLOW, bg=CARD)
risk_label.pack(side="left", padx=6)
alert_label = tk.Label(c3, textvariable=alert, wraplength=300, font=(FONT, 9),
                       fg="#fecaca", bg="#3b1d1d", pady=6)
alert_label.pack(fill="x", padx=10, pady=(4, 6))
tk.Label(c3, textvariable=ex_status, font=(FONT, 9, "bold"), fg=YELLOW, bg=CARD).pack(pady=(0, 8))

# ---- mission buttons
mbtn = tk.Frame(pg_dash, bg=PANEL)
mbtn.pack(pady=(6, 4))
for text, cmd, color in (
        ("ISS MODE", lambda: set_mission("ISS MISSION"), "#166534"),
        ("MOON MODE", lambda: set_mission("MOON MISSION"), "#475569"),
        ("MARS MODE", lambda: set_mission("MARS MISSION"), "#b91c1c"),
        ("REFRESH NASA DATA", refresh_nasa, "#0891b2")):
    flat_button(mbtn, text, cmd, color, fg="white").pack(side="left", padx=5)

# ---- trend charts
chart_panel = tk.Frame(pg_dash, bg=PANEL2)
chart_panel.pack(fill="x", padx=16, pady=(8, 4))
heading(chart_panel, "LIVE TRENDS (last 90 s)", color=BLUE, size=12).pack(fill="x", padx=12, pady=(10, 4))
crow = tk.Frame(chart_panel, bg=PANEL2)
crow.pack(fill="x", padx=8, pady=(0, 10))
for c in range(4):
    crow.columnconfigure(c, weight=1, uniform="ch")
chart_cv = {}
for c, name in enumerate(("hr", "spo2", "temp", "health")):
    cv = tk.Canvas(crow, height=110, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
    cv.grid(row=0, column=c, sticky="nsew", padx=4)
    chart_cv[name] = cv

# ---- vital signs panel
vital = tk.Frame(pg_dash, bg=PANEL2)
vital.pack(fill="x", padx=16, pady=(8, 4))
heading(vital, "VITAL SIGNS • REAL INPUT / SIMULATION / CONNECTION STATUS",
        color=BLUE, size=12).pack(fill="x", padx=14, pady=(10, 6))
vrow = tk.Frame(vital, bg=PANEL2)
vrow.pack(fill="x", padx=12, pady=(0, 12))
vrow.columnconfigure(0, weight=3)
vrow.columnconfigure(1, weight=2)

manual = tk.Frame(vrow, bg=CARD, highlightbackground=BORDER, highlightthickness=2)
manual.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
heading(manual, "REAL DEVICE READINGS (MANUAL ENTRY)", color=GREEN, size=10).pack(
    fill="x", padx=12, pady=(8, 4))
grid = tk.Frame(manual, bg=CARD)
grid.pack(fill="x", padx=12)
entries = {}
for c in range(3):
    grid.columnconfigure(c, weight=1)


def make_entry(r, c, label):
    f = tk.Frame(grid, bg=CARD)
    f.grid(row=r, column=c, sticky="ew", padx=4, pady=4)
    tk.Label(f, text=label, font=(FONT, 8, "bold"), fg=MUTED, bg=CARD, anchor="w").pack(fill="x")
    e = tk.Entry(f, bg="#050e18", fg="white", insertbackground="white",
                 relief="flat", font=(FONT, 11), width=12)
    e.pack(fill="x", ipady=5)
    entries[label] = e


make_entry(0, 0, "BP SYS (mmHg)")
make_entry(0, 1, "BP DIA (mmHg)")
make_entry(0, 2, "PULSE (BPM)")
make_entry(1, 0, "SpO₂ (%)")
make_entry(1, 1, "TEMP (°C)")


def apply_real_readings():
    def read(label, lo, hi):
        t = entries[label].get().strip()
        if not t:
            return None
        v = float(t)
        if not (lo <= v <= hi):
            raise ValueError(f"{label}: value must be between {lo} and {hi}")
        return v

    try:
        sys_ = read("BP SYS (mmHg)", 50, 260)
        dia = read("BP DIA (mmHg)", 30, 160)
        pulse = read("PULSE (BPM)", 20, 250)
        s = read("SpO₂ (%)", 50, 100)
        t = read("TEMP (°C)", 30, 45)
    except ValueError as e:
        messagebox.showerror("Invalid input", str(e) if "must be" in str(e)
                             else "Please enter numbers only.")
        return
    if all(v is None for v in (sys_, dia, pulse, s, t)):
        messagebox.showwarning("No input", "Please enter at least one reading.")
        return
    data_mode.set("REAL")
    if pulse is not None:
        heart.set(int(pulse))
    if s is not None:
        spo2.set(int(s))
    if t is not None:
        temperature.set(round(t, 1))
    if sys_ is not None:
        bp_sys_val["v"] = sys_
    if dia is not None:
        bp_dia_val["v"] = dia
    conn_summary.set("MANUAL ENTRY APPLIED • NOT DEVICE-VERIFIED")
    log_event("Manual readings applied")
    refresh_all()


btns = tk.Frame(manual, bg=CARD)
btns.pack(fill="x", padx=12, pady=(8, 12))
flat_button(btns, "APPLY REAL READINGS", apply_real_readings, "#22c55e").pack(side="left", padx=(4, 6))
flat_button(btns, "ANALYZE / HEALTH REPORT", show_report, "#38bdf8").pack(side="left")

side = tk.Frame(vrow, bg=PANEL2)
side.grid(row=0, column=1, sticky="nsew")
sim = tk.Frame(side, bg=CARD, highlightbackground=BORDER, highlightthickness=2)
sim.pack(fill="x")
heading(sim, "SIMULATION MODE", size=10).pack(fill="x", padx=12, pady=(8, 2))
tk.Label(sim, text="Generated demo data only — not a real measurement.",
         font=(FONT, 9), fg=MUTED, bg=CARD, anchor="w", justify="left",
         wraplength=300).pack(fill="x", padx=12)
tk.Label(sim, textvariable=data_mode, font=(FONT, 9, "bold"), fg=YELLOW, bg=CARD,
         anchor="w").pack(fill="x", padx=12)
flat_button(sim, "GENERATE SIMULATED VITALS", generate_simulated_vitals, YELLOW).pack(
    anchor="w", padx=12, pady=(6, 10))

conn = tk.Frame(side, bg="#2a0f14", highlightbackground="#7f1d1d", highlightthickness=2)
conn.pack(fill="x", pady=(8, 0))
heading(conn, "DEVICE CONNECTION STATUS", color=RED, size=10).pack(fill="x", padx=12, pady=(8, 2))
for txt in ("• BP MACHINE: NOT CONNECTED", "• PULSE OXIMETER: NOT CONNECTED",
            "• THERMOMETER: NOT CONNECTED"):
    tk.Label(conn, text=txt, font=(FONT, 8, "bold"), fg="#fb7185", bg="#2a0f14",
             anchor="w").pack(fill="x", padx=12)
tk.Label(conn, textvariable=conn_summary, font=(FONT, 8, "bold"), fg=YELLOW,
         bg="#2a0f14", anchor="w").pack(fill="x", padx=12, pady=(6, 10))

# ---- recommendations (dashboard)
rec = tk.Frame(pg_dash, bg=PANEL2)
rec.pack(fill="x", padx=16, pady=(8, 16))
heading(rec, "AI RECOMMENDATIONS", color=BLUE, size=12).pack(fill="x", padx=14, pady=(10, 2))
tk.Label(rec, textvariable=recommend, font=(FONT, 10), fg=TXT, bg=PANEL2, anchor="w",
         justify="left", wraplength=780).pack(fill="x", padx=14, pady=(0, 12))

# ============================================================
# EXERCISE PAGE
# ============================================================
heading(pg_ex, "EXERCISE COUNTER • AI REP DETECTION", size=16).pack(fill="x", padx=18, pady=(14, 2))
tk.Label(pg_ex, text="Stand where the camera sees your full body, press START, then perform each exercise. "
                     "Reach the target on every exercise to raise the Health Count to 100%.",
         font=(FONT, 9), fg=MUTED, bg=PANEL, wraplength=780, justify="left", anchor="w").pack(
    fill="x", padx=18, pady=(0, 8))

ctrl = tk.Frame(pg_ex, bg=PANEL)
ctrl.pack(fill="x", padx=16, pady=(0, 6))
flat_button(ctrl, "▶ START", start_exercise, "#22c55e", size=11).pack(side="left", padx=(0, 6))
flat_button(ctrl, "❚❚ PAUSE", pause_exercise, YELLOW, size=11).pack(side="left", padx=6)
flat_button(ctrl, "↺ RESET", reset_exercise, "#ef4444", fg="white", size=11).pack(side="left", padx=6)
tk.Label(ctrl, text="TARGET REPS / EXERCISE:", font=(FONT, 9, "bold"), fg=MUTED, bg=PANEL).pack(
    side="left", padx=(18, 4))
tk.Spinbox(ctrl, from_=1, to=50, width=4, textvariable=ex_target, font=(FONT, 12, "bold"),
           command=lambda: refresh_all(), bg=CARD, fg="white", buttonbackground=CARD,
           insertbackground="white", relief="flat").pack(side="left")
tk.Label(ctrl, textvariable=ex_status, font=(FONT, 12, "bold"), fg=YELLOW, bg=PANEL).pack(
    side="left", padx=18)

ex_grid = tk.Frame(pg_ex, bg=PANEL)
ex_grid.pack(fill="x", padx=12, pady=4)
ex_grid.columnconfigure(0, weight=1, uniform="e")
ex_grid.columnconfigure(1, weight=1, uniform="e")
ex_widgets = {}
for i, (k, name, desc) in enumerate(EXERCISES):
    f = tk.Frame(ex_grid, bg=CARD, highlightbackground=BORDER, highlightthickness=2)
    f.grid(row=i // 2, column=i % 2, sticky="nsew", padx=4, pady=4)
    tk.Label(f, text=name, font=(FONT, 11, "bold"), fg=BLUE, bg=CARD).pack(pady=(10, 0))
    tk.Label(f, text=desc, font=(FONT, 8), fg=MUTED, bg=CARD, wraplength=320).pack()
    cl = tk.Label(f, text="0 / 10", font=(FONT, 30, "bold"), fg=CYAN, bg=CARD)
    cl.pack(pady=(4, 2))
    bar = Bar(f, "", CARD, label_w=0, track=TRACK, height=16, padx=14)
    pl = tk.Label(f, text="READY", font=(FONT, 9, "bold"), fg=MUTED, bg=CARD)
    pl.pack(pady=(0, 10))
    ex_widgets[k] = (cl, bar, pl)

stats = tk.Frame(pg_ex, bg=PANEL2)
stats.pack(fill="x", padx=16, pady=(8, 4))
stats.columnconfigure(0, weight=3)
stats.columnconfigure(1, weight=2)
sl = tk.Frame(stats, bg=PANEL2)
sl.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
heading(sl, "SESSION SUMMARY", color=BLUE, size=12).pack(fill="x")
ex_stat_vars = {k: tk.StringVar(value="--") for k in
                ("SESSION TIME", "TOTAL REPS", "EXERCISE COMPLETE", "ESTIMATED ENERGY",
                 "VITALS HEALTH SCORE", "HEALTH COUNT")}
for k, v in ex_stat_vars.items():
    r = tk.Frame(sl, bg=PANEL2)
    r.pack(fill="x", pady=2)
    tk.Label(r, text=k, width=22, anchor="w", font=(FONT, 9, "bold"), fg=MUTED, bg=PANEL2).pack(side="left")
    tk.Label(r, textvariable=v, anchor="w", font=(FONT, 12, "bold"), fg=YELLOW, bg=PANEL2).pack(side="left")
tk.Label(sl, text="Energy is only a rough demo estimate.", font=(FONT, 8), fg=MUTED,
         bg=PANEL2, anchor="w").pack(fill="x", pady=(4, 0))
sr = tk.Frame(stats, bg=PANEL2)
sr.grid(row=0, column=1, sticky="nsew")
gauge_ex = tk.Canvas(sr, width=210, height=210, bg=PANEL2, highlightthickness=0)
gauge_ex.pack(pady=8)

tk.Label(pg_ex, textvariable=banner, font=(FONT, 13, "bold"), fg="#052e16", bg=PANEL,
         wraplength=780).pack(fill="x", padx=16, pady=(4, 2))
banner_label = pg_ex.winfo_children()[-1]
tk.Label(pg_ex, text="", bg=PANEL).pack(pady=6)

# ============================================================
# MISSION PAGE
# ============================================================
heading(pg_mis, "MISSION CONTROL • SPACE HEALTH", size=16).pack(fill="x", padx=18, pady=(14, 8))
mm = tk.Frame(pg_mis, bg=PANEL)
mm.pack(fill="x", padx=16, pady=(0, 6))
for text, cmd, color in (
        ("ISS MISSION", lambda: set_mission("ISS MISSION"), "#166534"),
        ("MOON MISSION", lambda: set_mission("MOON MISSION"), "#475569"),
        ("MARS MISSION", lambda: set_mission("MARS MISSION"), "#b91c1c")):
    flat_button(mm, text, cmd, color, fg="white", size=11).pack(side="left", padx=(0, 8))

info = tk.Frame(pg_mis, bg=PANEL2)
info.pack(fill="x", padx=16, pady=6)
tk.Label(info, textvariable=mission, font=(FONT, 15, "bold"), fg=YELLOW, bg=PANEL2,
         anchor="w").pack(fill="x", padx=14, pady=(10, 4))
for k, _ in MISSION_INFO["ISS MISSION"]:
    r = tk.Frame(info, bg=PANEL2)
    r.pack(fill="x", padx=14, pady=2)
    tk.Label(r, text=k, width=20, anchor="nw", font=(FONT, 9, "bold"), fg=MUTED, bg=PANEL2).pack(side="left")
    tk.Label(r, textvariable=mission_info_vars[k], anchor="w", justify="left", wraplength=520,
             font=(FONT, 10), fg=TXT, bg=PANEL2).pack(side="left", fill="x")
tk.Frame(info, bg=PANEL2, height=8).pack()

riskp = tk.Frame(pg_mis, bg=PANEL2)
riskp.pack(fill="x", padx=16, pady=6)
heading(riskp, "SPACE HEALTH RISKS", color=BLUE, size=12).pack(fill="x", padx=14, pady=(10, 4))
risk_bars = {}
for name in ("STRESS RISK", "FATIGUE RISK", "ISOLATION RISK", "BONE LOSS RISK",
             "CARDIO RISK", "RADIATION RISK"):
    risk_bars[name] = Bar(riskp, name, PANEL2, track=TRACK)
tk.Frame(riskp, bg=PANEL2, height=8).pack()

prof = tk.Frame(pg_mis, bg=PANEL2)
prof.pack(fill="x", padx=16, pady=(6, 16))
heading(prof, "ASTRONAUT PROFILE", color=BLUE, size=12).pack(fill="x", padx=14, pady=(10, 4))
pgrid = tk.Frame(prof, bg=PANEL2)
pgrid.pack(fill="x", padx=14, pady=(0, 6))
for i, (lab, var, w) in enumerate((("NAME", p_name, 20), ("CREW ID", p_id, 10), ("AGE", p_age, 6),
                                   ("HEIGHT (cm)", p_height, 8), ("WEIGHT (kg)", p_weight, 8))):
    f = tk.Frame(pgrid, bg=PANEL2)
    f.grid(row=0, column=i, padx=4, sticky="w")
    tk.Label(f, text=lab, font=(FONT, 8, "bold"), fg=MUTED, bg=PANEL2).pack(anchor="w")
    tk.Entry(f, textvariable=var, width=w, bg="#050e18", fg="white", insertbackground="white",
             relief="flat", font=(FONT, 11)).pack(ipady=4)
tk.Label(prof, textvariable=p_bmi, font=(FONT, 12, "bold"), fg=GREEN, bg=PANEL2,
         anchor="w").pack(fill="x", padx=14, pady=(2, 12))

# ============================================================
# AI ANALYSIS PAGE
# ============================================================
heading(pg_ai, "AI ANALYSIS • REPORT • ALERT LOG", size=16).pack(fill="x", padx=18, pady=(14, 8))
arow = tk.Frame(pg_ai, bg=PANEL)
arow.pack(fill="x", padx=12)
arow.columnconfigure(0, weight=1, uniform="a")
arow.columnconfigure(1, weight=1, uniform="a")

rp = tk.Frame(arow, bg=PANEL2)
rp.grid(row=0, column=0, sticky="nsew", padx=4)
heading(rp, "RISK RADAR", color=BLUE, size=12).pack(fill="x", padx=12, pady=(10, 0))
radar = tk.Canvas(rp, height=300, bg=PANEL2, highlightthickness=0)
radar.pack(fill="x", padx=8, pady=(0, 8))

lp = tk.Frame(arow, bg=PANEL2)
lp.grid(row=0, column=1, sticky="nsew", padx=4)
heading(lp, "ALERT / EVENT LOG", color=BLUE, size=12).pack(fill="x", padx=12, pady=(10, 4))
lbf = tk.Frame(lp, bg=PANEL2)
lbf.pack(fill="both", expand=True, padx=10, pady=(0, 10))
lsb = tk.Scrollbar(lbf)
lsb.pack(side="right", fill="y")
log_box = tk.Listbox(lbf, height=14, bg=CARD, fg=TXT, font=("Consolas", 9), relief="flat",
                     highlightthickness=0, yscrollcommand=lsb.set, selectbackground=BORDER)
log_box.pack(side="left", fill="both", expand=True)
lsb.config(command=log_box.yview)
for line in reversed(alert_log):
    log_box.insert(0, line)

btnr = tk.Frame(pg_ai, bg=PANEL)
btnr.pack(fill="x", padx=16, pady=8)
flat_button(btnr, "REFRESH REPORT", refresh_report, "#38bdf8").pack(side="left", padx=(0, 6))
flat_button(btnr, "SAVE REPORT (.txt)", save_report, "#22c55e").pack(side="left", padx=6)
flat_button(btnr, "EXPORT DATA (.csv)", export_csv, YELLOW).pack(side="left", padx=6)

report_box = tk.Text(pg_ai, height=30, bg=CARD, fg=TXT, font=("Consolas", 10), relief="flat",
                     padx=12, pady=10, wrap="word", state="disabled")
report_box.pack(fill="x", padx=16, pady=(0, 16))

# ============================================================
# RIGHT COLUMN: CAMERA + BODY PARTS + NASA
# ============================================================
heading(right, "AI CAMERA / POSE", size=15).pack(fill="x", padx=16, pady=(14, 6))
camera_box = tk.Label(right, bg="black", width=540, height=375)
camera_box.pack(padx=16)
camera_status_label = tk.Label(right, textvariable=camera_status, font=(FONT, 9, "bold"),
                               fg=GREEN, bg=PANEL)
camera_status_label.pack(pady=6)

bp_panel = tk.Frame(right, bg=PANEL2)
bp_panel.pack(fill="x", padx=14, pady=(4, 8))
heading(bp_panel, "LIVE BODY-PART MOVEMENT SCORE", color=BLUE, size=12).pack(
    fill="x", padx=12, pady=(10, 0))
tk.Label(bp_panel, text="Raise / move each body part to fill its bar • 100% = full demo range",
         font=(FONT, 8), fg=MUTED, bg=PANEL2, anchor="w").pack(fill="x", padx=12, pady=(0, 6))
bars = {n: Bar(bp_panel, n, PANEL2) for n in PART_NAMES}
tk.Frame(bp_panel, bg=PANEL2, height=8).pack()

nasa_panel = tk.Frame(right, bg=PANEL2)
nasa_panel.pack(fill="x", padx=14, pady=(4, 16))
heading(nasa_panel, "☢ NASA RADLAB RADIATION TELEMETRY", color=BLUE, size=12).pack(
    fill="x", padx=12, pady=(10, 4))
nasa_status_label = tk.Label(nasa_panel, textvariable=nasa_status, font=(FONT, 10, "bold"),
                             fg=YELLOW, bg=PANEL2, anchor="w")
nasa_status_label.pack(fill="x", padx=12)
tk.Label(nasa_panel, textvariable=nasa_count, font=(FONT, 9), fg=MUTED, bg=PANEL2,
         anchor="w").pack(fill="x", padx=12)
tk.Label(nasa_panel, textvariable=nasa_dose, font=(FONT, 10, "bold"), fg=YELLOW, bg=PANEL2,
         anchor="w", wraplength=480, justify="left").pack(fill="x", padx=12, pady=(4, 0))
tk.Label(nasa_panel, textvariable=nasa_time, font=(FONT, 9), fg="#93c5fd", bg=PANEL2,
         anchor="w", wraplength=480, justify="left").pack(fill="x", padx=12)
rad_bar = Bar(nasa_panel, "RADIATION RISK", PANEL2, label_w=16)
tk.Label(nasa_panel, text="Visualization score only — not a medical radiation limit.",
         font=(FONT, 8), fg=MUTED, bg=PANEL2, anchor="w").pack(fill="x", padx=12, pady=(0, 10))

# ============================================================
# UI UPDATE
# ============================================================
def update_ui():
    # --- telemetry cards
    hv = heart.get()
    card_value_labels["HEART RATE"].config(text=str(hv), fg=CYAN if 60 <= hv <= 100 else RED)
    sv = spo2.get()
    card_value_labels["SpO₂"].config(text=str(sv), fg=CYAN if sv >= 94 else RED)
    tv = temperature.get()
    card_value_labels["TEMPERATURE"].config(text=f"{tv:.1f}", fg=CYAN if 36.1 <= tv <= 37.5 else YELLOW)
    card_value_labels["STRESS"].config(text=str(stress.get()),
                                       fg=CYAN if stress.get() < 40 else (YELLOW if stress.get() < 70 else RED))
    card_value_labels["FATIGUE"].config(text=str(fatigue.get()),
                                        fg=CYAN if fatigue.get() < 40 else (YELLOW if fatigue.get() < 70 else RED))
    card_value_labels["MOVEMENT"].config(text=str(movement.get()))

    s = health.get()
    health_label.config(text=f"{s:.1f}", fg=level_color(s))
    stage_label.config(fg=level_color(s))
    risk_label.config(fg={"LOW": GREEN, "MEDIUM": YELLOW, "HIGH": RED}[risk.get()])
    alert_label.config(bg="#14301f" if risk.get() == "LOW" else "#3b1d1d",
                       fg="#bbf7d0" if risk.get() == "LOW" else "#fecaca")

    tot = total_health.get()
    tcol = GREEN if tot >= 85 else (YELLOW if tot >= 55 else RED)
    draw_gauge(gauge_dash, tot, "HEALTH COUNT", tcol)
    draw_gauge(gauge_ex, tot, "HEALTH COUNT", tcol)

    # --- exercise page
    t = get_target()
    for k in EX_KEYS:
        cl, bar, pl = ex_widgets[k]
        c = ex_count[k]
        cl.config(text=f"{min(c, 99)} / {t}", fg=GREEN if c >= t else CYAN)
        bar.set(min(c / t, 1) * 100, color="#16c60c" if c >= t else "#22d3ee")
        if c >= t:
            pl.config(text="✔ GOAL COMPLETE", fg=GREEN)
        elif ex_state["active"]:
            pl.config(text=("▲ UP" if ex_phase[k] == "up" else "▼ DOWN") +
                      f"   signal {ex_signal[k]:.0f}%", fg=YELLOW)
        else:
            pl.config(text="READY" if not ex_state["acc"] else "PAUSED", fg=MUTED)
    m, sec = divmod(int(ex_elapsed()), 60)
    ex_stat_vars["SESSION TIME"].set(f"{m:02d}:{sec:02d}")
    ex_stat_vars["TOTAL REPS"].set(str(sum(ex_count.values())))
    ex_stat_vars["EXERCISE COMPLETE"].set(f"{ex_pct.get():.0f} %")
    ex_stat_vars["ESTIMATED ENERGY"].set(f"≈ {exercise_kcal():.1f} kcal")
    ex_stat_vars["VITALS HEALTH SCORE"].set(f"{s:.1f} %")
    ex_stat_vars["HEALTH COUNT"].set("100 %" if tot >= 99.95 else f"{tot:.1f} %")
    banner_label.config(bg="#4ade80" if banner.get() else PANEL)

    # --- mission page risk bars
    for name, val in (("STRESS RISK", stress.get()), ("FATIGUE RISK", fatigue.get()),
                      ("ISOLATION RISK", isolation.get()), ("BONE LOSS RISK", bone.get()),
                      ("CARDIO RISK", cardio.get()), ("RADIATION RISK", radiation.get())):
        risk_bars[name].set(val, color=risk_color(val))
    p_bmi.set(bmi_text())

    # --- NASA bar
    rv = radiation.get()
    rad_bar.set(rv, color=risk_color(rv))

    # --- header clocks
    clock_utc.set("UTC " + datetime.datetime.utcnow().strftime("%H:%M:%S"))
    el = int(time.time() - APP_START)
    clock_met.set(f"MET {el // 3600:02d}:{(el // 60) % 60:02d}:{el % 60:02d}")


def ui_tick():
    refresh_all()
    root.after(300, ui_tick)


def record_tick():
    hr_hist.append(heart.get())
    spo2_hist.append(spo2.get())
    temp_hist.append(temperature.get())
    health_hist.append(total_health.get())
    csv_rows.append([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data_mode.get(),
                     mission.get(), heart.get(), spo2.get(), temperature.get(), stress.get(),
                     fatigue.get(), round(radiation.get(), 2), movement.get(),
                     health.get(), total_health.get(), ex_pct.get()])
    if len(csv_rows) > 5000:
        del csv_rows[:1000]
    if PAGES["dash"].winfo_ismapped():
        draw_chart(chart_cv["hr"], hr_hist, 40, 140, "#22ff88", "HEART RATE", " bpm")
        draw_chart(chart_cv["spo2"], spo2_hist, 85, 100, CYAN, "SpO₂", " %")
        draw_chart(chart_cv["temp"], temp_hist, 35, 39, YELLOW, "TEMPERATURE", " °C")
        draw_chart(chart_cv["health"], health_hist, 0, 100, "#a78bfa", "HEALTH COUNT", " %")
    if PAGES["ai"].winfo_ismapped():
        draw_radar(radar)
    root.after(1000, record_tick)


# ============================================================
# CAMERA LOOP
# ============================================================
def camera():
    ok, frame = cap.read()
    if not ok:
        camera_status.set("AI CAMERA: NOT AVAILABLE")
        camera_status_label.config(fg=RED)
        root.after(500, camera)
        return

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (540, 375))
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = pose.process(rgb)

    if result.pose_landmarks:
        human_detected["v"] = True
        process_pose(result.pose_landmarks.landmark)
        mp_draw.draw_landmarks(frame, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        camera_status.set("AI CAMERA: HUMAN DETECTED • VITALS + MOTION ACTIVE")
        camera_status_label.config(fg=GREEN)
    else:
        human_detected["v"] = False
        for n in PART_NAMES:
            part_scores[n] *= 0.9
        movement.set(int(part_scores["FULL BODY MOBILITY"]))
        camera_status.set("AI CAMERA: NO HUMAN DETECTED")
        camera_status_label.config(fg=YELLOW)

    cv2.putText(frame, "AI MOVEMENT MONITOR", (14, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
    cv2.putText(frame, mission.get(), (14, 54),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    cv2.putText(frame, f"REPS {sum(ex_count.values())}   EXERCISE {ex_pct.get():.0f}%   "
                       f"HEALTH {total_health.get():.0f}%",
                (14, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 120), 2)

    photo = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    camera_box.configure(image=photo, width=540, height=375)
    camera_box.image = photo

    for n, b in bars.items():
        b.set(part_scores[n])
    root.after(30, camera)


# ============================================================
# START
# ============================================================
update_mission_info()
show_page("dash")
generate_simulated_vitals()
log_event("System started")
draw_ecg()
sim_tick()
ui_tick()
record_tick()
camera()
refresh_nasa()

root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()
