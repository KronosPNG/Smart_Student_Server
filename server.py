from flask import Flask, request, jsonify, Response
from student import Student, Personality, Intelligence
from celery.result import AsyncResult
import random
import json
import tempfile
import whisper

from modules.openAI_TTS_Manager import OpenAI_TTS_Manager
from modules.chatGPT_Manager import ChatGPT_Manager
from tasks import transcribe_audio, generate_audio, generate_text


app = Flask(__name__)

student = None
model = None
already_started = False
can_ask_question = True
OpenAI_Key = None
ElevLabs_Key = None

ALLOWED_FORMATS = [
    "m4a",
    "mp3",
    "webm",
    "mp4",
    "mpga",
    "wav",
    "mpeg",
]

with app.app_context():
    print("Loading the model.")
    model = whisper.load_model("small")

    with open('configs/API_key.json') as config_file:
        data = json.load(config_file)

    # OpenAI API key
    OpenAI_Key = data['OpenAI']
    ElevLabs_Key = data['ElevenLabs']

@app.route("/test", methods=["POST"])
def test():
    req = request.get_json()

    print("------TEST------")
    print(req)
    print("----------------")

    return jsonify(req)

@app.route("/generate_question", methods=["POST"])
def generate_question():
    global can_ask_question
    # student = Student(Personality.CONFIDENT, Intelligence.HIGH, "Fantasy", ChatGPT_Manager(OpenAI_Key), ElevenLabsTTS_Manager(ElevLabs_Key))

    if not already_started:
        return jsonify({"error": "Studente non ancora creato!"})

    can_ask_question = True

    print("[Request] Received data")
    audio_data = request.get_data()

    audio_format = request.headers.get('Content-Type')

    if audio_format.replace("audio/", "") not in ALLOWED_FORMATS:
        return jsonify({"error": "Formato audio non supportato"})

    with tempfile.NamedTemporaryFile('wb+', delete=False) as temp:
        temp.write(audio_data)
        temp.seek(0)
    
    print("[Whisper] Transcribing audio")
    transcription = model.transcribe(temp.name)

    print("Transcription: ", transcription["text"])

    print("[Chat Completions] Generating response")
    # reply = student.generate_response(transcription["text"])

    print("[Text-to-Speech] Generating audio")
    # response = Response(student.generate_audio(reply, play_audio=False, format="pcm"), status=200, mimetype='audio/wav')

    response = Response(audio_data, status=200, mimetype='audio/wav')

    print("[Response] Sending response")
    return response

@app.route("/start", methods=["POST"])
def start():
    global student
    global already_started

    # if already_started:
    #     return jsonify({"error": "Studente gia' creato!"})

    already_started = True

    req = request.get_json()

    subject = req["subject"]

    # Create a student with random personality, intelligence and voice
    # random_personality = random.choice(list(Personality))
    # random_intelligence = random.choice(list(Intelligence))
    random_personality = Personality.CONFIDENT
    random_intelligence = Intelligence.HIGH
    voice = random.choice(OpenAI_TTS_Manager.VOICES_ITA)

    tts_model = OpenAI_TTS_Manager(OpenAI_Key, voice=voice)
    completions_model = ChatGPT_Manager(OpenAI_Key)

    student = Student(random_personality, random_intelligence, subject, completions_model, tts_model)

    return jsonify({"message": "Studente creato con successo"})

@app.get("/result/<id>")
def task_result(id: str) -> dict[str, object]:
    result = AsyncResult(id)

    return {
        "ready": result.ready(),
        "successful": result.successful(),
        "value": result.result if result.ready() else None,
    }

if __name__ == "__main__":
    print("Smart student pronto all'uso\n[In ascolto sulla porta 5000]")
    app.run(port = 5000)
            