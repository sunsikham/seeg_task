# SEEG Knowledge Task

PsychoPy로 구현된 동물 지식 구조 과제와 SEEG 기록을 관리하는 프로젝트입니다.
과제는 먹이사슬(food), 유전자 관계(gene), 서식지(habitat) 정보를 학습한 뒤
두 선택지 중 정답을 고르는 방식으로 구성되어 있습니다.

## 새 Windows 컴퓨터에서 빠른 시작

### 1. 준비

- Git 설치
- Python 3.10 설치
- Pupil Labs Neon과 Neon Companion이 설치된 휴대폰(시선 수집 시)
- SEEG 모드에서는 LabJack LJM Windows 드라이버 설치

### 2. 코드 받기

```powershell
git clone <repository-url>
cd seeg_task\bs_task_F
```

### 3. 실험 설정

`config.py`에서 세션 종류와 실험 MODE를 선택합니다.

```python
SESSION_TYPE = "BEHAVIORAL"  # 60 Hz, LabJack 사용 안 함
SESSION_TYPE = "SEEG"        # 144 Hz, LabJack 사용

MODE = 0  # food + gene + habitat
MODE = 1  # gene + habitat
MODE = 2  # food + habitat
MODE = 3  # food + gene
```

권장 화면 해상도는 1920×1080입니다.

### 4. 최초 설치

```powershell
setup.bat
```

### 5. 실험 실행

```powershell
run.bat
```

Neon을 사용할 때는 PC와 Companion 휴대폰을 같은 네트워크에 연결하고,
Companion에서 녹화를 먼저 시작한 뒤 `run.bat`을 실행합니다. 콘솔의
`Enter subject ID:`에 고유한 참가자 ID를 입력합니다. 결과는
`bs_task_F\Data\<subject_id>\`에 저장됩니다.

## 프로젝트 구조

```text
seeg_task/
├── bs_task_F/                  # PsychoPy 실험 코드
│   ├── main.py                 # 실험 실행 진입점
│   ├── config.py               # 실험 모드와 프레임 설정
│   ├── initiate.py             # 참가자 정보, 저장 폴더, LabJack 초기화
│   ├── phase_func/             # 학습·확인·본 과제 화면
│   ├── stimuli/                # 이미지와 trial JSON
│   ├── utils/                  # LabJack TTL 및 Neon 이벤트 전송
│   ├── save_func/              # 행동 결과 저장
│   ├── sys_func/               # trial 생성과 프레임 로그
│   └── Data/                   # 참가자별 행동 데이터
├── sub-01_task-KNOWLEDGE_02.EDF # 원본 SEEG 기록
└── edf_profile.py              # EDF 품질 점검 코드
```

원본 SEEG와 참가자 행동 데이터는 민감한 연구 데이터이므로 Git에서 추적하지
않습니다.

## 태스크 구조

이 실험은 동일한 6마리 동물을 다음 세 가지 관계 구조로 학습하고 판단하는
과제입니다.

- `food`: 동물 사이의 먹이사슬 관계
- `gene`: 동물 사이의 유전적 계통 관계
- `habitat`: 동물 사이의 서식지 위치 관계

참가자는 각 관계 구조를 본 뒤 동물을 직접 배치하는 확인 과제를 수행합니다.
이후 본 과제에서는 기준 동물(`premise`)과 두 선택지를 보고, 질문에서 요구한
관계상 더 가까운 동물을 왼쪽 또는 오른쪽 방향키로 선택합니다.

일반적인 관계 문항뿐 아니라 서로 다른 구조가 다른 답을 지지하도록 구성된
`Conflict` 또는 `Tree-conflict` 문항도 포함됩니다.

### 전체 진행 순서

현재 `main.py`와 `MODE=0` 설정을 기준으로 한 실행 순서는 다음과 같습니다.

```text
Companion 녹화 수동 시작
        ↓
참가자 ID 입력, Neon 연결 확인 및 LabJack 연결
        ↓
food·gene·habitat 전체 구조 제시
        ↓
food 배치 확인 과제
        ↓
food·gene·habitat 전체 구조 다시 제시
        ↓
gene 배치 확인 과제
        ↓
food·gene·habitat 전체 구조 다시 제시
        ↓
habitat 배치 확인 과제
        ↓
중간 확인 화면
        ↓
