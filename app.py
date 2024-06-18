from flask import Flask, request, render_template_string, send_file
import pdfplumber
from gtts import gTTS
import io

app = Flask(__name__)

index_html = '''

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF to Speech Converter</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background-color: #f0f0f0;
            margin: 0;
            padding: 0;
        }

        h1 {
            margin-top: 50px;
            color: #333;
        }

        form {
            margin: 20px 0;
        }

        input[type="file"] {
            display: block;
            margin: 0 auto 10px auto;
        }

        .upload-button, .audio-button {
            background-color: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 5px;
        }

        .upload-button:hover, .audio-button:hover {
            background-color: #218838;
        }

        #progress {
            margin: 20px 0;
        }

        textarea {
            width: 80%;
            height: 200px;
            margin: 20px auto;
            display: block;
            padding: 10px;
            font-size: 14px;
            border-radius: 5px;
            border: 1px solid #ccc;
            background-color: #fff;
            resize: none;
        }

        audio {
            margin: 20px auto;
            display: block;
        }
    </style>
</head>
<body>
    <h1>Upload a PDF to extract text and convert to speech</h1>
    <form id="upload-form" enctype="multipart/form-data">
        <input type="file" id="file-input" name="file">
        <button type="button" onclick="uploadFile()" class="upload-button">Upload</button>
    </form>
    <div id="progress" style="display:none;">
        <p>Loading...</p>
        <progress value="0" max="100"></progress>
    </div>
    <div id="extracted-text-section" style="display:none;">
        <h2>Extracted Text</h2>
        <textarea id="extracted-text" readonly></textarea>
        <form id="synthesize-form">
            <button type="button" onclick="generateAudio()" class="audio-button">Generate Audio</button>
        </form>
        <audio id="audio-output" controls></audio>
    </div>

    <script>
        function uploadFile() {
            const fileInput = document.getElementById('file-input');
            if (fileInput.files.length === 0) {
                alert('Please select a file.');
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload', true);

            xhr.upload.onprogress = function(event) {
                if (event.lengthComputable) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    document.querySelector('#progress progress').value = percentComplete;
                }
            };

            xhr.onload = function() {
                if (xhr.status === 200) {
                    document.getElementById('progress').style.display = 'none';
                    document.getElementById('extracted-text-section').style.display = 'block';
                    document.getElementById('extracted-text').value = xhr.responseText;
                } else {
                    alert('Error uploading file.');
                }
            };

            document.getElementById('progress').style.display = 'block';
            xhr.send(formData);
        }

        function generateAudio() {
            const textInput = document.getElementById('extracted-text').value;

            if (textInput.trim() === '') {
                alert('No text extracted.');
                return;
            }

            const formData = new FormData();
            formData.append('text', textInput);

            fetch('/synthesize', {
                method: 'POST',
                body: formData
            })
            .then(response => response.blob())
            .then(blob => {
                const audioURL = URL.createObjectURL(blob);
                const audioOutput = document.getElementById('audio-output');
                audioOutput.src = audioURL;
                audioOutput.play();
            })
            .catch(error => {
                console.error('Error generating audio:', error);
            });
        }
    </script>
</body>
</html>

'''

@app.route('/')
def index():
    return render_template_string(index_html)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part', 400

    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    # Extract text from PDF
    text = ''
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text()

    if not text.strip():
        return 'No text found in PDF', 400

    return text

@app.route('/synthesize', methods=['POST'])
def synthesize():
    text = request.form.get('text')
    if not text:
        return 'No text provided', 400

    # Convert text to speech
    tts = gTTS(text, lang='en', slow=True)
    audio = io.BytesIO()
    tts.write_to_fp(audio)
    audio.seek(0)

    return send_file(audio, mimetype='audio/mp3', as_attachment=True, download_name='speech.mp3')

if __name__ == '__main__':
    app.run(debug=True)
