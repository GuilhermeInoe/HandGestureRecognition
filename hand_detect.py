import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

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
    tips = [8, 12, 16, 20]  # Fingertip landmarks
    pips = [6, 10, 14, 18]  # PIP joints

    closed_fingers = sum(
        1 for tip, pip in zip(tips, pips)
        if lm[tip].y > lm[pip].y
    )
    thumb_closed = abs(lm[4].x - lm[2].x) < 0.05
    
    return closed_fingers >= 3 and thumb_closed

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
        
        if 'last_wrist_x' in globals():
            dx = (wrist.x - last_wrist_x) * screen_w * 1.5
            dy = (wrist.y - last_wrist_y) * screen_h * 1.5
            last_wrist_x, last_wrist_y = wrist.x, wrist.y
            
            movement_buffer = movement_buffer * SMOOTHING_FACTOR + np.array([dx, dy]) * (1 - SMOOTHING_FACTOR)
            
            current_x, current_y = pyautogui.position()
            new_x = np.clip(current_x + int(movement_buffer[0]), 0, screen_w-1)
            new_y = np.clip(current_y + int(movement_buffer[1]), 0, screen_h-1)
            pyautogui.moveTo(new_x, new_y, _pause=False)
        else:
            last_wrist_x, last_wrist_y = wrist.x, wrist.y
    
        finger_states = get_finger_states(hand_landmarks)

        signal_one = is_signal_one(finger_states)
        signal_peace = is_signal_peace(finger_states)
        if signal_peace:
            if control_mode != "FRUIT_NINJA":
                control_mode = "FRUIT_NINJA"
                if not mouse_down:
                    pyautogui.mouseDown(button='left', _pause=False)
                    mouse_down = True
                
        elif signal_one:
            if control_mode != "ANGRY_BIRDS":
                control_mode = "ANGRY_BIRDS"
                if mouse_down:
                    pyautogui.mouseUp(button='left', _pause=False)
                    mouse_down = False

        elif control_mode == "ANGRY_BIRDS":
            
            fist = is_fist_closed(hand_landmarks)
            
            if fist:
                if not mouse_down:
                    pyautogui.mouseDown(button='left', _pause=False)
                    mouse_down = True
            elif mouse_down:
                pyautogui.mouseUp(button='left', _pause=False)
                mouse_down = False
                
        elif control_mode == "FRUIT_NINJA":
            if not mouse_down:
                pyautogui.mouseDown(button='left', _pause=False)
                mouse_down = True
    
    # se nao pegar a mao
    if not hand_detected:
        if mouse_down:
            pyautogui.mouseUp(button='left', _pause=False)
            mouse_down = False
        if 'last_wrist_x' in globals():
            del last_wrist_x, last_wrist_y

    status_text = f"Modo: {control_mode}"
    color = (0, 255, 0) # Verde

    if control_mode == "FRUIT_NINJA":
        status_text += " (SLICING!)"
        color = (0, 0, 255) # Vermelho
    elif control_mode == "ANGRY_BIRDS":
        color = (0, 255, 255) # Amarelo
        if mouse_down: 
            status_text += " (CLICKING)"
            color = (0, 165, 255) # Laranja
    
    cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, f"FPS: {fps}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    cv2.imshow('Hand Mouse Controller', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        if mouse_down: pyautogui.mouseUp(button='left', _pause=False)
        break

cap.release()
cv2.destroyAllWindows()