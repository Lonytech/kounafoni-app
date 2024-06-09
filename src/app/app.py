from flask import Flask, redirect, render_template, url_for, request

app = Flask(__name__)

# Test audio data
audios = {
    "2024-05-14": [
        {"date": "2024-05-14", "media": "ORTM", "duration": "3:45", "file": "Résumé ORTM - 2024-05-14.mp3"},
        {"date": "2024-05-14", "media": "Malijet", "duration": "4:20", "file": "Résumé ORTM - 2024-05-14.mp3"},
        {"date": "2024-05-14", "media": "Bamada", "duration": "3:45", "file": "Résumé ORTM - 2024-05-14.mp3"},
        {"date": "2024-05-14", "media": "aBamako", "duration": "4:20", "file": "Résumé ORTM - 2024-05-14.mp3"}
    ],

    "2024-05-24": [
        {"date": "2024-05-24", "media": "ORTM", "duration": "3:45", "file": "Résumé ORTM - 2024-05-24.mp3"},
        {"date": "2024-05-24", "media": "Malijet", "duration": "4:20", "file": "Résumé ORTM - 2024-05-24.mp3"},
        {"date": "2024-05-24", "media": "Bamada", "duration": "3:45", "file": "Résumé ORTM - 2024-05-24.mp3"},
        {"date": "2024-05-24", "media": "aBamako", "duration": "4:20", "file": "Résumé ORTM - 2024-05-24.mp3"}
    ],

    "2024-05-16": [
        {"date": "2024-05-16", "media": "ORTM", "duration": "3:45", "file": "Résumé ORTM - 2024-05-16.mp3"},
        {"date": "2024-05-16", "media": "Malijet", "duration": "4:20", "file": "Résumé Malijet - 2024-05-16.mp3"},
        {"date": "2024-05-16", "media": "Bamada", "duration": "3:45", "file": "Résumé ORTM - 2024-05-16.mp3"},
        {"date": "2024-05-16", "media": "aBamako", "duration": "4:20", "file": "Résumé ORTM - 2024-05-16.mp3"}
    ]
}


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
    sorted_audio = sorted(audios.items(), key=lambda x: x[0], reverse=True)
    return render_template("news2.html", audio_files=sorted_audio)


@app.route("/chat")
def chat():
    print("in chat")
    return redirect("http://localhost:8000")
    # return render_template("chat.html")


if __name__ == "__main__":
    app.run(debug=True)
