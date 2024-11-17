import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from flask import Flask, Response, redirect, render_template, send_from_directory

AUDIOS_DIRECTORY_PATH = Path(__file__).parents[2] / "data" / "piper" / "exports"


if os.environ.get("CHATBOT_ENV") == "production":
    AUDIOS_DIRECTORY_PATH = (
        Path(__file__).parents[2] / "external_volume" / "data" / "exports"
    )

app = Flask(__name__)

# get a complete list of audio from directory
audio_dates_dirs = [d for d in AUDIOS_DIRECTORY_PATH.iterdir() if d.is_dir()]
audios = defaultdict(list)
for folder in audio_dates_dirs:
    for f in folder.iterdir():
        print(f)
        if f.is_file():
            print(f)
            audios[folder.name].append(
                {
                    "media": "ORTM",
                    "file": f.name,
                }
            )


@app.route("/data/<path:filename>")
def serve_audio(filename: str) -> Any:
    return send_from_directory(AUDIOS_DIRECTORY_PATH, filename)


@app.route("/")
def home() -> Any:
    return render_template("index.html")


@app.route("/news")
def news() -> Any:
    sorted_audio = sorted(audios.items(), key=lambda x: x[0], reverse=True)
    return render_template("news.html", audio_files=sorted_audio)


@app.route("/chat")
def chat() -> Any:
    if os.environ.get("FLASK_ENV") == "production":
        return redirect("https://chat.kounafonia.lonytech.com/")
    else:
        return redirect("http://127.0.0.1:8000")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    # app.run(debug=True)
