import json
from crypt import methods
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
import threading
import base64
import io, base64



app = Flask(__name__)
base_url = "https://raw.githubusercontent.com/trexsatya/trexsatya.github.io/gh-pages/db"

@app.route('/api/save-vocab', methods=['POST', 'OPTIONS'])
def save_vocab():
    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_preflight_response()
    perform_auth()
    data = request.get_data(as_text=True)
    [repo_slug, branch, user, token] = ['trexsatya/trexsatya.github.io', 'gh-pages', 'trexsatya',
                                        os.getenv("GITHUB_TOKEN")]
    branch_info = get_branch_info(repo_slug, branch, user, token)
    # print(current)
    push_to_repo_branch(f'db/language/swedish/vocabulary.txt', data, branch_info, repo_slug, branch,
                        user,
                        token)
    return _corsify_actual_response(jsonify({"status": "ok"}))

def perform_auth():
    auth = request.headers.get('X-Auth')
    if not auth:
        auth = request.args.get("x-auth")
    if not auth or auth != os.getenv("USER_PASSWORD"):
        abort(401)


# A welcome message to test our server
@app.route('/', methods=['GET'])
def index():
    return "<h1>Welcome to our server !!. endpoints start with /api</h1>"

@app.route('/hello', methods=['GET'])
def hello():
    return "<h1>Hello!</h1>"

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


def handle_bad_request(e):
    print(e)
    return 'bad request!', 400


# or, without the decorator
app.register_error_handler(400, handle_bad_request)

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