본 과제 120문항
        ↓
행동 결과와 진단 로그 저장·Neon 이벤트 flush
        ↓
프로그램 종료 후 Companion 녹화 수동 중지
```

각 MODE에 포함된 food, gene, habitat 확인 과제는 종류별로 한 번씩
실행됩니다. 각 확인 과제가 끝나면 모든 배치 시도와 정오답, 반응시간을
종류별 Excel 파일에 즉시 저장합니다.

### 본 과제 문항 구성

각 JSON 파일에는 구조별로 40문항이 정의되어 있습니다.

| 구조 | 일반 문항 | 충돌 문항 | 합계 |
|---|---:|---:|---:|
| Gene | Tree 28 | Conflict 12 | 40 |
| Food | Food 24 + Food-distance 4 | Conflict 8 + Conflict/distance 4 | 40 |
| Habitat | Habitat 28 | Tree-conflict 12 | 40 |

실제 실행 문항 수는 `MODE`에 따라 달라집니다. 현재 `MODE=0`에서는 food,
gene, habitat 각 40문항을 섞어서 총 120문항을 제시합니다.

### 단일 trial 진행

본 과제의 각 trial은 다음 순서로 진행됩니다.

```text
0.75~1.0초 무작위 ISI
        ↓
0.0~3.0초: 질문만 표시
        ↓
3.0~3.8초: 질문 + 기준 동물 이미지
        ↓
3.8~4.6초: 질문 + 기준 동물 + 왼쪽 후보 이름·이미지
        ↓
4.6~5.4초: 질문 + 기준 동물 + 양쪽 후보 이름·이미지
        ↓
5.4초부터: 전체 화면 유지 + 선택 화살표, 최대 10초
        ↓
