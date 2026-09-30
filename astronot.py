import cv2
import mediapipe as mp
import tkinter as tk
from PIL import Image, ImageTk
import random
import requests
import threading
import csv
import io

# ============================================================
# AL KASAV INNOVATION
# AL-KASAV ASTROHEALTH
# ASTRONAUT HEALTH MONITORING SYSTEM
#
# NASA SPACE APPS CHALLENGE 2026
#
# NASA DATA SOURCE:
# NASA Open Science Data Repository (OSDR)
# RadLab - ISS - DosTel radiation measurements
# ============================================================


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()

root.title(
    "AL-KASAV ASTROHEALTH | NASA Space Apps 2026"
)

root.geometry("1250x780")

root.configure(
    bg="#08111f"
)


# ============================================================
# VARIABLES
# ============================================================

heart = tk.IntVar(value=72)

oxygen = tk.IntVar(value=98)

temperature = tk.DoubleVar(value=36.7)

radiation = tk.DoubleVar(value=20.0)

stress = tk.IntVar(value=20)

isolation = tk.IntVar(value=20)

bone = tk.IntVar(value=20)

cardio = tk.IntVar(value=20)

movement = tk.IntVar(value=0)

balance = tk.IntVar(value=0)

coordination = tk.IntVar(value=0)

health = tk.IntVar(value=0)

stage = tk.StringVar(
    value="GOOD"
)

risk = tk.StringVar(
    value="LOW"
)

alert = tk.StringVar(
    value="System Ready"
)

mission = tk.StringVar(
    value="ISS MISSION"
)

nasa_dose = tk.StringVar(
    value="NASA Dose: Loading..."
)

nasa_timestamp = tk.StringVar(
    value="NASA Timestamp: --"
)

nasa_status = tk.StringVar(
    value="NASA OSDR: Connecting..."
)


# ============================================================
# NASA RADLAB
# ============================================================

NASA_API = (
    "https://visualization.osdr.nasa.gov/radlab/api/"
)


# NASA documentation provides an ISS/DosTel example
# using this historical time window.
NASA_PARAMS = {
    "spacecraft": "ISS",
    "instrument": "DosTel",
    "timestamp>": "2022-04-01T23:00",
    "timestamp<": "2022-04-02T01:05",
    "absorbed_dose_rate": "",
    "format": "csv"
}


nasa_readings = []


# ============================================================
# NASA DATA DOWNLOAD
# ============================================================

def download_nasa_data():

    global nasa_readings

    try:

        response = requests.get(
            NASA_API,
            params=NASA_PARAMS,
            timeout=15
        )

        response.raise_for_status()

        text = response.text.strip()

        if not text:

            raise Exception(
                "NASA API returned empty data."
            )

        reader = csv.DictReader(
            io.StringIO(text)
        )

        readings = []

        for row in reader:

            dose = None
            timestamp = ""

            # Find absorbed dose field
            for key in row:

                if key.lower() == "absorbed_dose_rate":

                    try:
                        dose = float(
                            row[key]
                        )
                    except:
                        pass

                if key.lower() == "timestamp":

                    timestamp = row[key]

            if dose is not None:

                readings.append(
                    {
                        "dose": dose,
                        "timestamp": timestamp
                    }
                )

        if not readings:

            raise Exception(
                "No radiation readings found."
            )

        nasa_readings = readings

        root.after(
            0,
            nasa_success
        )

    except Exception as error:

        print(
            "NASA DATA ERROR:",
            error
        )

        root.after(
            0,
            nasa_failed
        )


# ============================================================
# NASA SUCCESS
# ============================================================

def nasa_success():

    nasa_status.set(
        "NASA OSDR: CONNECTED"
    )

    nasa_status_label.config(
        fg="#4ade80"
    )

    nasa_dose.set(
        f"NASA DosTel readings: {len(nasa_readings)}"
    )

    nasa_timestamp.set(
        "Real NASA RadLab dataset loaded"
    )

    # Use first NASA reading
    update_nasa_reading(
        0
    )


# ============================================================
# NASA FAILURE
# ============================================================

def nasa_failed():

    nasa_status.set(
        "NASA OSDR: OFFLINE"
    )

    nasa_status_label.config(
        fg="#f87171"
    )

    nasa_dose.set(
        "NASA data unavailable"
    )

    nasa_timestamp.set(
        "Using demonstration fallback"
    )

    # Demonstration fallback
    radiation.set(
        round(
            random.uniform(
                10,
                60
            ),
            2
        )
    )

    calculate_health()


# ============================================================
# UPDATE NASA READING
# ============================================================

