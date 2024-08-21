import cv2
import numpy as np
import threading
import time
import speech_recognition as sr
import serial
import queue
from dataclasses import dataclass, field

from modules.NLP.STT import record_and_transcribe
from modules.NLP.create_JSON import create_museum_json
from modules.NLP.retrieval_model import answer_question
from modules.NLP.TSS import speak
from modules.NLP.NLG import generate_ai_response
from nlp_wala import AI_Assistant

@dataclass
class GlobalState:
    frame: np.ndarray = None
    qr_detected: bool = False
    nlp: bool = False
    running: bool = True
    process_qr: bool = False
    detect_qr: bool = True
    qr_counterMartin: int = 0
    qr_counterTribhuvan: int = 0
    qr_endnTurn: int=0
    arduino: serial.Serial = None
    command_queue: queue.Queue = field(default_factory=queue.Queue)
    hello_detected: bool = False
    run_idle_video: bool = True

ai=AI_Assistant()
global_state = GlobalState()
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(3, 200)
cap.set(4, 200)

def send_wheel_command_thread():
    while global_state.running:
        try:
            move1, move2 = global_state.command_queue.get(timeout=1)
            command = f"MOVE {move1} {move2}\n"
            retries = 3
            for attempt in range(retries):
                try:
                    if global_state.arduino and global_state.arduino.is_open:
                        global_state.arduino.write(command.encode())

                        print(f"Command sent: {command.strip()}")
                        break
                except serial.SerialException as e:
                    print(f"Failed to send command: {e}. Retrying {attempt + 1}/{retries}")
            else:
                print("Failed to send command after retries")
        except queue.Empty:
            continue

def add_wheel_command(move1, move2):
    global_state.command_queue.put((move1, move2))

def arduino_connection_thread():
    while global_state.running:
        try:
            if not global_state.arduino or not global_state.arduino.is_open:
                global_state.arduino = serial.Serial('COM6', 115200, timeout=0.1)
                print("Arduino port opened")
        except serial.SerialException as e:
            print(f"Failed to open Arduino port: {e}")
        time.sleep(1)

def u_turn():
    add_wheel_command(6, 8)
    time.sleep(1.7)
    add_wheel_command(0,0)

def say_martin():
    speak("This sarangi, crafted around 100 years ago during Nepal's Rana era, is made from fine Nepali wood and showcases exquisite craftsmanship. Its intricately carved body, resonant with a parchment-covered resonator, produces a warm, emotive tone.")

def say_hitler():
    speak("hitler hitler hitler")

def say_trivuwan():
    speak("trivuwan trivuwan trivuwan")

def say_turning():
    print("turning function")
    # time.sleep(1)
    add_wheel_command(6, 8)
    time.sleep(1.7)
    add_wheel_command(-6,5)
    time.sleep(0.5)
    add_wheel_command(0,0)
    cap.release()
    cv2.destroyAllWindows()
    global_state.running = False



def findPath(hsv):
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([200, 255, 70])
    mask = cv2.inRange(hsv, lower_black, upper_black)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    mask = cv2.erode(mask, kernel, iterations=2)
    mask = cv2.dilate(mask, kernel, iterations=1)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    biggest = max(contours, key=cv2.contourArea, default=None)
    return biggest

