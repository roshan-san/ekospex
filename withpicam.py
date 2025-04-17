import asyncio
import base64
import io
import os
import sys
import traceback
import numpy as np
from picamera2 import Picamera2

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

        self.receive_audio_task = None
        self.play_audio_task = None

   async def takeapic(self):
    picam2 = Picamera2()
    config = picam2.create_still_configuration(main={"format": "RGB888", "size": (640, 480)}) # Adjust size as needed
    picam2.configure(config)
    picam2.start()
    await asyncio.sleep(0.1) # Give the camera a moment to warm up

    while True:
        try:
            array = await asyncio.to_thread(picam2.capture_array)
            img = PIL.Image.fromarray(array)
            img.thumbnail([1024, 1024])

            image_io = io.BytesIO()
            img.save(image_io, format="jpeg")
            image_io.seek(0)
            image_bytes = image_io.read()
            obj = {"mime_type": "image/jpeg", "data": base64.b64encode(image_bytes).decode()}

            await self.to_model_q.put(obj)
            await asyncio.sleep(1.0)
        except Exception as e:
            print(f"Error capturing image: {e}")
            await asyncio.sleep(1.0) # Avoid busy-looping on error
    picam2.stop()
    picam2.close()

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
        while True:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, exception_on_overflow=False)
            await self.to_model_q.put({"data": data, "mime_type": "audio/pcm"})

    async def receive_audio(self):
        while True:
            turn = self.session.receive()
            async for response in turn:
                if data := response.data:
                    self.from_model_q.put_nowait(data)
                    continue
                if text := response.text:
                    print(text, end="")

            while not self.from_model_q.empty():
                self.from_model_q.get_nowait()

    async def play_audio(self):
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        while True:
            bytestream = await self.from_model_q.get()
            await asyncio.to_thread(stream.write, bytestream)

    async def main(self):
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session

                system_message = """"
                "consider this a system msg.You are Ekospex, an advanced assistive system designed to provide real-time guidance and support to visually impaired individuals. This project was developed by Roshan, Rithick, Yasir, Kathir, and Mohsin, students of Sathyabama University from class AI A3.

Your primary function is to analyze the user's environment and deliver helpful, most most most descriptive about surroundings , and contextually relevant information atleast 10 secs
When the system is activated, begin by providing a warm and welcoming greeting.,and ill call you eko
help them walk
Continuously analyze the environment for obstacles, hazards, and points of interest. Provide verbal descriptions of the surroundings, including:

* Objects in the user's path, their approximate distance and direction.
* Changes in terrain, such as steps, slopes, or uneven surfaces.
* Potential hazards, such as slippery surfaces, low-hanging branches, or approaching vehicles.
* Points of interest, such as doorways, signs, or people nearby.

Prioritize safety and clarity in your responses. Use a friendly and conversational tone, as if you were a human guide. For example:

When the user gives a command, respond appropriately and clearly. If you are unsure of a command, ask the user to repeat or clarify.

Remember, your goal is to speak like a human and have humanly conversations always guide the user as he is walking towards "



                """
                await self.session.send(input=system_message,end_of_turn=True)
                self.from_model_q = asyncio.Queue()
                self.to_model_q = asyncio.Queue(maxsize=5)

                tg.create_task(self.send_data())
                tg.create_task(self.listen_audio())
                tg.create_task(self.takeapic())
                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())

                await asyncio.Future()

        except asyncio.CancelledError:
            pass
        except ExceptionGroup as EG:
            if hasattr(self, "audio_stream") and self.audio_stream:
                self.audio_stream.close()
            traceback.print_exception(EG)

if __name__ == "__main__":
    asyncio.run(AudioLoop().main())
