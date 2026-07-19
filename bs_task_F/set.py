import sys
import subprocess
import os
import shutil
from pathlib import Path

VENV_DIR = "new_env"
REQUIREMENTS_FILE = "requirements.txt"
EYETRACKER_WHL_PATH = os.path.join(
    "eye_function",
    "psychopy_eyetracker_sr_research-0.0.5-py3-none-any.whl"
)
PYTHON_REQUIRED = (3, 10)


# =========================
# Python 3.10 찾기
# =========================
def find_python310():
    candidates = [
        r"C:\Python310\python.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Python\Python310\python.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), r"Python310\python.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), r"Python310\python.exe"),
    ]

    try:
        output = subprocess.check_output("where python", shell=True, text=True)
        for line in output.splitlines():
            candidates.append(line.strip())
    except subprocess.CalledProcessError:
        pass

    for path in candidates:
        if os.path.exists(path):
            try:
                ver = subprocess.check_output([path, "--version"], text=True).strip()
                if f"Python {PYTHON_REQUIRED[0]}.{PYTHON_REQUIRED[1]}" in ver:
                    return path
            except Exception:
                continue

    while True:
        user_input = input("Python 3.10 경로 입력: ").strip('"')
        if os.path.exists(user_input):
            try:
                ver = subprocess.check_output([user_input, "--version"], text=True).strip()
                if f"Python {PYTHON_REQUIRED[0]}.{PYTHON_REQUIRED[1]}" in ver:
                    return user_input
            except Exception:
                pass
        print(" 잘못된 경로입니다.")


# =========================
# 가상환경 생성 (무조건 재생성)
# =========================
def create_virtualenv(python_exe):
    if os.path.exists(VENV_DIR):
        print(f"[INFO] 기존 env 삭제: {VENV_DIR}")
        shutil.rmtree(VENV_DIR)

    print(f"[INFO] 새 env 생성 중...")
    subprocess.check_call([python_exe, "-m", "venv", VENV_DIR])


# =========================
# venv python 경로
# =========================
def get_python_path():
    if os.name == "nt":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_DIR, "bin", "python")


# =========================
# 설치
# =========================
def install_requirements():
    python_path = get_python_path()

    # pip 업그레이드 (핵심 수정 부분)
    print("[INFO] pip 업그레이드 (env)...")
    subprocess.check_call([
        python_path,
        "-m", "pip",
        "install",
        "--upgrade",
        "pip"
    ])

    # requirements 설치
    if os.path.exists(REQUIREMENTS_FILE):
        print("[INFO] requirements 설치 중...")
        subprocess.check_call([
            python_path,
            "-m", "pip",
            "install",
            "-r",
            REQUIREMENTS_FILE
        ])
    else:
        print("[WARNING] requirements.txt 없음 → 스킵")

    # eyetracker 설치
    if os.path.exists(EYETRACKER_WHL_PATH):
        print("[INFO] eyetracker 설치 중...")
        subprocess.check_call([
            python_path,
            "-m", "pip",
            "install",
            EYETRACKER_WHL_PATH
        ])
    else:
        print("[WARNING] eyetracker whl 없음 → 스킵")


# =========================
# 실행
# =========================
if __name__ == "__main__":

    python310 = find_python310()
    print(f"[INFO] Python: {python310}")

    create_virtualenv(python310)
    install_requirements()

    print("\nEnvironment setup complete.")
    if os.name == "nt":
        print("실행: new_env\\Scripts\\activate")
    else:
        print("실행: source new_env/bin/activate")