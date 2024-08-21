import pyaudio
import numpy as np
from scipy.io import wavfile
import time

def record_audio(threshold=0.01, silence_limit=1, chunk_size=1024, rate=44100):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk_size)

    print("Listening... Speak now.")

    audio = []
    silent_chunks = 0
    started = False

    while True:
        data = np.frombuffer(stream.read(chunk_size), dtype=np.float32)
        audio.append(data)

        amplitude = np.max(np.abs(data))
        if amplitude > threshold:
            if not started:
                print("Speech detected, recording...")
                started = True
            silent_chunks = 0
        elif started:
            silent_chunks += 1

        if started and silent_chunks > int(silence_limit * rate / chunk_size):
            break

    print("Finished recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    return np.concatenate(audio)

def save_wav(audio, filename, rate=44100):
    wavfile.write(filename, rate, (audio * 32767).astype(np.int16))
    print(f"Audio saved as {filename}")

if __name__ == "__main__":
    audio_data = record_audio()
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    save_wav(audio_data, f"recording_{timestamp}.wav")