import json
from typing import List
import smtplib, ssl
import requests
import threading
from flask import Flask, request, jsonify, make_response, Response
import datetime as dt
import os
from os import listdir
from os.path import isfile, join
from datetime import datetime
from werkzeug.exceptions import abort
import subprocess

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


@app.route('/mp3/<name>', methods=['GET', 'OPTIONS'])
def serve_mp3(name):
    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_preflight_response()
    folder = "/Users/satyendra.kumar/Documents/RandomlyGeneratedMusicalIdeas"

    def generate():
        with open(f"{folder}/{name}", "rb") as fwav:
            data = fwav.read(1024)
            while data:
                yield data
                data = fwav.read(1024)

    return _corsify_actual_response(Response(generate(), mimetype="audio/mpeg"))


def cleanup(folder):
    onlyfiles = [os.path.join(path, fn) for fn in next(os.walk(path))[2]] 
    for f in onlyfiles:
        ct = time.ctime(os.path.getctime(f))
        d = datetime.datetime.now() - ct 
        if d > 2:
            os.remove(f)




@app.route('/musicxml', methods=['POST', 'OPTIONS'])
def music_xml_to_mp3():
    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_preflight_response()
    folder = "/Users/satyendra.kumar/Documents/RandomlyGeneratedMusicalIdeas/"
    data = request.get_json(force=True)
    dt_string = datetime.now().strftime("%d-%m-%Y-%H%M%S")
    generated_name = f"{data['key']}_{dt_string}"
    prefix = f"{folder}/{generated_name}"
    musicxml_file = f'{prefix}.xml'

    with open(musicxml_file, 'w') as file:
        file.write(data['musicxml'])
    output_mp3_file = f"{prefix}.mp3"
    p = subprocess.Popen(["/Applications/MuseScore 4.app/Contents/MacOS/mscore", "-o", output_mp3_file, musicxml_file])
    p.wait()

    threading.Thread(target=cleanup, args=(folder,)).start()
    return _corsify_actual_response(jsonify({"name": f"{generated_name}.mp3"}))


@app.route('/article/<article_id>', methods=['POST'])
def save_article(article_id):
    perform_auth()

    article_json = request.get_json(force=True)

    if not article_json:
        data = request.get_data()
        print(data.decode("utf-8"))
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

    return make_response(jsonify({"status": "ok"}), 200)


def perform_auth():
    auth = request.headers.get('X-Auth')
    if not auth:
        auth = request.args.get("x-auth")
    if not auth or auth != os.getenv("USER_PASSWORD"):
        abort(401)


# A welcome message to test our server
@app.route('/')
def index():
    return "<h1>Welcome to our server !!</h1>"


def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    print("Returning preflight response", response)
    return response


def send_email():
    sender = 'apexcoder10@gmail.com'
    receivers = ['kumarsatya1990@gmail.com']

    message = """From: From ApexCoder <apexcoder10@gmail.com>
    To: To Satyendra <kumarsatya1990@gmail.com>
    Subject: SMTP e-mail test
    
    This is a test e-mail message.
    """

    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    try:
        smtpObj = smtplib.SMTP('smtp.gmail.com', port=587)
        smtpObj.starttls(context=context)
        smtpObj.login('apexcoder10@gmail.com', 'Alpha_1234')
        smtpObj.sendmail(sender, receivers, message)
        print("Successfully sent email")
    except smtplib.SMTPException as e:
        print("Error: unable to send email")

def handle_bad_request(e):
    print(e)
    return 'bad request!', 400

# or, without the decorator
app.register_error_handler(400, handle_bad_request)

if __name__ == '__main__':
    send_email()
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
