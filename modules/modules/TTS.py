# import pyttsx3

# # Initialize the TTS engine
# speaker = pyttsx3.init()

# # Set properties (optional)
# speaker.setProperty('rate', 120)  # Speed of speech (words per minute)
# speaker.setProperty('volume', 0.6)  # Volume (0.0 to 1.0)

# def speak(text):
#     # Convert text to speech and play it
#     speaker.say(text)
#     # Wait for the speech to finish
#     speaker.runAndWait()
import pyttsx3

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    try:
        engine.runAndWait()
    except RuntimeError:
        print("Run loop already started")


