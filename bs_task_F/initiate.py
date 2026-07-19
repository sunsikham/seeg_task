
import os
import sys
import platform
from datetime import datetime
from labjack import ljm
from config import HANDLE


def define_save(base_dir, subject_id):
    """
    세이브 폴더 생성 함수
    base_dir : 프로젝트 최상위 폴더
    subject_id : 실험 참여자 ID (예: 'subject01')
    """
    save_dir = os.path.join(base_dir, 'Data', subject_id)
    os.makedirs(save_dir, exist_ok=True)
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

    # 데이터 저장 경로 생성
    save_directory = define_save(current_folder, subject_id)
    print(f"Data will be saved to: {save_directory}")


    # 메타데이터 저장 (간단하게 텍스트로 저장)
    metadata_path = os.path.join(save_directory, 'metadata.txt')
    with open(metadata_path, 'w') as f:
        f.write(f"Subject ID: {subject_id}\n")
        f.write(f"Date: {datetime.now()}\n")
        f.write(f"OS: {os_name}\n")

    #labjack 초기화

    handle = None

    try:
        handle = ljm.openS("T4", "ANY", "ANY")
        print(" LabJack connected")
        info = ljm.getHandleInfo(handle)
        print("Connected:", info)

        names = [
            "EIO_DIRECTION",
            "EIO_STATE",
            "CIO_DIRECTION",
            "CIO_STATE"
        ]

        ljm.eWriteNames(
            handle,
            len(names),
            names,
            [0xFF, 0, 0x0F, 0]
        )

    except Exception as e:
        print(" LabJack not found → running without TTL")
        handle = None

    print("LabJack handle:", handle)
    

    

    print("Initialization complete.")

    return save_directory,handle