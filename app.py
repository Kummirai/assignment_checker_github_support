from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
import requests
from checker import run_user_code, parse_test_file

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
TEST_FOLDER = os.path.join(BASE_DIR, 'test_cases')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def evaluate_code(code_filename, code_content):
    test_files = sorted(f for f in os.listdir(TEST_FOLDER) if f.endswith(".txt"))
    results = []

    # Match test file by filename
    base_name = os.path.splitext(code_filename)[0]
    test_file_name = next((f for f in test_files if f.startswith(base_name)), None)

    if test_file_name:
        test_path = os.path.join(TEST_FOLDER, test_file_name)
        with open(test_path, 'r') as f:
            test_content = f.read()

        inputs, expected_output = parse_test_file(test_content)
        actual_output = run_user_code(code_content, inputs)

        results.append({
            "filename": code_filename,
            "inputs": inputs,
            "expected": expected_output,
            "output": actual_output,
            "passed": expected_output.strip() == actual_output.strip()
        })
    else:
        results.append({
            "filename": code_filename,
            "error": f"No matching test file for {code_filename}"
        })

    return results

@app.route("/", methods=["GET", "POST"])
def index():
    results = []

    if request.method == "POST":
        # Handle local uploads
        code_files = request.files.getlist("code_files")
        for code_file in code_files:
            if code_file:
                code_filename = secure_filename(code_file.filename)
                code_path = os.path.join(UPLOAD_FOLDER, code_filename)
                code_file.save(code_path)

                with open(code_path, 'r') as f:
                    code_content = f.read()

                results.extend(evaluate_code(code_filename, code_content))

        # Handle GitHub file input
        github_url = request.form.get("github_url")
        if github_url and github_url.endswith(".py"):
            try:
                response = requests.get(github_url)
                if response.status_code == 200:
                    raw_code = response.text
                    filename = github_url.split("/")[-1]
                    results.extend(evaluate_code(filename, raw_code))
                else:
                    results.append({
                        "filename": github_url,
                        "error": f"Failed to fetch file. HTTP {response.status_code}"
                    })
            except Exception as e:
                results.append({
                    "filename": github_url,
                    "error": f"Request failed: {e}"
                })

    return render_template("index.html", results=results)