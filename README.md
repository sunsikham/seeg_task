# SEEG Knowledge Task

PsychoPy로 구현된 동물 지식 구조 과제와 SEEG 기록을 관리하는 프로젝트입니다.
과제는 먹이사슬(food), 유전자 관계(gene), 서식지(habitat) 정보를 학습한 뒤
두 선택지 중 정답을 고르는 방식으로 구성되어 있습니다.

## 프로젝트 구조

```text
seeg_task/
├── bs_task_F/                  # PsychoPy 실험 코드
│   ├── main.py                 # 실험 실행 진입점
│   ├── config.py               # 실험 모드와 프레임 설정
│   ├── initiate.py             # 참가자 정보, 저장 폴더, LabJack 초기화
│   ├── phase_func/             # 학습·확인·본 과제 화면
│   ├── stimuli/                # 이미지와 trial JSON
│   ├── utils/                  # LabJack TTL 트리거
│   ├── save_func/              # 행동 결과 저장
│   ├── sys_func/               # trial 생성과 프레임 로그
│   └── data/                   # 참가자별 행동 데이터
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

현재 `main.py`와 `MODE=1` 설정을 기준으로 한 실행 순서는 다음과 같습니다.

```text
참가자 ID 입력 및 LabJack 연결
        ↓
gene·habitat 전체 구조 제시
        ↓
gene 배치 확인 과제
        ↓
gene·habitat 전체 구조 다시 제시
        ↓
habitat 배치 확인 과제
        ↓
habitat 배치 확인 과제 반복
        ↓
중간 확인 화면
        ↓
본 과제 80문항
        ↓
results_t.xlsx 및 frame_log.xlsx 저장
```

현재 코드에서는 habitat 확인 과제가 두 번 연속 실행됩니다. 이것이 의도적인
반복인지 중복 호출인지는 실제 실험 프로토콜과 대조해야 합니다.

### 본 과제 문항 구성

각 JSON 파일에는 구조별로 40문항이 정의되어 있습니다.

| 구조 | 일반 문항 | 충돌 문항 | 합계 |
|---|---:|---:|---:|
| Gene | Tree 28 | Conflict 12 | 40 |
| Food | Food 24 + Food-distance 4 | Conflict 8 + Conflict/distance 4 | 40 |
| Habitat | Habitat 28 | Tree-conflict 12 | 40 |

실제 실행 문항 수는 `MODE`에 따라 달라집니다. 현재 `MODE=1`에서는 gene
40문항과 habitat 40문항을 섞어서 총 80문항을 제시합니다.

### 단일 trial 진행

본 과제의 각 trial은 다음 순서로 진행됩니다.

```text
0.75~1.0초 무작위 ISI
        ↓
질문과 기준 동물 제시
        ↓
420프레임 후 왼쪽·오른쪽 선택지 제시
        ↓
방향키로 응답
        ↓
정답 또는 오답 TTL 트리거 전송
        ↓
선택한 화살표 피드백
```

`waiting_frames=420`이므로 60 Hz 모니터에서는 선택지가 약 7초 뒤에
나타납니다. 본 과제에서는 10문항마다 현재 MODE에 포함된 전체 관계 구조를
다시 보여주며, 참가자가 Enter를 눌러야 계속 진행됩니다.

### 반응시간 기록

- `rt1`: trial이 시작된 시점부터 응답까지의 시간
- `rt2`: 선택지가 나타난 시점부터 응답까지의 시간

확인 과제의 반환 결과는 현재 `main.py`에서 별도의 결과 파일로 저장하지
않습니다. 본 과제의 반응과 정오답은 `results_t.xlsx`에 저장되며, 확인 과제를
포함한 화면 전환 정보는 `frame_log.xlsx`에 기록됩니다.

## 실행 환경

- Python 3.10
- Windows 실험 PC
- PsychoPy 2025.1.0
- LabJack T4
- Natus Quantum SEEG recording system

LabJack 연결에 실패하면 TTL 트리거 없이 실험이 계속 실행되도록 작성되어
있습니다. 실제 SEEG 실험 전에는 콘솔에서 LabJack 연결 성공 여부를 반드시
확인해야 합니다.

## 설치

Windows PowerShell 또는 명령 프롬프트에서:

```powershell
cd bs_task_F
py -3.10 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 실행

