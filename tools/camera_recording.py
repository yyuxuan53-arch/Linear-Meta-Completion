import cv2
import subprocess
import os
import time
import shutil
from datetime import datetime


# ============================================================
# SETTINGS
# ============================================================

CAMERA = "/dev/video0"

WIDTH = 3840
HEIGHT = 2160
FPS = 30

# Formal experiment:
RECORD_SECONDS = 300

# For testing, temporarily use:
# RECORD_SECONDS = 30

SAVE_DIR = os.path.expanduser("~/Kilobot_Recordings")
os.makedirs(SAVE_DIR, exist_ok=True)

PREVIEW_WIDTH = 1280


# ============================================================
# CHECK FFMPEG
# ============================================================

ffmpeg_path = shutil.which("ffmpeg")
ffprobe_path = shutil.which("ffprobe")

if ffmpeg_path is None:
    print("ERROR: ffmpeg is not installed.")
    print()
    print("Install it with:")
    print("sudo apt update")
    print("sudo apt install ffmpeg")
    raise SystemExit(1)

if ffprobe_path is None:
    print("ERROR: ffprobe is not installed.")
    raise SystemExit(1)

print(f"FFmpeg:  {ffmpeg_path}")
print(f"FFprobe: {ffprobe_path}")


# ============================================================
# EXPERIMENT NAME
# ============================================================

run_name = input("\nEnter experiment name: ").strip()

if not run_name:
    run_name = "test"

output_path = os.path.join(
    SAVE_DIR,
    f"{run_name}_raw.mkv"
)

# Never overwrite an existing experiment
if os.path.exists(output_path):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_path = os.path.join(
        SAVE_DIR,
        f"{run_name}_{timestamp}_raw.mkv"
    )


# ============================================================
# INFORMATION
# ============================================================

print()
print("============================================================")
print("KILOBOT 4K RECORDING")
print("============================================================")
print(f"Camera:      {CAMERA}")
print(f"Resolution:  {WIDTH} x {HEIGHT}")
print(f"FPS:         {FPS}")
print(f"Real time:   {RECORD_SECONDS} seconds")
print(f"Output:      {output_path}")
print("============================================================")
print()


# ============================================================
# OPEN CAMERA FOR OPENCV PREVIEW
# ============================================================

print("Opening camera for preview...")

cap = cv2.VideoCapture(CAMERA, cv2.CAP_V4L2)

if not cap.isOpened():
    print(f"ERROR: Could not open {CAMERA}")
    raise SystemExit(1)


# Ask BRIO for MJPEG
cap.set(
    cv2.CAP_PROP_FOURCC,
    cv2.VideoWriter_fourcc(*"MJPG")
)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
cap.set(cv2.CAP_PROP_FPS, FPS)


# Give camera time to initialise
time.sleep(2)


# ============================================================
# CHECK ACTUAL CAMERA SETTINGS
# ============================================================

actual_width = int(
    cap.get(cv2.CAP_PROP_FRAME_WIDTH)
)

actual_height = int(
    cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
)

actual_fps = cap.get(
    cv2.CAP_PROP_FPS
)

fourcc_int = int(
    cap.get(cv2.CAP_PROP_FOURCC)
)

actual_fourcc = "".join(
    [
        chr((fourcc_int >> 8 * i) & 0xFF)
        for i in range(4)
    ]
)


print("Camera opened.")
print()
print(f"Actual resolution: {actual_width} x {actual_height}")
print(f"Actual FPS:        {actual_fps}")
print(f"Actual FOURCC:     {actual_fourcc}")
print()


if actual_width != WIDTH or actual_height != HEIGHT:

    print("WARNING:")
    print("Camera did not open at requested 4K resolution.")
    print()


if abs(actual_fps - FPS) > 0.5:

    print("WARNING:")
    print("Camera did not report the requested 30 FPS.")
    print()


# ============================================================
# PREVIEW
# ============================================================

print("============================================================")
print("PREVIEW READY")
print()
print("S = start recording")
print("Q = quit")
print("============================================================")
print()


