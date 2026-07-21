from psychopy import visual, core, event
from openpyxl import Workbook
from phase_func.both_question import run_both_task
from phase_func.food_web_check import run_foodweb_task
from phase_func.gene_check import run_gene_task
from phase_func.habitat_check import run_habitat_task
from phase_func.fixation import attention_check
from phase_func.show_info import show_all_food_phase,  show_all_gene_phase, show_all_habitat_phase
from phase_func.test_gene import run_gene_task
from phase_func.test_food import run_food_task
from phase_func.test_habitat import run_habitat_task
from save_func.save_results import (
    save_check_results_to_excel,
    save_results_to_excel,
    save_results_to_excel_A,
)
from initiate import initiate
from utils.labjack_trigger import close_labjack, trigger_timing_log
from sys_func.frame_count import frame_log
from config import MODE, REFRESH_RATE_TOLERANCE_HZ, SESSION_TYPE, STIMULI_DIR, TARGET_REFRESH_HZ
import pandas as pd
import random
import os
#.\new_ven\Scripts\activate  이후 python main.py 


def save_diagnostic_logs(save_directory):
    diagnostic_logs = (
        (frame_log, "frame_log.xlsx"),
        (trigger_timing_log, "trigger_timing_log.xlsx"),
    )

    for log_data, filename in diagnostic_logs:
        save_path = os.path.join(save_directory, filename)
        try:
            pd.DataFrame(log_data).to_excel(save_path, index=False)
            print(f"[Diagnostics] saved: {save_path}")
        except Exception as e:
            print(f"[Diagnostics] failed to save {filename}: {e}")


def save_display_metadata(save_directory, actual_refresh_hz):
    metadata_path = os.path.join(save_directory, "metadata.txt")
    with open(metadata_path, "a", encoding="utf-8") as f:
        f.write(f"Actual Refresh Hz: {actual_refresh_hz:.2f}\n")


