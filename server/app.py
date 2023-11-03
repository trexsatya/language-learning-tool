import json
from typing import List
import smtplib, ssl
import requests
import threading
from flask import Flask, request, jsonify, make_response, Response
import datetime as dt
import os
import re
import time
from os import listdir
from os.path import isfile, join
from datetime import datetime
from werkzeug.exceptions import abort
import subprocess
from math import floor
import jsonpickle
import pysrt
import pathlib
import uuid
from github_util import push_to_repo_branch, get_branch_info
import subprocess
import unicodedata
import urllib.parse

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
        push_to_repo_branch(f'db/articles/{current_subject_}', current_subject_json, branch_info, repo_slug, branch,
                            user,
                            token)

        updated_subject_json = requests.get(f"{base_url}/articles/{updated_subject_}").json()
        updated_subject_json: List = list(filter(lambda x: x['id'] != article_id_, updated_subject_json))
        updated['content'] = ''
        updated_subject_json.append(updated)
        print(f"Updated {updated_subject_}: {json.dumps(updated_subject_json)}")
        push_to_repo_branch(f'db/articles/{updated_subject_}', json.dumps(updated_subject_json), branch_info, repo_slug,
                            branch, user,
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

@app.route('/proxy', methods=['GET'])
def proxy():
    url = request.args.get("url", None)
    resp = requests.get(url).text
    return _corsify_actual_response(Response(resp, mimetype="text/plain"))


@app.route('/srt', methods=['POST'])
def save_srt():
    data = request.get_data()
    # print(data.decode("utf-8"))
    data = json.loads(data.decode("utf-8"))
    write_srt_file(data['translated'], data['lang'], data['file'])
    write_audio_base64(data['audio'], data['lang'], data['file'])
    return {"status": "ok"}


def __find_matching_mp3(srt_file):
    def normalize(s):
        s = unicodedata.normalize('NFC', s).replace("？", " ")\
                .replace("：", " ").replace("⧸", " ").replace("｜", " ").replace("_", " ")
        return ' '.join(s.split())

    srt_file = srt_file.replace("[Swedish] ", "")
    srt_file = srt_file.replace(" [DownSub.com]", "")
    p = pathlib.Path(srt_file)

    normalized_name_srt = normalize( p.name)
    print("Looking for mp3 for", srt_file)

    for it in p.parent.glob("*.mp3"):
        name = str(it.stem)
        normalized_name_mp3_file = normalize(name)

        if "Edith" in name:
            def chars(s):
                return s + str(list(map(lambda x: f"{x}_{ord(x)}", list(unicodedata.normalize('NFC', s)))))
            print(f"{chars(normalized_name_mp3_file)}\n{chars(str(normalized_name_srt))}")

        if normalized_name_mp3_file in normalized_name_srt:
            return it

# __find_matching_mp3('/Users/satyendra.kumar/Documents/Swedish_Media/Swedish_YT_2/[Swedish] PUTIN-PRISER -
# Klimatrörelse + Krig ekonomisk armageddon_ [DownSub.com].srt')


def slice_mp3(in_file, out_file, start, end):
    def extract(n):
        s = str(n)
        if ":" in s:
            return s.replace(",", ".")
        millis = s[-3:]
        rest = s[:-3]
        n = int(rest)
        hrs = floor(n / 3600)
        mins = floor((n % 3600) / 60)
        secs = floor((n % 3600) % 60)
        return f"{str(hrs).rjust(2, '0')}:{str(mins).rjust(2, '0')}:{str(secs).rjust(2, '0')}.{millis}"

    folder = pathlib.Path(out_file).parent
    if not folder.exists():
        print(f"Creating new dir {folder}")
        folder.mkdir(parents=True)

    cmd = f"ffmpeg -ss {extract(start)} -t {extract(end - start)} -i \"{in_file}\"  -acodec copy {out_file}"
    print(cmd)
    os.system(cmd)


def folder_for_word(word):
    word = '_'.join(map(lambda x: x.strip().lower(), word.split(" ")))
    _dir = pathlib.Path(f"/Users/satyendra.kumar/Documents/Swedish_Media/WordBuilding/{word}")
    if not _dir.exists():
        try:
            _dir.mkdir()
        except FileExistsError:
            pass
    return _dir


def mp3_out_file_for_word(word):
    _dir = folder_for_word(word)
    return f"{str(_dir)}/{datetime.now().timestamp()}.mp3"


counter = 0


def record_mp3_mapping(mp3_file, text, file):
    folder = pathlib.Path(mp3_file).parent
    text_json_path = pathlib.Path(f"{folder}/texts.json")
    text_json = []
    if text_json_path.exists():
        with text_json_path.open() as f:
            text_json = json.load(f)
    text_json.append({'text': text, 'mp3': mp3_file, 'file': file})
    with text_json_path.open(mode='w') as f:
        json.dump(text_json, f)

    texts_added = []
    uniq = []
    for it in text_json:
        if not (it['text'] in texts_added):
            uniq.append(it)
            texts_added.append(it['text'])

    url = f"https://storage.googleapis.com/cupitor-220103.appspot.com/audio"
    html = " <br>\n"

    def url_for_mp3(p):
        p = p.replace('/Users/satyendra.kumar/Documents/Swedish_Media/WordBuilding/', '')
        p = p.replace("ä", "a%CC%88")
        p = p.replace("å", "a%CC%8A")
        p = p.replace("ö", "o%CC%88")
        return f"{url}/{p}"

    for it in uniq:
        global counter
        counter += 1
        xid = f"{datetime.now().timestamp()}-{counter}"
        fallback = f"<a href=\"{url_for_mp3(it['mp3'])}\"> Listen </a>"
        html += f"<div example-id=\"{xid}\"><span class=\"example\"> {it['text']} </span> <audio type=\"audio/mpeg\" " \
                f"src=\"{url_for_mp3(it['mp3'])}\" controls>{fallback}</audio> " \
                f"<div style=\"color: grey;font-size: smaller;\">Source: " \
                f"<a href=\"https://www.youtube.com/results?search_query={it['file']}\">{it['file']} </a></div> </div> <br>\n"

    with pathlib.Path(f"{folder}/html.txt").open(mode='w+') as f:
        f.write(html)

    return text_json

# TESTS
# print(folder_for_word("kvar"))
# mp3_for_kvar = mp3_out_file_for_word("kvar")
# slice_mp3("/Users/satyendra.kumar/Documents/Swedish_Media/Swedish_YT_2/ENERGI-KRIS： Till kärnkraftens FÖRSVAR.mp3",
#           mp3_for_kvar, 810100, 817380)
# record_mp3_mapping(mp3_for_kvar, 'Kvar means left')
# print(mp3_out_file_for_word("kvar"))


def __find_word(text):
    if not text or len(text) < 3:
        return []
    base_dir = "/Users/satyendra.kumar/Documents/Swedish_Media"
    p = pathlib.Path(base_dir)
    relevant = []
    for it in p.rglob("*.srt"):
        subs = pysrt.open(it)
        sub_text = '\n'.join(map(lambda x: x.text, subs))

        if re.search(text.lower(), sub_text.lower()):
            relevant.append(subs)

    return relevant


# print(len(list(map(lambda x: x[0], __find_word("bn")))))


@app.route('/find', methods=['GET'])
def find_word():
    text = request.args.get("text", None)
    res = __find_word(text)
    _json = jsonpickle.encode(res, unpicklable=False)
    return _corsify_actual_response(Response(_json, mimetype="application/json"))


@app.route('/extract_word_from_subtitle', methods=['POST'])
def extract_word():
    data = request.get_json(force=True)
    srt_path = data['srt_path']
    start = data['start']
    end = data['end']
    word = data['word']
    text = data['text']

    mp3_path = __find_matching_mp3(srt_path)
    if not mp3_path:
        return f"No matching mp3 found {mp3_path}", 400

    mp3_for_word = mp3_out_file_for_word(word)
    slice_mp3(mp3_path, mp3_for_word, start, end)
    _json = record_mp3_mapping(mp3_for_word, text, pathlib.Path(srt_path).stem)

    return _corsify_actual_response(Response(jsonpickle.encode(_json, unpicklable=False), mimetype="application/json"))


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
    onlyfiles = [os.path.join(path, fn) for fn in next(os.walk(folder))[2]]
    for f in onlyfiles:
        ct = time.ctime(os.path.getctime(f))
        d = datetime.now() - ct
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

    [repo_slug, branch, user, token] = ['trexsatya/trexsatya.github.io', 'gh-pages', 'trexsatya',
                                        os.getenv("GITHUB_TOKEN")]

    branch_info = get_branch_info(repo_slug, branch, user, token)

    push_to_repo_branch(f'db/article/{article_id}', json.dumps(article_json), branch_info, repo_slug, branch, user,
                        token)

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
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
