import os
import sys
import subprocess
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_NAME = "AIClaudeClaw"
DIST_DIR = os.path.join(ROOT_DIR, "dist")
BUILD_DIR = os.path.join(ROOT_DIR, "build")

def build():
    print("=========================================================")
    print("AI Claw - Standalone Executable Builder (.exe)")
    print("=========================================================\n")

    for d in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        f"--name={OUTPUT_NAME}",
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.sip",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=google.genai",
        "--hidden-import=google.generativeai",
        "--hidden-import=anthropic",
        "--hidden-import=openai",
        "--hidden-import=PIL",
        "--hidden-import=psutil",
        "--hidden-import=pyautogui",
        "--hidden-import=pyscreeze",
        "--hidden-import=pynput",
        "--hidden-import=cv2",
        "--collect-all=cv2",
        "--collect-all=ui",
        "--collect-all=core",
        "--add-data=config;config",
        "--clean",
        os.path.join(ROOT_DIR, "main.py")
    ]

    print("Executing:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=ROOT_DIR)

    if res.returncode == 0:
        dist_app = os.path.join(DIST_DIR, OUTPUT_NAME)
        # Copy extra dirs
        for extra in ["config", "presets", "guide"]:
            s = os.path.join(ROOT_DIR, extra)
            d = os.path.join(dist_app, extra)
            if os.path.exists(s) and not os.path.exists(d):
                shutil.copytree(s, d, dirs_exist_ok=True)

        print("\n=========================================================")
        print(f"BUILD SUCCESSFUL! Standalone Executable created:")
        print(f"Path: {os.path.join(dist_app, f'{OUTPUT_NAME}.exe')}")
        print("=========================================================")
    else:
        print("\nBuild failed with code:", res.returncode)

if __name__ == "__main__":
    build()
