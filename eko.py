import asyncio
import base64
import io
import os
import sys
import traceback

import cv2
import pyaudio
import PIL.Image
from dotenv import load_dotenv
load_dotenv()

from google import genai
API_KEY = os.getenv("GOOGLE_API_KEY")
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024
CONFIG = {"response_modalities": ["AUDIO"]}
MODEL = "models/gemini-2.0-flash-exp"

client = genai.Client(api_key=API_KEY, http_options={"api_version": "v1alpha"})
pya = pyaudio.PyAudio()

class AudioLoop:
    def __init__(self):
        self.from_model_q = None
        self.to_model_q = None
        self.session = None
        self.audio_stream = None
        self.video_cap = None
        self.output_stream = None

    async def takeapic(self):
        self.video_cap = await asyncio.to_thread(cv2.VideoCapture, 0)
        try:
            while True:
                ret, frame = self.video_cap.read()
                if not ret:
                    break
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = PIL.Image.fromarray(frame_rgb)
                img.thumbnail([1024, 1024])

                image_io = io.BytesIO()
                img.save(image_io, format="jpeg")
                image_io.seek(0)
                image_bytes = image_io.read()
                obj = {"mime_type": "image/jpeg", "data": base64.b64encode(image_bytes).decode()}

                await self.to_model_q.put(obj)
                await asyncio.sleep(1.0)
        finally:
            if self.video_cap:
                self.video_cap.release()

    async def send_data(self):
        while True:
            msg = await self.to_model_q.get()
            await self.session.send(input=msg)

    async def listen_audio(self):
        mic_info = pya.get_default_input_device_info()
        self.audio_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        try:
            while True:
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, exception_on_overflow=False)
                await self.to_model_q.put({"data": data, "mime_type": "audio/pcm"})
        finally:
            if self.audio_stream:
                self.audio_stream.close()

    async def receive_audio(self):
        while True:
            turn = self.session.receive()
            async for response in turn:
                if data := response.data:
                    if self.from_model_q:
                        await self.from_model_q.put(data)
                    continue
                if text := response.text:
                    print(text, end="")

    async def play_audio(self):
        self.output_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        try:
            while True:
                bytestream = await self.from_model_q.get()
                await asyncio.to_thread(self.output_stream.write, bytestream)
        finally:
            if self.output_stream:
                self.output_stream.close()

    async def cleanup(self):
        if self.audio_stream:
            self.audio_stream.close()
        if self.video_cap:
            self.video_cap.release()
        if self.output_stream:
            self.output_stream.close()

    async def main(self):
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session

                with open('system_message.txt', 'r') as f:
                    system_message = f.read()

                await self.session.send(input=system_message, end_of_turn=True)
                self.from_model_q = asyncio.Queue()
                self.to_model_q = asyncio.Queue(maxsize=5)

                tg.create_task(self.send_data())
                tg.create_task(self.listen_audio())
                tg.create_task(self.takeapic())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                await asyncio.Future()

        except asyncio.CancelledError:
            await self.cleanup()
        except ExceptionGroup as EG:
            await self.cleanup()
            traceback.print_exception(EG)
        except Exception as e:
            await self.cleanup()
            traceback.print_exception(e)

if __name__ == "__main__":
    asyncio.run(AudioLoop().main())