def update_nasa_reading(index):

    if not nasa_readings:

        return

    if index >= len(nasa_readings):

        index = 0

    data = nasa_readings[index]

    dose = data["dose"]

    timestamp = data["timestamp"]

    # Convert NASA dose rate to a 0-100
    # demonstration risk indicator.
    #
    # IMPORTANT:
    # This is NOT a medical radiation limit.
    # It is only a visualization score.

    risk_score = min(
        100,
        max(
            0,
            dose * 20
        )
    )

    radiation.set(
        round(
            risk_score,
            2
        )
    )

    nasa_dose.set(
        f"NASA Absorbed Dose: {dose:.4f} μGy/h"
    )

    nasa_timestamp.set(
        f"NASA Timestamp: {timestamp}"
    )

    calculate_health()

    # Move through the downloaded NASA readings
    root.after(
        3000,
        lambda: update_nasa_reading(
            index + 1
        )
    )


# ============================================================
# HEALTH ENGINE
# ============================================================

def clamp(value):

    return max(
        0,
        min(
            int(value),
            100
        )
    )


def calculate_health():

    radiation_risk = min(
        radiation.get(),
        100
    )

    score = (

        (100 - radiation_risk)

        +

        (100 - stress.get())

        +

        (100 - isolation.get())

        +

        (100 - bone.get())

        +

        (100 - cardio.get())

        +

        oxygen.get()

        +

        movement.get()

    ) / 7


    health.set(
        clamp(score)
    )


    # ========================================================
    # HEALTH STAGE
    # ========================================================

    if health.get() < 25:

        stage.set(
            "CRITICAL"
        )

    elif health.get() < 45:

        stage.set(
            "SEVERE"
        )

    elif health.get() < 65:

        stage.set(
            "MODERATE"
        )

    elif health.get() < 85:

        stage.set(
            "IMPROVING"
        )

    else:

        stage.set(
            "GOOD"
        )


    # ========================================================
    # RISK ENGINE
    # ========================================================

    maximum = max(

        radiation.get(),

        stress.get(),

        isolation.get(),

        bone.get(),

        cardio.get()

    )


    if maximum >= 70:

        risk.set(
            "HIGH"
        )

        alert.set(
            "WARNING: Mission health indicators require attention."
        )

    elif maximum >= 40:

        risk.set(
            "MEDIUM"
        )

        alert.set(
            "CAUTION: Continue astronaut health monitoring."
        )

    else:

        risk.set(
            "LOW"
        )

        alert.set(
            "No major simulated alert."
        )


# ============================================================
# SIMULATED HEALTH SENSORS
# ============================================================

def simulate():

    heart.set(
        random.randint(
            60,
            105
        )
    )

    oxygen.set(
        random.randint(
            93,
            99
        )
    )

    temperature.set(
        round(
            random.uniform(
                36.1,
                37.8
            ),
            1
        )
    )

    stress.set(
        random.randint(
            5,
            95
        )
    )

    isolation.set(
        random.randint(
            5,
            95
        )
    )

    bone.set(
        random.randint(
            5,
            90
        )
    )

    cardio.set(
        random.randint(
            5,
            90
        )
    )

    calculate_health()


# ============================================================
# MISSION MODES
# ============================================================

def iss_mode():

    mission.set(
        "ISS MISSION"
    )

    stress.set(
        random.randint(
            5,
            45
        )
    )

    isolation.set(
        random.randint(
            5,
            50
        )
    )

    bone.set(
        random.randint(
            5,
            60
        )
    )

    cardio.set(
        random.randint(
            5,
            60
        )
    )

    calculate_health()


def moon_mode():

    mission.set(
        "MOON MISSION"
    )

    stress.set(
        random.randint(
            10,
            65
        )
    )

    isolation.set(
        random.randint(
            15,
            75
        )
    )

    bone.set(
        random.randint(
            20,
            80
        )
    )

    cardio.set(
        random.randint(
            10,
            70
        )
    )

    calculate_health()


def mars_mode():

    mission.set(
        "MARS MISSION"
    )

    stress.set(
        random.randint(
            25,
            85
        )
    )

    isolation.set(
        random.randint(
            30,
            95
        )
    )

    bone.set(
        random.randint(
            30,
            90
        )
    )

    cardio.set(
        random.randint(
            20,
            85
        )
    )

    calculate_health()


# ============================================================
# MEDIA PIPE POSE
# ============================================================

mp_pose = mp.solutions.pose

pose = mp_pose.Pose(

    static_image_mode=False,

    model_complexity=1,

    min_detection_confidence=0.6,

    min_tracking_confidence=0.6

)


