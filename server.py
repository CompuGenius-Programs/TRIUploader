import json
import os

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from git import Repo, rmtree

load_dotenv()

app = Flask(__name__)
app.config['KAARAH_FOLDER'] = 'repo/divrei_torah/kaarah'
app.config['MAAMAREI_MORDECHAI_FOLDER'] = 'repo/divrei_torah/maamarei_mordechai'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

username = os.getenv('GITHUB_USERNAME')
password = os.getenv('GITHUB_TOKEN')
repository = os.getenv('GITHUB_REPO')
remote = f"https://{username}:{password}@github.com/{username}/{repository}.git"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def update_html_file(urls, titles, descriptions, categories):
    with Repo.clone_from(remote, "repo") as repo:
        with open("urls.json", "r") as f:
            data = json.load(f)
        for url, title, description, category in zip(urls, titles, descriptions, categories):
            if category == "published_works":
                data[category].append({"sefer": title, "description": description, "url": url})
            else:
                data[category].append({"title": title, "url": url})
        with open("urls.json", "w") as f:
            json.dump(data, f, indent=2)

        repo.git.add("urls.json")
        message = f"Added {', '.join(titles)}"
        repo.index.commit(message)
        origin = repo.remote(name="origin")
        origin.push()

    rmtree("repo")


@app.route('/upload', methods=['POST'])
def upload_files():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid data format"}), 400

    urls = [item.get('url') for item in data]
    titles = [item.get('title') for item in data]
    descriptions = [item.get('description') for item in data]
    categories = [item.get('category') for item in data]

    update_html_file(urls, titles, descriptions, categories)

    return jsonify({"message": "Urls uploaded successfully", "urls": urls}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
