# 🗞️ kounafoni-app [kùnnafoni]
Mali local news summary web app

## 📝 Description: 
The idea is to provide a web interface to enable easy access to Malian news on a daily basis. 
It highlights the work of the local press and official media through high-quality summary reports.

## ℹ️📚 Usage
### Local 
To run the application locally, the easiest way is to open two separate shell terminals.
- In the first terminal, you will launch the flask application from the root directory,
the project's basic webapp: `python src/app/app.py`

- In the second terminal, you will launch the chainlit application in headless mode,
which is the server dedicated to interact with the chatbot: `chainlit run --headless src/chatbot.py`

Once you've launched these two servers, go to http://localhost:5000/ or http://127.0.0.1:5000


## ⚙️ Features
Using various data sources (ORTM, Malijet, etc.) :
- 10-minute summary of Malian news in podcast format
- Written and voice interaction with a chatbot (conversational agent) on Malian news.

[//]: # (Screenshots: Include screenshots of the application to give contributors a visual idea of the project.)

## 🔬 Technologies Used
Essentially built with python.

### 🛠️ External tools required
- Poetry -> See : https://python-poetry.org/docs/
- Install ffmpeg for audio processing : 
  - On Linux :
    - `sudo apt update && sudo apt install ffmpeg`
- Ollama -> See : https://ollama.com/download
  - For linux users :
    - curl -fsSL https://ollama.com/install.sh | sh
    - ollama run mistral:7b-instruct-q4_0

(Schema of underlying technologies used for the app will come soon)

## 🤝 Contribute
To be defined

## ©️ License
See [License](LICENSE).

## 📧 Contact
- website: lonytech.com
- mail: contact@lonytech.com or abubakrtraore@gmail.com

## More information
The lexicon used for the words present in this project comes from **BAMADABA**, a Bambara dictionary project
of the Bambara Reference Corpus.
See : 
- http://cormand.huma-num.fr/Bamadaba/lexicon/index.htm
- http://cormand.huma-num.fr/Bamadaba/index-french/a.htm (use the search button to find any word)
- https://aclanthology.org/W14-6501.pdf (about the corpus project)
