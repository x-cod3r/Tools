from kittentts import KittenTTS
import soundfile as sf

# Initialize the TTS model
tts_model = KittenTTS()

# Get available voices
print(tts_model.available_voices)

# Synthesize speech and save to file
# Using the first available voice as an example
tts_model.generate_to_file("Hello, My name is Mahmoud and I can do nice things ", "kitten.wav", voice=tts_model.available_voices[0])
