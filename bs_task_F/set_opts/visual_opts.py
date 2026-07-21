# ui_config.py

from config import (
    FEEDBACK_DURATION_S,
    FEEDBACK_FRAMES,
    RESPONSE_TIMEOUT_FRAMES,
    RESPONSE_TIMEOUT_S,
)

UI_CONFIG = {
    # ===== 텍스트 =====
    "question": {
        "pos": (0, 300),
        "height": 60,
        "wrapWidth": 1200,
        "color": "black",
        "font": "Malgun Gothic"
    },

    "option": {
        "left_pos": (-400, -50),
        "right_pos": (400, -50),
        "height": 60,
        "color": "black",
        "font": "Malgun Gothic"
    },

    # ===== 이미지 =====
    "image": {
        "left_pos": (-400, -180),
        "right_pos": (400, -180),
        "main_pos": (0, 60),
        "sub_left_pos": (-650, 300),
        "sub_right_pos": (650, 300),

        # 정사각형
        "size": (180, 180),
        "size2": (120, 120)
    },

    "feedback_text": {

    "left_pos": (0, -220),
    "right_pos": (0, -220)

    },

    # ===== 화살표 =====
    "arrow": {
        "left_pos": (-400, -330),
        "right_pos": (400, -330),
        "height": 120,
        "color": "black",
        "active_color": "yellow"
    },

    # ===== 타이밍 =====
    "timing": {
        "timeout": RESPONSE_TIMEOUT_S,
        "timeout_frames": RESPONSE_TIMEOUT_FRAMES,
        "feedback_duration": FEEDBACK_DURATION_S,
        "feedback_frames": FEEDBACK_FRAMES,
        "iti": 0.3,   # trial 간 간격
        "show_full" : 1800,
        "show_random" : 1200
    },

    "image_phase": {

        # =====================================
        # food 전체 6개
        # 2 x 3 grid
        # =====================================
        "food_all": {

            "position": (0, 0),

            "size": (1600, 800)
        },

        # =====================================
        # gene 전체 3개
        # triangle layout
        # =====================================
        "gene_all": {

            "position": (0, 0),

            "size": (1600, 800)
        },

        "habitat_all": {

            "position": (0, 0),

            "size": (1500, 800)
        },


        # =====================================
        # food 랜덤 2개
        # vertical layout
        # =====================================
        "food_pair": {

            "positions": [

                (0, 220),
                (0, -220),
            ],

            "size": (800, 300)
        },

        # =====================================
        # gene 랜덤 1개
        # =====================================
        "gene_single": {

            "position": (0, 0),

            "size": (660, 500)
        }
    }
}


