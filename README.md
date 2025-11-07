# Controlador de Mouse por Gestos

Este é um script em Python que utiliza `OpenCV` para capturar a imagem da webcam e `MediaPipe` para detectar gestos com as mãos. Ele permite que você controle o cursor do mouse, simule cliques e alterne entre diferentes modos de controle, ideal para jogar ou para uma interação "sem as mãos".

## 🚀 Funcionalidades

* **Controle do Cursor:** Movimenta o mouse pela tela baseado na posição do seu pulso.
* **Suavização de Movimento:** Utiliza um buffer para evitar que o cursor trema com pequenos movimentos da mão.
* **Dois Modos de Operação:**
    1.  **Modo "Angry Birds"**: Controle o clique manualmente.
    2.  **Modo "Fruit Ninja"**: O clique é mantido pressionado o tempo todo.
* **Troca de Modo por Gestos:** Alterne entre os modos de forma intuitiva.
* **Feedback Visual:** A janela da câmera exibe o modo atual, o status do clique e o FPS.

## 📋 Requisitos

Você precisará de Python 3.x e das seguintes bibliotecas:

* `opencv-python`
* `mediapipe`
* `pyautogui`
* `numpy`

## ⚙️ Instalação

1.  Clone este repositório ou salve os arquivos (`.py` e `requirements.txt`) em um diretório local.

2.  (Opcional, mas recomendado) Crie e ative um ambiente virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  Instale as dependências a partir do arquivo `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

## ▶️ Como Usar

1.  Execute o script Python:
    ```bash
    python seu_script.py
    ```
    *(Substitua `seu_script.py` pelo nome real do seu arquivo)*

2.  Uma janela da sua webcam será aberta.

3.  Posicione sua mão (apenas uma) na frente da câmera.

4.  Use os gestos descritos abaixo para controlar o mouse.

5.  Pressione a tecla **'q'** (com o foco na janela da câmera) para fechar o programa.

## 🎮 Gestos de Controle

* **Movimento do Mouse**:
    * Mova seu **pulso** pela câmera. O cursor seguirá seus movimentos.

---

* **Modo "Angry Birds" (Padrão)**
    * **Ativação**: Faça o **sinal de 1** (☝️ - dedo indicador para cima, resto fechado).
    * **Ação**: Neste modo, o mouse está solto.
    * **Clique**: Feche a mão em um **punho fechado** (✊) para clicar e segurar (arrastar). Abra a mão para soltar o clique.

---

* **Modo "Fruit Ninja"**
    * **Ativação**: Faça o **sinal de paz** (✌️ - indicador e médio para cima, resto fechado).
    * **Ação**: Ao entrar neste modo, o mouse é **automaticamente clicado e mantido pressionado**.
    * **Clique**: Não é necessário (já está clicado). Mova o pulso para "cortar" pela tela.

---