mp_draw = (
    mp.solutions.drawing_utils
)


cap = cv2.VideoCapture(
    0
)


# ============================================================
# CAMERA
# ============================================================

def camera():

    ret, frame = cap.read()

    if not ret:

        root.after(
            100,
            camera
        )

        return


    frame = cv2.flip(
        frame,
        1
    )


    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    result = pose.process(
        rgb
    )


    if result.pose_landmarks:

        lm = (
            result.pose_landmarks.landmark
        )


        # LEFT ARM

        left_movement = abs(

            lm[11].y -

            lm[15].y

        ) * 250


        # RIGHT ARM

        right_movement = abs(

            lm[12].y -

            lm[16].y

        ) * 250


        movement_score = clamp(

            (

                left_movement +

                right_movement

            ) / 2

        )


        movement.set(
            movement_score
        )

        balance.set(
            movement_score
        )

        coordination.set(
            movement_score
        )


        calculate_health()


        mp_draw.draw_landmarks(

            frame,

            result.pose_landmarks,

            mp_pose.POSE_CONNECTIONS

        )


    # ========================================================
    # CAMERA TEXT
    # ========================================================

    cv2.putText(

        frame,

        "AI MOVEMENT MONITOR",

        (20, 35),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.8,

        (0, 255, 255),

        2

    )


    cv2.putText(

        frame,

        mission.get(),

        (20, 70),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (255, 255, 255),

        2

    )


    # ========================================================
    # SHOW CAMERA
    # ========================================================

    image = Image.fromarray(

        cv2.cvtColor(

            frame,

            cv2.COLOR_BGR2RGB

        )

    )


    photo = ImageTk.PhotoImage(
        image
    )


    camera_box.configure(
        image=photo
    )


    camera_box.image = photo


    root.after(
        20,
        camera
    )


# ============================================================
# HEADER
# ============================================================

tk.Label(

    root,

    text="AL KASAV INNOVATION",

    font=(
        "Arial",
        25,
        "bold"
    ),

    fg="white",

    bg="#10243b"

).pack(

    fill="x",

    pady=5

)


tk.Label(

    root,

    text=(
        "AL-KASAV ASTROHEALTH | "
        "ASTRONAUT HEALTH MONITORING SYSTEM"
    ),

    font=(
        "Arial",
        16,
        "bold"
    ),

    fg="#38bdf8",

    bg="#08111f"

).pack(
    pady=5
)


# ============================================================
# CAMERA BOX
# ============================================================

camera_box = tk.Label(

    root,

    bg="black",

    width=700,

    height=390

)


camera_box.place(

    x=20,

    y=105

)


# ============================================================
# DASHBOARD
# ============================================================

dash = tk.Frame(

    root,

    bg="#10243b",

    width=470,

    height=610

)


dash.place(

    x=755,

    y=100

)


tk.Label(

    dash,

    text="LIVE ASTRONAUT HEALTH DASHBOARD",

    font=(
        "Arial",
        16,
        "bold"
    ),

    fg="white",

    bg="#10243b"

).pack(
    pady=8
)


# ============================================================
# METRIC FUNCTION
# ============================================================

def metric(
    name,
    variable
):

    row = tk.Frame(

        dash,

        bg="#10243b"

    )


    row.pack(

        fill="x",

        padx=15,

        pady=2

    )


    tk.Label(

        row,

        text=name,

        width=23,

        anchor="w",

        fg="white",

        bg="#10243b"

    ).pack(
        side="left"
    )


    tk.Label(

        row,

        textvariable=variable,

        fg="#fde047",

        bg="#10243b",

        font=(
            "Arial",
            11,
            "bold"
        )

    ).pack(
        side="left"
    )


# ============================================================
# VITAL SIGNS
# ============================================================

metric(
    "Heart Rate (BPM)",
    heart
)

metric(
    "Oxygen Saturation (%)",
    oxygen
)

metric(
    "Temperature (°C)",
    temperature
)


# ============================================================
# NASA DATA SECTION
# ============================================================

tk.Label(

    dash,

    text="NASA SPACE DATA",

    font=(
        "Arial",
        13,
        "bold"
    ),

    fg="#38bdf8",

    bg="#172554"

).pack(

    fill="x",

    pady=(8, 2)

)


metric(

    "Radiation Risk",

    radiation

)


tk.Label(

    dash,

    textvariable=nasa_dose,

    wraplength=400,

    fg="#facc15",

    bg="#172554",

    font=(
        "Arial",
        10,
        "bold"
    )

).pack(
    pady=2
)


