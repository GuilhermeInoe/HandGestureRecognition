import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import sys

# --- Configurações do Estilingue ---
SLINGSHOT_IMAGE = 'slingshot.png'
PIXELS_ABOVE_SLINGSHOT = 120
CONFIDENCE_LEVEL = 0.8
anchor_pos = None # (x, y) da âncora


mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,  
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_drawing = mp.solutions.drawing_utils

screen_w, screen_h = pyautogui.size()
mouse_down = False
modo_travado = False

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640) 
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 60)  

# Performance tracking
fps_counter = 0
fps = 0
last_time = time.time()

# Smoothing
SMOOTHING_FACTOR = 0.4
movement_buffer = np.array([0, 0])

control_mode = "ANGRY_BIRDS" 


# Função para encontrar o estilingue e definir a âncora
def find_and_set_anchor():
    global anchor_pos
    print("Modo Angry Birds: Procurando estilingue...")
    try:
        location = pyautogui.locateCenterOnScreen(SLINGSHOT_IMAGE, confidence=CONFIDENCE_LEVEL)
        if location:
            slingshot_x, slingshot_y = location
            target_x = slingshot_x
            target_y = slingshot_y - PIXELS_ABOVE_SLINGSHOT
            anchor_pos = (target_x, target_y)
            pyautogui.moveTo(anchor_pos, duration=0.25, _pause=False)
            print(f"Âncora definida em {anchor_pos}")
        else:
            print("Estilingue não encontrado. Usando centro da tela como âncora.")
            anchor_pos = (screen_w // 2, screen_h // 2)
            pyautogui.moveTo(anchor_pos, duration=0.25, _pause=False)
    
    except pyautogui.ImageNotFoundException:
        print(f"ERRO: Arquivo '{SLINGSHOT_IMAGE}' não encontrado.")
        print("Usando centro da tela como âncora.")
        anchor_pos = (screen_w // 2, screen_h // 2)
        pyautogui.moveTo(anchor_pos, duration=0.25, _pause=False)
    except Exception as e:
        print(f"Erro ao procurar imagem: {e}")
        anchor_pos = None # Sem âncora


def get_finger_states(hand_landmarks):
    lm = hand_landmarks.landmark
    states = []
    states.append(lm[4].y < lm[3].y)
    tips = [8, 12, 16, 20]  
    pips = [6, 10, 14, 18]  
    
    for tip, pip in zip(tips, pips):
        states.append(lm[tip].y < lm[pip].y)
        
    return states

def is_signal_one(finger_states):
    return finger_states[1:] == [True, False, False, False]

def is_signal_peace(finger_states):
    return finger_states[1:] == [True, True, False, False]

def is_fist_closed(hand_landmarks):
    lm = hand_landmarks.landmark
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]

    closed_fingers = sum(
        1 for tip, pip in zip(tips, pips)
        if lm[tip].y > lm[pip].y
    )
    thumb_closed = abs(lm[4].x - lm[2].x) < 0.05
    
    return closed_fingers >= 3 and thumb_closed

# Chama a função uma vez no início se o modo padrão for Angry Birds
if control_mode == "ANGRY_BIRDS":
    find_and_set_anchor()

while cap.isOpened():
    # FPS counter
    fps_counter += 1
    if time.time() - last_time >= 1.0:
        fps = fps_counter
        fps_counter = 0
        last_time = time.time()
    
    ret, frame = cap.read()
    if not ret:
        continue
    
    frame = cv2.resize(frame, (640, 480))
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    results = hands.process(rgb)
    hand_detected = False

    
    if results.multi_hand_landmarks:
        hand_detected = True
        hand_landmarks = results.multi_hand_landmarks[0]
        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        wrist = hand_landmarks.landmark[0]
        
        finger_states = get_finger_states(hand_landmarks)

        # 1. Lógica de Troca de Modo (se não estiver travado)
        if not modo_travado:
            signal_one = is_signal_one(finger_states)
            signal_peace = is_signal_peace(finger_states)
            
            if signal_peace: # Mudar para FRUIT_NINJA
                if control_mode != "FRUIT_NINJA":
                    control_mode = "FRUIT_NINJA"
                    anchor_pos = None # Desativa âncora
                    if not mouse_down:
                        pyautogui.mouseDown(button='left