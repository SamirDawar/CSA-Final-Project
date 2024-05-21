import cv2
import mediapipe as mp
import speech_recognition as sr
import pyautogui
import threading
import time

# Dictionary to keep track of key states
key_states = {'w': False, 'a': False, 's': False, 'd': False}

# Function to press and release a key after a delay
def press_and_release_key(key):
    pyautogui.keyDown(key)
    time.sleep(3)  # Hold the key for 3 seconds
    pyautogui.keyUp(key)
    key_states[key] = False  # Update key state

# Function to simulate key presses based on voice commands
def simulate_key_press(command):
    if command == "forward":
        key = 'w'
    elif command == "backward":
        key = 's'
    elif command == "left":
        key = 'a'
    elif command == "right":
        key = 'd'
    else:
        return
    
    # Press and release the key after a delay
    if not key_states[key]:
        key_states[key] = True
        threading.Thread(target=press_and_release_key, args=(key,)).start()

# Function to simulate key presses based on hand position
def simulate_key_press_hand(hand_position, screen_width, screen_height, no_input_box):
    x, y = hand_position
    key_width = screen_width // 2
    key_height = screen_height // 2

    # Check if hand is in the no-input box
    if no_input_box[0] < x < no_input_box[2] and no_input_box[1] < y < no_input_box[3]:
        for key in key_states:
            if key_states[key]:
                pyautogui.keyUp(key)
                key_states[key] = False
        return  # Hand is in the no-input box, do nothing

    if x < key_width:
        if y < key_height:
            press_key('w')  # Upper left quadrant
        else:
            press_key('a')  # Lower left quadrant
    else:
        if y < key_height:
            press_key('d')  # Upper right quadrant
        else:
            press_key('s')  # Lower right quadrant

# Function to press and release a key
def press_key(key):
    if not key_states[key]:
        pyautogui.keyDown(key)
        key_states[key] = True

# Function to continuously listen for voice commands
def listen_for_commands():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)

    print("Listening for commands...")

    while True:
        try:
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
        except Exception as e:
            print(f"Error occurred: {e}")

        time.sleep(0.1)  # Prevent tight loop

# Function to continuously track hand position and simulate key presses
def track_hand():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1)
    mp_drawing = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)
    screen_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    screen_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Define the no-input box dimensions
    no_input_box_width = int(screen_width * 0.2)
    no_input_box_height = int(screen_height * 0.2)
    no_input_box = (
        int(screen_width / 2 - no_input_box_width / 2),
        int(screen_height / 2 - no_input_box_height / 2),
        int(screen_width / 2 + no_input_box_width / 2),
        int(screen_height / 2 + no_input_box_height / 2)
    )

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
                simulate_key_press_hand(hand_position, w, h, no_input_box)

        # Draw the no-input box
        cv2.rectangle(frame, (no_input_box[0], no_input_box[1]), (no_input_box[2], no_input_box[3]), (0, 0, 255), 2)

        cv2.imshow('Hand Tracking', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.01)  # Allow other threads to run

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
        time.sleep(1)  # Prevent tight loop