tk.Label(

    dash,

    textvariable=nasa_timestamp,

    wraplength=400,

    fg="#93c5fd",

    bg="#172554"

).pack()


nasa_status_label = tk.Label(

    dash,

    textvariable=nasa_status,

    fg="#facc15",

    bg="#172554",

    font=(
        "Arial",
        10,
        "bold"
    )

)

nasa_status_label.pack(
    pady=3
)


# ============================================================
# SPACE HEALTH RISKS
# ============================================================

metric(
    "Stress Risk",
    stress
)

metric(
    "Isolation Risk",
    isolation
)

metric(
    "Bone Loss Risk",
    bone
)

metric(
    "Cardio Risk",
    cardio
)


# ============================================================
# AI MOVEMENT
# ============================================================

metric(
    "Balance",
    balance
)

metric(
    "Coordination",
    coordination
)

metric(
    "Movement Score",
    movement
)


# ============================================================
# OVERALL HEALTH
# ============================================================

metric(

    "Overall Health",

    health

)


# ============================================================
# MISSION STATUS
# ============================================================

tk.Label(

    dash,

    text="MISSION STATUS",

    font=(
        "Arial",
        13,
        "bold"
    ),

    fg="white",

    bg="#172554"

).pack(

    fill="x",

    pady=(8, 0)

)


tk.Label(

    dash,

    textvariable=mission,

    font=(
        "Arial",
        14,
        "bold"
    ),

    fg="#38bdf8",

    bg="#172554"

).pack(
    fill="x"
)


tk.Label(

    dash,

    textvariable=stage,

    font=(
        "Arial",
        21,
        "bold"
    ),

    fg="#4ade80",

    bg="#172554"

).pack(
    fill="x"
)


tk.Label(

    dash,

    text="RISK",

    fg="white",

    bg="#172554"

).pack(
    pady=(3, 0)
)


tk.Label(

    dash,

    textvariable=risk,

    font=(
        "Arial",
        17,
        "bold"
    ),

    fg="#facc15",

    bg="#172554"

).pack()


tk.Label(

    dash,

    textvariable=alert,

    wraplength=400,

    fg="#fecaca",

    bg="#3b1d1d",

    font=(
        "Arial",
        10
    )

).pack(

    padx=15,

    pady=8

)


# ============================================================
# BUTTONS
# ============================================================

tk.Button(

    root,

    text="SIMULATE HEALTH",

    command=simulate,

    bg="#2563eb",

    fg="white",

    font=(
        "Arial",
        11,
        "bold"
    )

).place(

    x=110,

    y=600

)


tk.Button(

    root,

    text="ISS MODE",

    command=iss_mode,

    bg="#166534",

    fg="white",

    font=(
        "Arial",
        11,
        "bold"
    )

).place(

    x=270,

    y=600

)


tk.Button(

    root,

    text="MOON MODE",

    command=moon_mode,

    bg="#475569",

    fg="white",

    font=(
        "Arial",
        11,
        "bold"
    )

).place(

    x=390,

    y=600

)


tk.Button(

    root,

    text="MARS MODE",

    command=mars_mode,

    bg="#b91c1c",

    fg="white",

    font=(
        "Arial",
        11,
        "bold"
    )

).place(

    x=520,

    y=600

)


tk.Button(

    root,

    text="REFRESH NASA DATA",

    command=lambda: threading.Thread(

        target=download_nasa_data,

        daemon=True

    ).start(),

    bg="#0891b2",

    fg="white",

    font=(
        "Arial",
        11,
        "bold"
    )

).place(

    x=640,

    y=600

)


# ============================================================
# FOOTER
# ============================================================

tk.Label(

    root,

    text=(
        "NASA DATA: OSDR • RadLab • ISS • DosTel"
    ),

    font=(
        "Arial",
        10,
        "bold"
    ),

    fg="#7dd3fc",

    bg="#08111f"

).place(

    x=390,

    y=675

)


tk.Label(

    root,

    text=(
        "MONITOR → ANALYZE → DETECT RISK → ALERT → ACT"
    ),

    font=(
        "Arial",
        11,
        "bold"
    ),

    fg="white",

    bg="#08111f"

).place(

    x=370,

    y=705

)


# ============================================================
# START SYSTEM
# ============================================================

simulate()

camera()


# Start NASA data download
threading.Thread(

    target=download_nasa_data,

    daemon=True

).start()


# ============================================================
# CLOSE HANDLER
# ============================================================

def close_app():

    try:

        cap.release()

        pose.close()

        cv2.destroyAllWindows()

    except:

        pass

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    close_app
)


# ============================================================
# RUN
# ============================================================

root.mainloop()
