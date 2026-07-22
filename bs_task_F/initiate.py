
import os
import sys
import platform
from datetime import datetime
from config import MODE, SESSION_TYPE, TARGET_REFRESH_HZ, USE_LABJACK, USE_NEON
from utils.labjack_trigger import init_labjack


def define_save(base_dir, subject_id):
    """
    세이브 폴더 생성 함수
    base_dir : 프로젝트 최상위 폴더
    subject_id : 실험 참여자 ID (예: 'subject01')
    """
    save_dir = os.path.join(base_dir, 'Data', subject_id)
    if os.path.exists(save_dir):
        raise FileExistsError(
            f"Participant ID already exists: {subject_id}. "
            "Enter a new ID to protect existing data."
        )
    os.makedirs(save_dir)
    return save_dir

def initiate():
    """
    Raven Task 실험 초기화 함수
    
    Returns:
        visual_opt, device_opt, game_opt, eye_opt, save_directory
    """

    # 0) 기본 정보 및 환경 확인
    print("Initializing Raven Task environment...")

    current_folder = os.path.dirname(os.path.abspath(__file__))
    print(f"Current folder: {current_folder}")

    # test 모드 플래그 (실제 실험 환경에서는 False)
    test = False

    # 운영체제에 따른 사용자명 및 실험 참여자 ID 받기
    os_name = platform.system()
    if os_name == 'Darwin':  # macOS
        print("Running on macOS")
        username = os.getenv('USER')
        test = True  # test 모드로
        subject_id = input("Enter subject ID: ")
    elif os_name == 'Windows':
        print("Running on Windows")
        username = os.getenv('USERNAME')
        test = True  # test 모드로
        # 사용자에게 실험 참여자 ID 입력받기
        subject_id = input("Enter subject ID: ")
    else:
        print("Running on unknown OS")
        username = "OTHER"
        subject_id = "UNKNOWN"

    session_id = datetime.now().strftime("%Y%m%dT%H%M%S")

    # 데이터 저장 경로 생성
    save_directory = define_save(current_folder, subject_id)
    print(f"Data will be saved to: {save_directory}")


    if USE_LABJACK:
        # 패키지, 드라이버 또는 장치가 없으면 None을 반환한다.
        handle = init_labjack(device="T4", connection="ANY", identifier="ANY")
    else:
        handle = None
        print("[LabJack] BEHAVIORAL 모드에서 TTL 트리거를 비활성화합니다.")

    metadata_path = os.path.join(save_directory, 'metadata.txt')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        f.write(f"Subject ID: {subject_id}\n")
        f.write(f"Session ID: {session_id}\n")
        f.write(f"Date: {datetime.now()}\n")
        f.write(f"OS: {os_name}\n")
        f.write(f"Session Type: {SESSION_TYPE}\n")
        f.write(f"Task Mode: {MODE}\n")
        f.write(f"Target Refresh Hz: {TARGET_REFRESH_HZ}\n")
        f.write(f"LabJack Enabled: {USE_LABJACK}\n")
        f.write(f"LabJack Connected: {handle is not None}\n")
        f.write(f"Neon Enabled: {USE_NEON}\n")

    print("LabJack handle:", handle)
    

    

    print("Initialization complete.")

    return save_directory, handle, subject_id, session_id
