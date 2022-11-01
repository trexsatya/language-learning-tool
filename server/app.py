import json
from typing import List

import requests
from flask import Flask, request, jsonify, make_response
import datetime as dt
import os

from werkzeug.exceptions import abort

from github_util import push_to_repo_branch, get_branch_info

app = Flask(__name__)
base_url = "https://raw.githubusercontent.com/trexsatya/trexsatya.github.io/gh-pages/db"


@app.route('/getmsg/', methods=['GET'])
def respond():
    # Retrieve the name from url parameter
    name = request.args.get("name", None)

    # For debugging
    print(f"got name {name}")

    response = {}

    # Check if user sent a name at all
    if not name:
        response["ERROR"] = "no name found, please send a name."
    # Check if the user entered a number not a name
    elif str(name).isdigit():
        response["ERROR"] = "name can't be numeric."
    # Now the user entered a valid name
    else:
        response["MESSAGE"] = f"Welcome {name} to our awesome platform!!"

    # Return the response in json format
    return jsonify(response)


def update_index_if_required(updated, branch_info, repo_slug, branch, user, token):
    article_id_ = updated['id']
    current = requests.get(f"{base_url}/article/{article_id_}").json()

    [current_subject_, updated_subject_] = [current['subject'], updated['subject']]

    if current_subject_ != updated_subject_:
        print("Change in index: ", current_subject_, " -> ", updated_subject_)

        current_subject_json = requests.get(f"{base_url}/articles/{current_subject_}").json()
        current_subject_json = json.dumps(list(filter(lambda x: x['id'] != article_id_, current_subject_json)))
        print(f"Updated {current_subject_}: {current_subject_json}")
        push_to_repo_branch(f'db/articles/{current_subject_}', current_subject_json, branch_info, repo_slug, branch, user,
                            token)

        updated_subject_json = requests.get(f"{base_url}/articles/{updated_subject_}").json()
        updated_subject_json: List = list(filter(lambda x: x['id'] != article_id_, updated_subject_json))
        updated['content'] = ''
        updated_subject_json.append(updated)
        print(f"Updated {updated_subject_}: {json.dumps(updated_subject_json)}")
        push_to_repo_branch(f'db/articles/{updated_subject_}', json.dumps(updated_subject_json), branch_info, repo_slug, branch, user,
                            token)

    if current['name'] != updated['name']:
        print("We need to update search index")
        current_search_json = requests.get(f"{base_url}/search").json()
        for item in current_search_json:
            if item['id'] == updated['id']:
                item['name'] = updated['name']
                break
        push_to_repo_branch(f'db/search', json.dumps(current_search_json), branch_info, repo_slug,
                            branch, user,
                            token)

output_path = "/Users/satyendra.kumar/IdeaProjects/mediaelement/output"

def write_srt_file(translated, lang, file):
    basename = os.path.basename(file)
    file_name = f"{basename.split('.')[0]}_{lang}.srt"
    file_path = f"{output_path}/{file_name}"
    with open(file_path, 'w') as file:
        file.write(translated)


def write_audio_base64(audio, lang, file):
    basename = os.path.basename(file)
    file_name = f"audio_{basename.split('.')[0]}_{lang}.json"
    file_path = f"{output_path}/{file_name}"
    with open(file_path, 'w') as file:
        file.write(json.dumps(audio))


@app.route('/srt', methods=['POST'])
def save_srt():
    data = request.get_data()
    # print(data.decode("utf-8"))
    data = json.loads(data.decode("utf-8"))
    write_srt_file(data['translated'], data['lang'], data['file'])
    write_audio_base64(data['audio'],  data['lang'], data['file'])
    return {"status": "ok"}


@app.route('/article/<article_id>', methods=['POST'])
def save_article(article_id):
    auth = request.headers.get('X-Auth')
    if not auth:
        auth = request.args.get("x-auth")
    if not auth or auth != os.getenv("USER_PASSWORD"):
        abort(401)
    article_json = request.get_json()

    if not article_json:
        data = request.get_data()
        # print(data.decode("utf-8"))
        article_json = json.loads(data.decode("utf-8"))

    article_json['lastUpdated'] = str(dt.datetime.now())
    for key in ['img', 'summary']:
        if (key not in article_json) or not article_json[key]:
            article_json[key] = ''

    if ('tags' not in article_json) or not article_json['tags']:
        article_json['tags'] = []

    if ('authorId' not in article_json) or not article_json['authorId']:
        article_json['authorId'] = 1

    [repo_slug, branch, user, token] = ['trexsatya/trexsatya.github.io', 'gh-pages', 'trexsatya', os.getenv("GITHUB_TOKEN")]

    branch_info = get_branch_info(repo_slug, branch, user, token)

    push_to_repo_branch(f'db/article/{article_id}', json.dumps(article_json), branch_info, repo_slug, branch, user, token)

    update_index_if_required(article_json, branch_info, repo_slug, branch, user, token)

    return make_response(jsonify(article_json), 200)


# A welcome message to test our server
@app.route('/')
def index():
    return "<h1>Welcome to our server !!</h1>"


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)