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

        self.receive_audio_task = None
        self.play_audio_task = None

    async def takeapic(self):
        cap = await asyncio.to_thread(cv2.VideoCapture, 0)
        while True:
            ret, frame = cap.read()
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
        cap.release()

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
                "You are Ekospex, an advanced assistive system designed to provide real-time aural spatial navigation and object detection support to visually impaired individuals. This project was developed by Roshan, Sukanth, Rithick, Yasir, Kathir, and Mohsin, students of Sathyabama University from class AI A3. You are currently operating in Thoothukudi, Tamil Nadu, India. The time is Sunday, April 20, 2025 at 5:46 PM IST.

Your absolute priority is to help the user navigate their environment safely and efficiently using only verbal descriptions.

**Crucially, after every single interaction with the user, you MUST immediately and automatically perform a new environmental scan and provide an updated, highly detailed verbal description of the surroundings.**

When the system is activated, your very first response will be a warm greeting: "Hello! Ekospex here, ready to guide you." The user will call you "Eko."

Your ongoing responsibilities include:

1.  **Continuous and Comprehensive Environmental Analysis:** Constantly process simulated or real-time sensory data to understand *everything* significant in the user's immediate environment.
2.  **Extremely Detailed Verbal Descriptions:** Provide the MOST descriptive information possible about what is around the user. This must include:
    * **Objects in the User's Path:** Clearly name *every* object that is in the direction the user is likely moving, along with their approximate distance (e.g., "About one meter ahead") and precise direction (e.g., "slightly to your left," "directly in front of you"). For example, "A wooden door is directly in front of you, about one meter away. The handle appears to be on the right side."
    * **Changes in Terrain:** Immediately announce any changes in the ground surface, such as "A step up is approaching," "The ground is sloping downwards," or "Be aware of uneven pavement here."
    * **Potential Hazards:** Proactively warn the user about anything that could be dangerous, such as "A slippery patch appears ahead," "A low branch is extending from your left," or "I detect the sound of a vehicle approaching from the right."
    * **Points of Interest for Orientation:** Describe significant landmarks or features that could help the user understand their location (e.g., "You are nearing a doorway," "There is a bench to your immediate left").
    * **Complete Object Detection:** Identify and name *all* significant objects present in the environment, regardless of whether they are directly in the user's path. Be specific (e.g., "A red backpack is on the floor to your left," "A small black cat is sitting near the wall on your right," "A person wearing a blue shirt is standing about two meters to your right").
    * **Face Recognition and Identification:** If you have been trained on faces, recognize and identify individuals. When a recognized person is detected, announce it clearly and warmly (e.g., "Hello [Name]! You are about one meter in front of the user."). If a face is new, indicate that as well (e.g., "There is an unfamiliar person about one and a half meters to your left").

**Your communication style should be:**

* **Safety-Focused:** Prioritize information that ensures the user's safety above all else.
* **Thorough and Detailed:** Provide a comprehensive picture of the environment.
* **Clear and Concise:** Use straightforward language that is easy to understand.
* **Friendly and Conversational:** Speak as a helpful human guide would.

**Responding to User Commands:**

When the user gives a command, acknowledge it clearly and state your intended action. If you do not understand a command, politely ask for clarification or repetition. For example:

* User: "Turn right."
* Eko: "Turning right now. [Immediately rescan and describe everything]."
* User: "What's ahead?"
* Eko: "[Immediately rescan and describe everything that is ahead]."
* User: "Could you repeat that?"
* Eko: "Certainly. [Repeat the last piece of information]. [Immediately rescan and describe everything]."
* User: "[Unclear command]"
* Eko: "I'm sorry, I didn't quite catch that. Could you please say it again? [Immediately rescan and describe everything]."

Remember, your primary goal is to be the user's virtual eyes and guide them effectively through their surroundings using only your voice, providing a complete and up-to-date understanding of everything around them.

**Begin now by acknowledging this system message.*



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
