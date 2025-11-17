import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import sys

# --- Configurações Críticas ---
SLINGSHOT_IMAGE = 'slingshot.png'
PIXELS_ABOVE_SLINGSHOT = 120
CONFIDENCE_LEVEL = 0.8
DELAY_ON_RELEASE = 0.2
anchor_pos = None

# --- Inicialização do MediaPipe e Câmera ---
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

# --- Variáveis de Performance e Estado ---
fps_counter, fps, last_time = 0, 0, time.time()
SMOOTHING_FACTOR = 0.4
movement_buffer = np.array([0, 0])
control_mode = "ANGRY_BIRDS" 
last_mode_switch_time = time.time()
MODE_SWITCH_COOLDOWN = 1         # Cooldown de troca de modo


def find_and_set_anchor():
    """
    Procura a imagem do estilingue na tela e define a 'anchor_pos'
    (posição inicial do mouse) acima dela.
    Se não encontrar, usa o centro da tela.
    """
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
            print("Estilingue não encontrado. Usando centro da tela.")
            anchor_pos = (screen_w // 2, screen_h // 2)
            pyautogui.moveTo(anchor_pos, duration=0.25, _pause=False)
    
    except Exception as e:
        print(f"Erro ao procurar imagem '{SLINGSHOT_IMAGE}': {e}")
        anchor_pos = (screen_w // 2, screen_h // 2) # Padrão em caso de erro
        pyautogui.moveTo(anchor_pos, duration=0.25, _pause=False)


def get_finger_states(hand_landmarks):
    """
    Analisa os landmarks e retorna uma lista de 5 booleanos
    indicando se cada dedo está esticado [Polegar, Indicador, Médio, Anelar, Mínimo].
    """
    lm = hand_landmarks.landmark
    states = []
    # Lógica do Polegar
    states.append(lm[4].y < lm[3].y)
    # Lógica dos outros 4 dedos (ponta vs. junta do meio)
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    for tip, pip in zip(tips, pips):
        states.append(lm[tip].y < lm[pip].y)
    return states

def is_signal_one(finger_states):
    """Verifica se o gesto é 'um' (só o indicador)."""
    return finger_states[1:] == [True, False, False, False]

def is_signal_peace(finger_states):
    """Verifica se o gesto é 'paz' (indicador e médio)."""
    return finger_states[1:] == [True, True, False, False]

def is_signal_three_fingers(finger_states):
    """Verifica se o gesto é 'três' (indicador, médio, anelar)."""
    return finger_states[1:] == [True, True, True, False]

def is_fist_closed(hand_landmarks):
    """Verifica se a mão está com o punho fechado."""
    lm = hand_landmarks.landmark
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    # Conta dedos dobrados (ponta abaixo da junta)
    closed_fingers = sum(1 for tip, pip in zip(tips, pips) if lm[tip].y > lm[pip].y)
    # Verifica polegar cruzado
    thumb_closed = abs(lm[4].x - lm[2].x) < 0.05
    return closed_fingers >= 3 and thumb_closed

# --- Início do Programa ---
if control_mode == "ANGRY_BIRDS":
    find_and_set_anchor() # Procura a âncora ao iniciar

# --- Loop Principal ---
while cap.isOpened():
    # Cálculo de FPS
    fps_counter += 1
    if time.time() - last_time >= 1.0:
        fps = fps_counter
        fps_counter = 0
        last_time = time.time()
    
    # Leitura e Processamento Básico da Imagem
    ret, frame = cap.read()
    if not ret: continue
    frame = cv2.resize(frame, (640, 480))
    frame = cv2.flip(frame, 1) # Espelha a imagem
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Detecção do MediaPipe
    results = hands.process(rgb)
    hand_detected = False
    
    # --- Bloco Crítico: Lógica de Detecção da Mão ---
    if results.multi_hand_landmarks:
        hand_detected = True
        hand_landmarks = results.multi_hand_landmarks[0]
        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        
        wrist = hand_landmarks.landmark[0]
        finger_states = get_finger_states(hand_landmarks)

        # === 1. Lógica de Troca de Modo (só se 'L' não foi pressionada) ===
        if not modo_travado:
            signal_one = is_signal_one(finger_states)
            signal_peace = is_signal_peace(finger_states)
            signal_three = is_signal_three_fingers(finger_states) 
            
            if signal_peace and control_mode != "FRUIT_NINJA":
                control_mode = "FRUIT_NINJA"
                last_mode_switch_time = time.time() # NOVO: Atualiza o tempo
                anchor_pos = None
                if not mouse_down:
                    pyautogui.mouseDown(button='left', _pause=False)
                    mouse_down = True
                    
            elif signal_one and control_mode != "ANGRY_BIRDS":
                control_mode = "ANGRY_BIRDS"
                last_mode_switch_time = time.time() # NOVO: Atualiza o tempo
                if mouse_down:
                    pyautogui.mouseUp(button='left', _pause=False)
                    mouse_down = False
                find_and_set_anchor() # Reposiciona na âncora
                if 'last_wrist_x' in globals(): del last_wrist_x
            
            elif signal_three and control_mode != "MOUSE_LIVRE": 
                control_mode = "MOUSE_LIVRE"
                last_mode_switch_time = time.time() # NOVO: Atualiza o tempo
                anchor_pos = None 
                if mouse_down: 
                    pyautogui.mouseUp(button='left', _pause=False)
                    mouse_down = False
                if 'last_wrist_x' in globals(): del last_wrist_x

        # === 2. Lógica de Ação (baseado no modo ativo) ===
        should_move_mouse = False # Define se o mouse pode se mover
        
        # NOVO: Verifica se o cooldown já passou
        ready_for_action = (time.time() - last_mode_switch_time > MODE_SWITCH_COOLDOWN)
        
        if control_mode == "FRUIT_NINJA":
            should_move_mouse = True
            if not mouse_down: # Garante clique contínuo
                pyautogui.mouseDown(button='left', _pause=False)
                mouse_down = True
        
        elif control_mode == "ANGRY_BIRDS":
            fist = is_fist_closed(hand_landmarks)
            
            # ALTERADO: Só clica se o punho estiver fechado E o cooldown tiver passado
            if fist and ready_for_action:
                # "PUXANDO": Punho fechado -> clica e permite movimento
                should_move_mouse = True
                if not mouse_down:
                    pyautogui.mouseDown(button='left', _pause=False)
                    mouse_down = True
            else: 
                # "SOLTANDO" ou "EM COOLDOWN":
                should_move_mouse = False
                if mouse_down: # Se estava clicando, solta (lógica normal de "soltar")
                    pyautogui.mouseUp(button='left', _pause=False)
                    time.sleep(DELAY_ON_RELEASE) # Delay crítico
                    mouse_down = False
                    if anchor_pos:
                        pyautogui.moveTo(anchor_pos, _pause=False) # Retorna à âncora
                    if 'last_wrist_x' in globals(): del last_wrist_x
        
        elif control_mode == "MOUSE_LIVRE": 
            should_move_mouse = True # Move o mouse livremente
            fist = is_fist_closed(hand_landmarks)
            
            # ALTERADO: Só clica se o cooldown tiver passado
            if fist and ready_for_action: 
                if not mouse_down:
                    pyautogui.mouseDown(button='left', _pause=False)
                    mouse_down = True
            else: # Solta ao abrir a mão ou se estiver em cooldown
                if mouse_down:
                    pyautogui.mouseUp(button='left', _pause=False)
                    mouse_down = False

        # === 3. Execução do Movimento (só se permitido) ===
        if should_move_mouse:
            if 'last_wrist_x' in globals():
                # Cálculo do movimento (delta) + suavização
                dx = (wrist.x - last_wrist_x) * screen_w * 1.5
                dy = (wrist.y - last_wrist_y) * screen_h * 1.5
                movement_buffer = movement_buffer * SMOOTHING_FACTOR + np.array([dx, dy]) * (1 - SMOOTHING_FACTOR)
                
                current_x, current_y = pyautogui.position()
                new_x = np.clip(current_x + int(movement_buffer[0]), 0, screen_w-1)
                new_y = np.clip(current_y + int(movement_buffer[1]), 0, screen_h-1)
                
                pyautogui.moveTo(new_x, new_y, _pause=False)

            last_wrist_x, last_wrist_y = wrist.x, wrist.y # Salva a posição para o próximo frame
    
    
    # --- Bloco Crítico: Segurança (Mão Perdida) ---
    if not hand_detected:
        if mouse_down: # Se a mão sumir, solta o clique
            pyautogui.mouseUp(button='left', _pause=False)
            
            # Só retorna à âncora se estiver no modo Angry Birds
            if control_mode == "ANGRY_BIRDS":
                time.sleep(DELAY_ON_RELEASE) 
                if anchor_pos:
                    pyautogui.moveTo(anchor_pos, _pause=False) # Retorna à âncora
            
            mouse_down = False
        if 'last_wrist_x' in globals(): del last_wrist_x # Reseta o cálculo de movimento

    # --- Bloco de UI: Desenha status na tela ---
    status_text = f"Modo: {control_mode}"
    color = (0, 255, 0)
    
    # NOVO: Verifica o cooldown para a UI também
    ready_for_action = (time.time() - last_mode_switch_time > MODE_SWITCH_COOLDOWN)
    
    if control_mode == "FRUIT_NINJA":
        status_text += " (SLICING!)"; color = (0, 0, 255)
    
    elif control_mode == "ANGRY_BIRDS":
        color = (0, 255, 255)
        if anchor_pos: # Desenha a âncora na janela
             anchor_frame_x = int(anchor_pos[0] / screen_w * 640)
             anchor_frame_y = int(anchor_pos[1] / screen_h * 480)
             cv2.circle(frame, (anchor_frame_x, anchor_frame_y), 10, (255,0,255), 3)
        
        # ALTERADO: Mostra "COOLDOWN" na tela
        if not ready_for_action:
            status_text += " (COOLDOWN)"
            color = (128, 128, 128) # Cinza
        elif mouse_down: 
            status_text += " (PUXANDO)"
            color = (0, 165, 255)
        else:
            status_text += " (NA ANCORA)"
    
    elif control_mode == "MOUSE_LIVRE":
        color = (0, 255, 0)
        
        # ALTERADO: Mostra "COOLDOWN" na tela
        if not ready_for_action:
            status_text += " (COOLDOWN)"
            color = (128, 128, 128) # Cinza
        elif mouse_down:
            status_text += " (CLICANDO)"
            color = (0, 165, 255)
        else:
            status_text += " (LIVRE)"
    
    lock_text = " (TRAVADO)" if modo_travado else " (LIVRE)"
    lock_color = (0, 0, 255) if modo_travado else (0, 255, 0)

    cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, lock_text, (500, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, lock_color, 2)
    cv2.putText(frame, f"FPS: {fps}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    # --- Mostrar Janela e Ler Teclas ---
    cv2.imshow('Hand Mouse Controller', frame)
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'): # 'q' para Sair
        if mouse_down: pyautogui.mouseUp(button='left', _pause=False)
        break
    elif key == ord('l'): # 'l' para Travar/Destravar a troca de modo
        modo_travado = not modo_travado
        time.sleep(0.1) 

# --- Encerramento ---
cap.release()
cv2.destroyAllWindows()
print("Script encerrado.")