반드시 `bs_task_F` 폴더에서 실행합니다. 자극 파일 경로가 현재 작업 폴더를
기준으로 작성되어 있습니다.

```powershell
cd bs_task_F
.venv\Scripts\activate
python main.py
```

실행 시 참가자 ID를 입력하면 결과가 `bs_task_F/Data/<subject_id>/`에
저장됩니다. Windows에서는 기존 `data/` 폴더와 대소문자를 구분하지 않지만,
Linux에서는 `Data/`와 `data/`가 서로 다른 폴더이므로 주의해야 합니다.

## 실험 모드

실험 조건은 `bs_task_F/config.py`의 `MODE`로 선택합니다.

| MODE | 포함 조건 |
|---:|---|
| 0 | food + gene + habitat |
| 1 | gene + habitat |
| 2 | food + habitat |
| 3 | food + gene |

현재 설정은 코드의 `config.py`를 직접 확인해야 합니다. 실행 당시의
MODE는 참가자 메타데이터에 저장됩니다.

### 세션 모드

`bs_task_F/config.py`의 `SESSION_TYPE`으로 녹화 환경을 선택합니다.

| SESSION_TYPE | 주사율 | LabJack TTL | 동기화 마커 |
|---|---:|---|---|
| `BEHAVIORAL` | 60 Hz | 비활성 | 숨김 |
| `SEEG` | 144 Hz | 활성 | 표시 |

기본값은 `BEHAVIORAL`입니다. 각 모드의 주사율과 실제 모니터 주사율이
±1 Hz 범위에서 일치해야 실험이 시작됩니다. 선택한 세션 모드, 목표·실제
주사율, LabJack 활성·연결 여부는 `metadata.txt`에 저장됩니다.

## 주요 출력 파일

참가자 폴더에는 다음 파일이 생성됩니다.

- `metadata.txt`: 참가자 ID, 실행 시각, 세션·과제 모드, 주사율, LabJack 상태
- `results_t.xlsx`: trial 정보, 반응, 반응시간, 정오답
- `frame_log.xlsx`: PsychoPy 화면 flip 시각과 프레임 간격

## TTL 트리거

LabJack T4의 EIO0-EIO7을 8비트 데이터 라인으로 사용하고 CIO0의 상승
에지로 Natus Quantum에 값을 전달합니다.

| 코드 | 의미 |
|---:|---|
| 10 / 11 | food 확인 과제 시작 / 반응 |
| 12 / 13 | gene 확인 과제 시작 / 반응 |
| 14 / 15 | habitat 확인 과제 시작 / 반응 |
| 20 | 본 과제 premise 시작 |
| 21 / 22 | 본 과제 정답 / 오답 반응 |
| 23 | 선택지 제시 시작 |
| 30 / 31 | food 정보 화면 / 변형 화면 |
| 32 / 33 | gene 정보 화면 / 변형 화면 |
| 34 / 35 | habitat 정보 화면 / 변형 화면 |

트리거 정의의 기준 파일은 `bs_task_F/utils/labjack_trigger.py`입니다.

## 데이터 취급 주의사항

- 원본 EDF와 참가자 결과 파일을 수정하거나 덮어쓰지 않습니다.
- 테스트 실행에는 실제 참가자 ID를 사용하지 않습니다.
- 외부 공유 전에 EDF 헤더와 참가자 메타데이터를 익명화합니다.
- 코드 변경 후에는 실험용 PC에서 자극 표시, 키 입력, 결과 저장 및 TTL
  수신을 모두 점검합니다.

## 현재 상태

이 폴더에는 여러 시점의 실험 결과가 포함되어 있으며 현재 코드가 과거
세션에서 사용한 코드와 완전히 동일하지 않을 수 있습니다. 과거 데이터를
재분석할 때는 기록 날짜, MODE, 결과 파일 형식 및 EDF 트리거를 함께
확인해야 합니다.
