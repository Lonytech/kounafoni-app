from flask import Flask, redirect, render_template, url_for, request

app = Flask(__name__)

# Dummy audio data
audio_files = [
    {
        "name": "Audio 1",
        "duration": "3:45",
        "file": "Le 20heures de ORTM1 du 13 mai 2024..wav",
    },
    {
        "name": "Audio 2",
        "duration": "2:30",
        "file": "🔴 Direct | JT 20H de ORTM1 du 24 mai 2024.wav",
    },
    {"name": "Audio 3", "duration": "4:15", "file": "audio3.mp3"},
]

audios = [
    {"date": "2024-05-14", "media": "ORTM", "duration": "3:45", "file": "Résumé ORTM - 2024-05-14.mp3"},
    {"date": "2024-05-24", "media": "Malijet", "duration": "4:20", "file": "Résumé ORTM - 2024-05-24.mp3"},
    {"date": "2024-05-14", "media": "Bamada", "duration": "3:45", "file": "Résumé ORTM - 2024-05-14.mp3"},
    {"date": "2024-05-24", "media": "aBamako", "duration": "4:20", "file": "Résumé ORTM - 2024-05-24.mp3"},
    # Ajoutez plus d'audios ici
]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/news")
def news():
    # query = request.args.get("query")
    # if query:
    #     filtered_audio = [
    #         audio for audio in audio_files if query.lower() in audio["name"].lower()
    #     ]
    # else:
    #     filtered_audio = audio_files
    return render_template("news2.html", audio_files=audios)


@app.route("/chat")
def chat():
    print("in chat")
    return redirect("http://localhost:8000")
    # return render_template("chat.html")


if __name__ == "__main__":
    app.run(debug=True)