def detect_lines(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    contour = findPath(hsv)
    mask = np.zeros_like(hsv[:, :, 0])
    if contour is not None:
        cv2.drawContours(mask, [contour], -1, 255, -1)
        mask = cv2.medianBlur(mask, 5)
    res = cv2.bitwise_and(image, image, mask=mask)
    copy = image.copy()
    if contour is not None:
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            cv2.line(image, (cx, 0), (cx, 720), (255, 0, 0), 1)
            cv2.line(image, (0, cy), (1280, cy), (255, 0, 0), 1)
            cv2.drawContours(copy, [contour], -1, (0, 255, 0), 1)
            if 120 < cx < 190:
                add_wheel_command(-6, 5)
            elif cx < 120:
                add_wheel_command(-4, 5)
            elif cx >= 190:
                add_wheel_command(-6, 4)   
            return image, copy, hsv, res, True
    return image, copy, hsv, res, False

def detect_qr_code(image):
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(image)
    if data:
        return data
    return None

def qr_detection_thread():
    while global_state.running:
        if global_state.frame is not None and not global_state.process_qr:
            qr_data = detect_qr_code(global_state.frame)
            if qr_data:
                global_state.qr_detected = True
                global_state.process_qr = True
                if qr_data == "tribhuwankoinfo":
                    global_state.qr_counterTribhuvan += 1
                    if global_state.qr_counterTribhuvan == 1:
                        time.sleep(1)
                        add_wheel_command(0, 0)
                        u_turn()
                    elif global_state.qr_counterTribhuvan == 2:
                        time.sleep(1)
                        add_wheel_command(0, 0)
                        u_turn()
                if qr_data == "endMaTurn":
                    global_state.qr_counterTribhuvan += 1
                    if global_state.qr_counterTribhuvan == 1:
                        # time.sleep(1)
                        print("suruko")
                        add_wheel_command(0, 0)
                        u_turn()
                        say_turning()   
                elif qr_data == "martinkoinfo":
                    global_state.qr_counterMartin += 1
                    if global_state.qr_counterMartin == 1:
                        time.sleep(0.5)
                        add_wheel_command(0, 0)
                        say_martin()
                        global_state.nlp = True
                        ai.run_chatbot()
                        handle_user_interaction()
                elif qr_data == "ending":
                    global_state.qr_endnTurn +=1
                    if global_state.qr_endnTurn==1:
                        print("turning")
                        # time.sleep(1)
                        add_wheel_command(0, 0)
                        say_turning()
                        u_turn()
                global_state.qr_detected = False
                global_state.process_qr = False
                global_state.nlp = False

def handle_user_interaction():
    global global_state
    while global_state.nlp:
        speak("Do you have any questions, Yes or No ?")
        continue_response = record_and_transcribe()
        print(f"User response to continue: {continue_response}")
        if continue_response and (continue_response.lower() == "no" or continue_response.lower() == "no no"):
            global_state.nlp = False
            break

        if continue_response is None:
            speak("I didn't quite get it. Please repeat.")
            continue
        retrieved_answer = answer_question(continue_response)
        prompt = f"Question: {continue_response}, context: {retrieved_answer}, based on context answer the question asked in humanly response"
        ai_response = generate_ai_response(prompt)
        speak(ai_response)

def camera_capture_thread():
    while global_state.running:
        ret, frame = cap.read()
        if not ret:
            break
        global_state.frame = frame
        if not global_state.process_qr and not global_state.nlp:
            cropped = frame[100:250, 80:]
            original, center, hsv, res, line_detected = detect_lines(frame)
            cv2.imshow('hsv', hsv)
            cv2.imshow('res', res)
            if center is not None:
                cv2.imshow('Detected Lines', center)
            if original is not None:
                cv2.imshow('Contours', original)
            if not line_detected:
                print("No line detected. Sending stop command.")
                add_wheel_command(0, 0)
        if cv2.waitKey(1) & 0xFF == ord('d'):
            global_state.running = False
            break

def idle_vid():
    vid = cv2.VideoCapture("./akha.mp4")
    if not vid.isOpened():
        print("Error: Video file not found or cannot be opened.")
        return

    fps = vid.get(cv2.CAP_PROP_FPS)
    delay = int(1000 / fps)

    cv2.namedWindow('Idle Video', cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty('Idle Video', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while global_state.run_idle_video:
        ret, frame = vid.read()

        if not ret:
            vid.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Restart video
            continue

        cv2.imshow('Idle Video', frame)

        if cv2.waitKey(delay) & 0xFF == ord('d'):
            break

    vid.release()
    cv2.destroyAllWindows()

def recognize_speech():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        print("Listening for command...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio)
            return command.lower()
        except (sr.UnknownValueError, sr.RequestError):
            return None

def nlp_in_between():
    while global_state.running:
        if not global_state.nlp:
            command = recognize_speech()
            if command == "nitro":
                print("Detected command 'nitro'")
                add_wheel_command(0,0)
                # global_state.nlp = True
                handle_user_interaction()

def start_threads(threads):
    for thread in threads:
        thread.start()

def join_threads(threads):
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    try:
        # Initial speech recognition for "hello"
        while not global_state.hello_detected:
            command = recognize_speech()
            if command and command.lower() == "hello":
                print("Hello detected, starting main function.")
                global_state.hello_detected = True
        create_museum_json()
        threads = [
            threading.Thread(target=qr_detection_thread),
            threading.Thread(target=camera_capture_thread),
            threading.Thread(target=send_wheel_command_thread),
            threading.Thread(target=nlp_in_between),
            threading.Thread(target=idle_vid)
        ]
        start_threads(threads)
        join_threads(threads)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        if global_state.arduino and global_state.arduino.is_open:
            global_state.arduino.close()
        print("Serial connection closed.")