start_recording = False


while True:

    ret, frame = cap.read()

    if not ret:
        print("ERROR: Failed to read camera frame.")
        break


    # --------------------------------------------------------
    # Create preview copy
    # --------------------------------------------------------

    preview = frame.copy()

    cv2.putText(
        preview,
        "READY - Press S to start 5 min recording",
        (60, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (255, 255, 255),
        5
    )


    # --------------------------------------------------------
    # Resize preview only
    # --------------------------------------------------------

    scale = PREVIEW_WIDTH / WIDTH

    preview_height = int(
        HEIGHT * scale
    )

    display = cv2.resize(
        preview,
        (PREVIEW_WIDTH, preview_height),
        interpolation=cv2.INTER_AREA
    )


    cv2.imshow(
        "Kilobot 4K Recording - Preview",
        display
    )


    # --------------------------------------------------------
    # Keyboard
    # --------------------------------------------------------

    key = cv2.waitKey(1) & 0xFF


    if key in (ord("s"), ord("S")):

        start_recording = True
        break


    elif key in (ord("q"), ord("Q"), 27):

        start_recording = False
        break


# ============================================================
# RELEASE OPENCV CAMERA
# ============================================================

cap.release()
cv2.destroyAllWindows()


if not start_recording:

    print("Recording cancelled.")
    raise SystemExit(0)


print()
print("Releasing camera from OpenCV...")

# Give Linux/V4L2 time to fully release the device
time.sleep(1.0)


# ============================================================
# FFMPEG COMMAND
# ============================================================

#
# IMPORTANT:
#
# There is intentionally NO:
#
#       -t 300
#
# here.
#
# Python controls the real-world recording duration using
# time.monotonic().
#
# FFmpeg simply records until Python sends "q".
#

ffmpeg_command = [

    ffmpeg_path,

    "-hide_banner",

    # --------------------------------------------------------
    # V4L2 input
    # --------------------------------------------------------

    "-f", "v4l2",

    # Use real wall-clock timestamps
    "-use_wallclock_as_timestamps", "1",

    # BRIO MJPEG stream
    "-input_format", "mjpeg",

    # 4K
    "-video_size", f"{WIDTH}x{HEIGHT}",

    # 30 FPS
    "-framerate", str(FPS),

    # Camera
    "-i", CAMERA,


    # --------------------------------------------------------
    # DO NOT RE-ENCODE
    # --------------------------------------------------------

    "-c:v", "copy",


    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    "-y",

    output_path
]


# ============================================================
# SHOW COMMAND
# ============================================================

print()
print("============================================================")
print("STARTING FFMPEG")
print("============================================================")
print()
print("Recording mode:")
print(f"  {WIDTH} x {HEIGHT}")
print(f"  {FPS} FPS")
print("  MJPEG stream copy")
print()
print(
    f"Python will stop recording after "
    f"{RECORD_SECONDS} REAL seconds."
)
print()
print("Starting camera...")
print("============================================================")
print()


# ============================================================
# START FFMPEG
# ============================================================

try:

    process = subprocess.Popen(
        ffmpeg_command,

        # Needed so Python can send "q"
        stdin=subprocess.PIPE,

        # Keep FFmpeg information visible
        stdout=None,
        stderr=None,

        text=True
    )

except Exception as e:

    print()
    print("ERROR: Could not start FFmpeg.")
    print(e)

    raise SystemExit(1)


# ============================================================
# WAIT TO SEE IF FFMPEG STARTED SUCCESSFULLY
# ============================================================

time.sleep(2)


if process.poll() is not None:

    print()
    print("ERROR:")
    print("FFmpeg stopped immediately.")
    print()
    print("Check the FFmpeg error above.")

    raise SystemExit(1)


# ============================================================
# REAL-WORLD TIMER STARTS HERE
# ============================================================

record_start = time.monotonic()

print()
print("============================================================")
print("RECORDING STARTED")
print("============================================================")
print()
print("Real elapsed time:")
print()


last_second = -1


try:

    while True:

        # ----------------------------------------------------
        # REAL elapsed time
        # ----------------------------------------------------

        elapsed = time.monotonic() - record_start

        remaining = max(
            0,
            RECORD_SECONDS - elapsed
        )


        # ----------------------------------------------------
        # Print once per second
        # ----------------------------------------------------

        current_second = int(elapsed)

        if current_second != last_second:

            last_second = current_second

            print(
                f"\r"
                f"REAL TIME: "
                f"{elapsed:6.1f} / "
                f"{RECORD_SECONDS} s"
                f"    "
                f"Remaining: "
                f"{remaining:6.1f} s",
                end="",
                flush=True
            )


        # ----------------------------------------------------
        # Check whether FFmpeg crashed
        # ----------------------------------------------------

        if process.poll() is not None:

            print()
            print()
            print("ERROR:")
            print("FFmpeg stopped before recording finished.")

            break


        # ----------------------------------------------------
        # Stop after REAL wall-clock duration
        # ----------------------------------------------------

        if elapsed >= RECORD_SECONDS:

            print()
            print()
            print(
                f"Reached {RECORD_SECONDS} "
                f"real-world seconds."
            )

            break


        time.sleep(0.05)


except KeyboardInterrupt:

    print()
    print()
    print("Recording manually interrupted.")


# ============================================================
# STOP FFMPEG CLEANLY
# ============================================================

if process.poll() is None:

    print()
    print("Stopping FFmpeg cleanly...")

    try:

        # FFmpeg understands q = quit
        process.stdin.write("q\n")
        process.stdin.flush()

    except Exception:
        pass


    try:

        process.wait(timeout=10)

    except subprocess.TimeoutExpired:

        print("FFmpeg did not stop cleanly.")
        print("Terminating process...")

        process.terminate()

        try:
            process.wait(timeout=5)

        except subprocess.TimeoutExpired:

            print("Killing FFmpeg...")

            process.kill()
            process.wait()


# ============================================================
# FINAL REAL ELAPSED TIME
# ============================================================

real_elapsed = time.monotonic() - record_start


print()
print("============================================================")
print("RECORDING FINISHED")
print("============================================================")
print()
print(
    f"Actual real recording time: "
    f"{real_elapsed:.2f} seconds"
)
print()
print("Saved to:")
print(output_path)
print()


# ============================================================
# CHECK FILE EXISTS
# ============================================================

if not os.path.exists(output_path):

    print("ERROR:")
    print("Video file was not created.")

    raise SystemExit(1)


file_size = os.path.getsize(output_path)

print(
    f"File size: "
    f"{file_size / (1024 ** 3):.2f} GB"
)

print()


# ============================================================
# FFPROBE
# ============================================================

print("============================================================")
print("CHECKING VIDEO WITH FFPROBE")
print("============================================================")
print()


ffprobe_command = [

    ffprobe_path,

    "-v", "error",

    "-select_streams", "v:0",

    "-show_entries",
    (
        "stream="
        "codec_name,"
        "width,"
        "height,"
        "r_frame_rate,"
        "avg_frame_rate,"
        "nb_frames:"
        "format="
        "duration,"
        "size"
    ),

    "-of",
    "default=noprint_wrappers=1",

    output_path
]


subprocess.run(ffprobe_command)


# ============================================================
# FINAL MESSAGE
# ============================================================

print()
print("============================================================")
print("EXPECTED FOR FORMAL 5-MIN RECORDING")
print("============================================================")
print()
print("Resolution:")
print("  3840 x 2160")
print()
print("Frame rate:")
print("  approximately 30 FPS")
print()
print("Real recording duration:")
print("  approximately 300 seconds")
print()
print("Expected frames for 5 min @ 30 FPS:")
print("  approximately 9000")
print()
print("IMPORTANT:")
print("  Keep this *_raw.mkv file unchanged.")
print("  Do cropping / sampling / analysis later.")
print()
print("============================================================")
