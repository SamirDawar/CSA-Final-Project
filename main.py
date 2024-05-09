import cv2
import mediapipe as mp
import speech_recognition as sr
import pyautogui
import threading

# Function to simulate key presses based on voice commands
def simulate_key_press(command):
    if command == "forward":
        pyautogui.press('w')
    elif command == "backward":
        pyautogui.press('s')
    elif command == "left":
        pyautogui.press('a')
    elif command == "right":
        pyautogui.press('d')
    # Add more commands as needed

# Function to simulate key presses based on hand position
def simulate_key_press_hand(hand_position, screen_width, screen_height):
    x, y = hand_position
    key_width = screen_width // 2
    key_height = screen_height // 2

    if x < key_width:
        if y < key_height:
            pyautogui.press('w')  # Upper left quadrant
        else:
            pyautogui.press('a')  # Lower left quadrant
    else:
        if y < key_height:
            pyautogui.press('d')  # Upper right quadrant
        else:
            pyautogui.press('s')  # Lower right quadrant

# Function to continuously listen for voice commands
def listen_for_commands():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)

    print("Listening for commands...")

    while True:
        with microphone as source:
            audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio).lower()
            print("Recognized command:", command)
            simulate_key_press(command)
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print("Could not request results; {0}".format(e))

# Function to continuously track hand position and simulate key presses
def track_hand():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1)
    mp_drawing = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)  # Flip horizontally for a mirror effect
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Extract the hand position (normalized to [0, 1])
                x = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x
                y = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y

                # Convert the normalized position to pixel coordinates
                h, w, _ = frame.shape
                hand_position = (int(x * w), int(y * h))

                # Draw a circle at the hand position for visualization
                cv2.circle(frame, hand_position, 10, (0, 255, 0), -1)

                # Simulate key press based on hand position
                simulate_key_press_hand(hand_position, w, h)

        cv2.imshow('Hand Tracking', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Start a new thread for listening to voice commands
    command_listener_thread = threading.Thread(target=listen_for_commands)
    command_listener_thread.daemon = True
    command_listener_thread.start()

    # Start a new thread for tracking hand position
    hand_tracking_thread = threading.Thread(target=track_hand)
    hand_tracking_thread.daemon = True
    hand_tracking_thread.start()

    # Main thread continues to execute other tasks or waits for termination
    while True:
        pass