def run_experiment(save_directory, handle):
    win = visual.Window(
        size=(1280, 800),
        fullscr=True,
        units="pix",
        color="lightgray"
    )

    actual_refresh_hz = win.getActualFrameRate()
    if actual_refresh_hz is None:
        win.close()
        raise RuntimeError(
            "모니터 주사율을 안정적으로 측정하지 못했습니다. "
            "실험을 시작하지 않습니다."
        )

    if abs(actual_refresh_hz - TARGET_REFRESH_HZ) > REFRESH_RATE_TOLERANCE_HZ:
        win.close()
        raise RuntimeError(
            f"모니터 주사율이 {actual_refresh_hz:.2f} Hz로 측정되었습니다. "
            f"{TARGET_REFRESH_HZ} Hz로 설정한 뒤 다시 실행하세요."
        )

    print(f"[Session] type: {SESSION_TYPE}")
    print(f"[Display] refresh rate: {actual_refresh_hz:.2f} Hz")
    save_display_metadata(save_directory, actual_refresh_hz)


     # 질문 한국어로 수정
    # ui를 이전 태스크랑 유사하게
    # 지금 테스크를 LLM에 제로샷으로 풀게했을때 스트럭처가 나타날것인가?
    # LLM의 대답으로 스트럭처를 이용했는지 판단할수있나? (그게 학습된 방대한 데이터에 의한건지 prior구조에 의한건지 )
    # reasoning model / non-reasoning model
    # api key
    # 개개인이 가진 structure prior를 답변으로부터 유추할수있는지
    '''나오는 동물개체가 같고 물어보는 특징만 다른 트라이얼을 여러번 물어봐야한다 
    유전자/서식지/푸드웹 중복포함 각 50문항?
    문항이 많아지니까 2개테마씩만 동물개수를 줄이고 20조합으로 3개씩 반복(같은 구조내 옵션만 위치 랜덤) 각 테마당 60문항
    120문항
    체크질문을 7개로 줄이기 
    먹이사슬을 물어볼때 리버스, 포워드가 확실히 구분이 되도록 질문을 바꾼다 '''

    json_path = os.path.join(STIMULI_DIR, "web.json")
    food_json_path = os.path.join(STIMULI_DIR, "trial_list2.json")
    gene_json_path = os.path.join(STIMULI_DIR, "trial_list1.json")
    habitat_json_path = os.path.join(STIMULI_DIR, "trial_list3.json")
    
   
    if MODE==0:
        show_all_food_phase(win, handle)
        show_all_gene_phase(win, handle)
        show_all_habitat_phase(win, handle)

        food_check_results = run_food_task(win,handle)
        save_check_results_to_excel(
            food_check_results,
            "food",
            save_directory,
            "results_food_check.xlsx",
        )

        show_all_food_phase(win, handle)
        show_all_gene_phase(win, handle)
        show_all_habitat_phase(win, handle)

        gene_check_results = run_gene_task(win,handle)
        save_check_results_to_excel(
            gene_check_results,
            "gene",
            save_directory,
            "results_gene_check.xlsx",
        )


        show_all_food_phase(win, handle)
        show_all_gene_phase(win, handle)
        show_all_habitat_phase(win, handle)

        habitat_check_results = run_habitat_task(win,handle)
        save_check_results_to_excel(
            habitat_check_results,
            "habitat",
            save_directory,
            "results_habitat_check.xlsx",
        )

    elif MODE==1:
       
        show_all_gene_phase(win, handle)
        show_all_habitat_phase(win, handle)

        gene_check_results = run_gene_task(win,handle)
        save_check_results_to_excel(
            gene_check_results,
            "gene",
            save_directory,
            "results_gene_check.xlsx",
        )


        
        show_all_gene_phase(win, handle)
        show_all_habitat_phase(win, handle)

        habitat_check_results = run_habitat_task(win,handle)
        save_check_results_to_excel(
            habitat_check_results,
            "habitat",
            save_directory,
            "results_habitat_check.xlsx",
        )

    elif MODE==2:
        show_all_food_phase(win, handle)
        show_all_habitat_phase(win, handle)

        food_check_results = run_food_task(win,handle)
        save_check_results_to_excel(
            food_check_results,
            "food",
            save_directory,
            "results_food_check.xlsx",
        )


        show_all_food_phase(win, handle)
        show_all_habitat_phase(win, handle)

        habitat_check_results = run_habitat_task(win,handle)
        save_check_results_to_excel(
            habitat_check_results,
            "habitat",
            save_directory,
            "results_habitat_check.xlsx",
        )

    elif MODE==3:
        show_all_food_phase(win, handle)
        show_all_gene_phase(win, handle)

        food_check_results = run_food_task(win,handle)
        save_check_results_to_excel(
            food_check_results,
            "food",
            save_directory,
            "results_food_check.xlsx",
        )

        show_all_food_phase(win, handle)
        show_all_gene_phase(win, handle)

        gene_check_results = run_gene_task(win,handle)
        save_check_results_to_excel(
            gene_check_results,
            "gene",
            save_directory,
            "results_gene_check.xlsx",
        )

    
       
    '''
    show_all_food_phase(win, handle)
    show_all_gene_phase(win, handle)
    show_all_habitat_phase(win, handle)

    run_food_task(win)

    #results0 =run_foodweb_task(win, json_path,handle)

    #save_results_to_excel_A(results0, save_directory, "results_cf.xlsx")

    show_all_food_phase(win, handle)
    show_all_gene_phase(win, handle)
    show_all_habitat_phase(win, handle)

    run_gene_task(win)

    #results1 =run_gene_task(win, json_path,handle)

    #save_results_to_excel_A(results1, save_directory, "results_cg.xlsx")

    

    show_all_food_phase(win, handle)
    show_all_gene_phase(win, handle)
    show_all_habitat_phase(win, handle)

    run_habitat_task(win)

    #results2 = run_habitat_task(win, json_path,handle)

    #save_results_to_excel_A(results2, save_directory, "results_ch.xlsx")
        
    '''

    attention_check(win)


    

    


    results = run_both_task(
        win=win,
        food_json_path=food_json_path,
        gene_json_path=gene_json_path,
        habitat_json_path=habitat_json_path,
        handle=handle,
        on_trial_complete=lambda completed_results: save_results_to_excel(
            completed_results,
            save_directory,
            "results_t.xlsx",
        ),
    )

    print(results)

    win.close()
    core.quit()


def main():
    save_directory, handle = initiate()

    try:
        run_experiment(save_directory, handle)
    finally:
        try:
            save_diagnostic_logs(save_directory)
        finally:
            close_labjack(handle)


if __name__ == "__main__":
    main()
