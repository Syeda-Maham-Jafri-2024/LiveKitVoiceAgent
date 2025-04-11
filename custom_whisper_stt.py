# custom_whisper_stt.py

import tempfile
import numpy as np
import soundfile as sf
import openai
import logging

class Capabilities:
    def __init__(self, streaming=False):
        self.streaming = streaming

class SimulatedStreamingWhisperSTT:
    def __init__(self, model="whisper-1", language="ur", detect_language=False):
        self.model = model
        self.language = language
        self.detect_language = detect_language
        self.capabilities = Capabilities(streaming=False)
        self._stt = None  # Ensure it's initially set to None

    def on(self, event_name, callback=None):
        """Handles events by accepting a callback, logging for debugging"""
        logging.info(f"Event received: {event_name}")
        if callback:
            logging.info(f"Callback received: {callback}")
        # Since we don't need the callback, just call it to avoid issues
        if callback:
            callback()

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmpfile:
            sf.write(tmpfile.name, audio_data, sample_rate)
            tmpfile.seek(0)
            transcript = openai.Audio.transcribe(
                model=self.model,
                file=tmpfile,
                language=self.language,
                response_format="text"
            )
        return transcript

    def set_stt(self, stt_object):
        """Method to set the STT object"""
        self._stt = stt_object
