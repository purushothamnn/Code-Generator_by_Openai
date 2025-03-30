from flask import Flask, render_template, request, jsonify
import os
import re
from openai import OpenAI
from config import API_KEY

client = OpenAI(api_key=API_KEY)

app = Flask(__name__)

def create_file(file_path, content):
    try:
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
    except OSError as e:
        print(f"Error creating file {file_path}: {e}")

def strip_first_and_last_line(text):
    lines = text.strip().split('\n')
    if len(lines) > 2:
        return '\n'.join(lines[1:-1])
    else:
        return ''

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        app_requirement = request.form.get('app_requirement', '').strip()
        folder_name = request.form.get('fileName', '').strip()

        if not app_requirement:
            return jsonify({"error": "App requirement cannot be empty"}), 400
        if not folder_name:
            return jsonify({"error": "Folder name cannot be empty"}), 400

        # Sanitize folder name
        folder_name = re.sub(r'[^\w\-_]', '', folder_name)
        if not folder_name:
            return jsonify({"error": "Invalid folder name"}), 400

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # Get file list
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Return name of all the files in a directory needed to make application in python that meets following needs - {app_requirement}. Strictly do not return anything else."}]
        )
        file_list = [file_name.lstrip('- ').strip() for file_name in response.choices[0].message.content.strip().split('\n')]

        # Get file contents
        file_contents = {}
        for file_name in file_list:
            response2 = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Return code for file {file_name}. Strictly do not return anything else."}]
            )
            file_contents[file_name] = strip_first_and_last_line(response2.choices[0].message.content)

        # Create files
        for file_name, content in file_contents.items():
            create_file(os.path.join(folder_name, file_name), content)

        return jsonify({"message": f"Files created successfully in folder: {folder_name}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)