응답 후 선택한 화살표 피드백 0.5초
```

단계 사이에 빈 화면이나 trial 내부 jitter는 넣지 않습니다. 이전 요소를
유지하면서 새 요소를 누적하고, 후보는 모든 trial에서 왼쪽에서 오른쪽
순서로 공개합니다. 60 Hz에서는 질문 180프레임, 각 공개 단계 48프레임이며,
144 Hz에서는 질문 432프레임, 각 공개 단계 115프레임입니다. 본 과제에서는
10문항마다 현재 MODE에 포함된 전체 관계 구조를 다시 보여주며, 참가자가
Enter를 눌러야 계속 진행됩니다.

### 반응시간 기록

- `rt1`: trial이 시작된 시점부터 응답까지의 시간
- `rt2`: 선택지가 나타난 시점부터 응답까지의 시간

본 과제 결과에는 무작위로 선택된 질문 특성(`question_target`)과 실제 제시한
전체 문장(`question_text`)도 함께 기록합니다. 질문·기준 동물·왼쪽 후보·오른쪽
후보·선택 화면의 상대적 flip 시각과 응답 감지 시각도 저장합니다.

`results_t.xlsx`는 각 trial이 완료될 때마다 갱신됩니다. 중간에 Escape로
종료하거나 오류가 발생해도 마지막으로 완료된 trial까지의 행동 결과가
남습니다. 저장 중 기존 체크포인트가 손상되지 않도록 임시 파일을 완성한 뒤
결과 파일을 교체합니다.

## 실행 환경

- Python 3.10
- Windows 실험 PC
- PsychoPy 2025.1.0
- LabJack T4
- Natus Quantum SEEG recording system
- 권장 화면 해상도 1920×1080

LabJack 연결에 실패하면 TTL 트리거 없이 실험이 계속 실행되도록 작성되어
있습니다. 현재 코드는 주사율을 자동 검사하지만 화면 해상도는 자동으로
검사하지 않으므로 Windows 디스플레이 설정에서 직접 확인합니다.

## 설치

Python 3.10을 먼저 설치한 뒤 `bs_task_F/setup.bat`을 실행합니다. 이 스크립트는
Python 3.10을 확인하고 `.venv`를 만든 다음 `requirements.txt`와 선택적
LabJack 패키지를 설치합니다. Python 자체는 자동으로 설치하지 않습니다.

Windows PowerShell 또는 명령 프롬프트에서는 다음처럼 실행할 수 있습니다.

```powershell
cd bs_task_F
setup.bat
```

## 실행

설치가 끝나면 `bs_task_F/run.bat`을 실행합니다.

```powershell
cd bs_task_F
run.bat
```

실행 직후 콘솔에 `Enter subject ID:`가 나타납니다. 참가자 ID를 입력하고
Enter를 누르면 전체화면 실험이 시작되고 결과는
`bs_task_F/Data/<subject_id>/`에 저장됩니다. 같은 참가자 ID의 폴더가 이미
있으면 기존 자료 보호를 위해 새 폴더나 파일을 만들지 않고 즉시 중단합니다.
실행마다 고유한 ID를 사용합니다.

## 실험 모드

실험 조건은 `bs_task_F/config.py`의 `MODE`로 선택합니다.

| MODE | 포함 조건 |
|---:|---|
| 0 | food + gene + habitat |
| 1 | gene + habitat |
| 2 | food + habitat |
| 3 | food + gene |

`config.py`의 `MODE = 0` 값을 원하는 번호로 바꾼 뒤 실행합니다. 실행 당시의
MODE는 참가자 메타데이터에 저장됩니다. MODE 0·1·2·3 모두 포함된 확인 과제를
종류별로 한 번씩 실행합니다.

### 세션 모드

`bs_task_F/config.py`의 `SESSION_TYPE`으로 녹화 환경을 선택합니다.

| SESSION_TYPE | 주사율 | LabJack TTL | SEEG 흰색 마커 | Neon AprilTag |
|---|---:|---|---|---|
| `BEHAVIORAL` | 60 Hz | 비활성 | 숨김 | `USE_NEON=True`이면 표시 |
| `SEEG` | 144 Hz | 활성 | 표시 | `USE_NEON=True`이면 표시 |

기본값은 `BEHAVIORAL`입니다. 각 모드의 주사율과 실제 모니터 주사율이
±1 Hz 범위에서 일치해야 실험이 시작됩니다. 선택한 세션 모드, 목표·실제
주사율, LabJack 활성·연결 여부는 `metadata.txt`에 저장됩니다.

## Neon 시선 수집

`bs_task_F/config.py`의 기본값은 `USE_NEON = True`입니다. 이 설정은
`BEHAVIORAL`과 `SEEG` 모두에서 Neon 이벤트와 화면 가장자리의 AprilTag 7개를
활성화합니다. 왼쪽 아래는 SEEG 흰색 광학 마커와 겹치지 않도록 비워 둡니다.
장비 없이 행동 과제만 점검할 때는 `USE_NEON = False`로 바꾸면 Neon 패키지,
휴대폰 연결 및 AprilTag 없이 기존 실행 경로를 사용합니다.

Neon 수집 순서는 다음과 같습니다.

1. PC와 Companion 휴대폰을 같은 네트워크에 연결합니다.
2. 휴대폰 Companion에서 참가자 녹화를 수동으로 시작합니다.
3. `run.bat`을 실행하고 고유한 참가자 ID를 입력합니다.
4. 프로그램이 완전히 종료되고 진단 로그 저장 메시지가 나온 뒤 녹화를
   수동으로 중지합니다.

`USE_NEON=True`인데 10초 안에 장치를 찾지 못하거나, 장치가 여러 대
발견되거나, 활성 녹화가 없으면 첫 자극 전에 중단합니다. 실험 도중 연결이
끊기면 자극은 계속 진행하며 이벤트의 원래 타임스탬프를 큐에 보관합니다.
재연결 후 같은 recording ID인지 확인하여 순서대로 재전송하고, 종료 시에는
화면을 먼저 닫은 뒤 최대 5초 동안 남은 이벤트 전송을 시도합니다.

Cloud section용 이벤트는 다음 구조로 기록됩니다.

```text
SESSION_START_<ID>_<DATETIME>
EXPERIMENT_START / EXPERIMENT_END / EXPERIMENT_ABORT
<DOMAIN>_INFO_SECTION_START / END + <DOMAIN>_INFO_O###
<DOMAIN>_CHECK_SECTION_START / END + attempt별 RESPONSE_VIEW·RESPONSE·FEEDBACK
MAIN_SECTION_START / END + MAIN_T###_QUESTION·PREMISE·OPTION_LEFT·OPTION_RIGHT·CHOICE
MAIN_T###_RESPONSE_LEFT|RIGHT_CORRECT|WRONG 또는 MAIN_T###_NO_RESPONSE
```

학습 정보 화면은 이미지가 처음 보이는 flip부터 Enter 입력까지, 확인 과제는
각 응답 시도와 피드백을 각각 별도 section으로 기록합니다. 본 과제는 문항마다
질문·기준 동물·왼쪽 후보·오른쪽 후보·선택의 5개 section을 만듭니다. 본 과제의
0.5초 피드백과 ISI는 녹화에는 포함되지만 section에는 포함하지 않습니다.

## 주요 출력 파일

참가자 폴더에는 다음 파일이 생성됩니다.

- `metadata.txt`: 참가자 ID, 실행 시각, 세션·과제 모드, 주사율, LabJack 상태
- `results_food_check.xlsx`: food 확인 과제의 모든 배치 시도와 정오답·반응시간
- `results_gene_check.xlsx`: gene 확인 과제의 모든 배치 시도와 정오답·반응시간
- `results_habitat_check.xlsx`: habitat 확인 과제의 모든 배치 시도와 정오답·반응시간
- `results_t.xlsx`: trial 정보, 실제 질문, 반응시간, onset 시각, 정오답
- `frame_log.xlsx`: PsychoPy 화면 flip 시각과 프레임 간격
- `trigger_timing_log.xlsx`: 트리거 코드, trial·phase, 전송·reset 시각과 성공 여부
- `neon_event_log.xlsx`: Neon 이벤트 순서, 세션·녹화 ID, PC/Companion 시각,
  재전송 횟수와 성공·오류 상태

`metadata.txt`와 모든 행동 결과 Excel에는 `session_id`와
`neon_recording_id`가 기록되어 Companion/Cloud 녹화와 로컬 결과를 연결할 수
있습니다. Neon 로그는 이벤트마다 `send_attempt=0`, `send_error=Queued`인 최초
큐 기록을 남긴 뒤 실제 전송 시도별 행을 추가합니다. Cloud 수신 여부를 점검할
때는 같은 `event_sequence`에서 `send_success=True`인 행이 있는지 확인합니다.

`results_t.xlsx`의 주요 추가 열은 다음과 같습니다.

```text
question_target
question_text
question_onset_s
premise_onset_s
option_left_onset_s
option_right_onset_s
choice_onset_s
response_detected_s
```

## TTL 트리거

LabJack T4의 EIO0-EIO7을 8비트 데이터 라인으로 사용하고 CIO0의 상승
에지로 Natus Quantum에 값을 전달합니다.

| 코드 | 의미 |
|---:|---|
| 10 / 11 | food 확인 과제 시작 / 반응 |
| 12 / 13 | gene 확인 과제 시작 / 반응 |
| 14 / 15 | habitat 확인 과제 시작 / 반응 |
| 20 | 본 과제 질문 시작 (`QUESTION_ON`) |
| 21 | 정답 반응 (`CORRECT_RESPONSE`) |
| 22 | 오답 반응 (`WRONG_RESPONSE`) |
| 23 | 선택 화살표 시작 (`CHOICE_ON`) |
| 24 | 기준 동물 이미지 시작 (`PREMISE_ON`) |
| 25 | 왼쪽 후보 시작 (`OPTION_LEFT_ON`) |
| 26 | 오른쪽 후보 시작 (`OPTION_RIGHT_ON`) |
| 27 | 10초 무응답 (`NO_RESPONSE`) |
| 30 / 31 | food 정보 화면 / 변형 화면 |
| 32 / 33 | gene 정보 화면 / 변형 화면 |
| 34 / 35 | habitat 정보 화면 / 변형 화면 |

본 과제의 정상적인 한 trial 마커 순서는
`20 → 24 → 25 → 26 → 23 → 21/22/27`입니다. 모든 시각 자극 onset 트리거는
화면 flip에 맞춰 전송하고 다음 프레임에서 reset합니다. 실제 응답 마커는 선택
마커 reset 이후 키가 감지된 시점에 전송합니다. SEEG 모드에서는 각 onset에
흰색 광학 마커도 표시합니다. 트리거 정의의 기준 파일은
`bs_task_F/utils/labjack_trigger.py`입니다.

## 데이터 취급 주의사항

- 원본 EDF와 참가자 결과 파일을 수정하거나 덮어쓰지 않습니다.
- 테스트 실행에는 실제 참가자 ID를 사용하지 않습니다.


