import speech_recognition as sr
import ollama
import pyaudio
from piper import PiperVoice
import os

#os.system('spd-say "Hello, I am ready."')

##command_prefix = "spd-say "
##command_endfix = "Respond as BMO would from Adventure time"

# Find the voice next to THIS file, so it works no matter which folder the terminal is in.
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "voices_bmo", "en_US-bmo_voice.onnx")  # en_US-bmo_voice.onnx.json must sit next to it
MIC_INDEX = 0   # FIX 1: this was never created. Change 0 to your mic's number from the printed list.
COMMAND_ENDFIX = " Respond strictly as BMO from Adventure Time. Keep answers short, upbeat, and childlike."

r = sr.Recognizer()
p = pyaudio.PyAudio()

# get_device_count() = how many audio devices (mics + speakers) the computer has.
# This loop prints only the ones that can record (input channels > 0).
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    if dev['maxInputChannels'] > 0:
        print(f"Device Index {i}: {dev['name']}")

print("loading BMO voice model...")
voice = PiperVoice.load(MODEL_PATH)


def speak(text):
    stream = None
    for chunk in voice.synthesize(text):
        if stream is None:
            # Open the speakers once, using the sound format of the first chunk.
            stream = p.open(format=p.get_format_from_width(chunk.sample_width),
                            channels=chunk.sample_channels,
                            rate=chunk.sample_rate,
                            output=True)
        stream.write(chunk.audio_int16_bytes)
    if stream is not None:
        stream.stop_stream()
        stream.close()


speak("Hello! BMO is ready!")

while True:
    try:
        # Only the listening part needs the microphone open.
        with sr.Microphone(device_index=MIC_INDEX) as source:
            print(f"Listening on mic {MIC_INDEX}...")
            r.adjust_for_ambient_noise(source, duration=0.2)
            audio = r.listen(source, 10, 15)

        text = r.recognize_google(audio)
        text = text.lower()
        print("You said:", text)
        
        if "exit" in text:
            speak("Bye bye!")
            print("Exiting program...")
            break

        result = ollama.generate(model="llama3", prompt=text + COMMAND_ENDFIX)
        response = result['response']   # FIX 7: no extra quote marks (Piper would read them)
        print("BMO:", response)

        speak(response)

    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))

    except sr.UnknownValueError:
        print("Could not understand audio")

    except KeyboardInterrupt:
        print("Program terminated by user")
        break

    except sr.WaitTimeoutError:

        print("(Heard nothing for 10 seconds - if you WERE talking, try a different MIC_INDEX)")
        continue

p.terminate()
