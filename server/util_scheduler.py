import schedule
import time
import requests
from pyquery import PyQuery as pq
import lxml
import urllib
import random
import certifi
import json
import smtplib, ssl
import os
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from github_util import push_to_repo_branch, get_branch_info
import pytz
import itertools

base_url = "https://raw.githubusercontent.com/trexsatya/trexsatya.github.io/gh-pages/db"
ARTICLE_URL = f"{base_url}/article/14"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def send_email(subject, body):
    context = ssl.create_default_context(cafile=certifi.where())
    sender = 'kumarsatya1990@gmail.com'
    receivers = ['kumarsatya1990@gmail.com'
        ,'anna_zhy@hotmail.com', 'yuanyuanliuse@gmail.com'
                 ]
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = receivers[0]

    html = f"""\
<html>
  <body>
    {body}
  </body>
</html>
"""

    part1 = MIMEText("", "plain")
    part2 = MIMEText(body, "html")

    message.attach(part1)
    message.attach(part2)

    try:
        smtpObj = smtplib.SMTP('smtp-mail.outlook.com', 587)
        smtpObj.starttls(context=context)

        smtpObj.login(os.getenv('EMAIL_ID'), os.getenv("EMAIL_PWD"))
        smtpObj.sendmail(sender, receivers, message.as_string())

#         print("Successfully sent email")
    except smtplib.SMTPException as e:
        print(e)
        pass


word_of_the_day = None


def find_random_word(_filter, d):
    # print(d(".title-popup"))

    ids = []
    for el in d("li > div"):
        ids.append(d(el).attr('example-id'))

    unfiltered_ids = ids
    if _filter:
        ids = list(filter(_filter, ids))

    # print("Choices", ids)
    if not len(ids):
        print("Filter returns 0 items, selecting a random word")
        reset_word_of_the_day()
        ids = unfiltered_ids
    selected_id = random.choice(ids)

    content = get_example_content(d, selected_id)

    return selected_id, content


def get_example_content(d, selected_id):
    el = d(f"div[example-id=\"{selected_id}\"]")
    content = f"""
{pq(el).html()}
<br>
<hr>
"""
    for ts in d(el).find(".title-popup"):
        content += f""" {d(ts).attr('title')} <br>"""
    return content


def get_article():
    url = ARTICLE_URL
    response = requests.get(url)
    response.raise_for_status()
    json = response.json()
    return json


def record_it(word_html_id, _history):
    _history.append({'time': time_now().strftime(DATETIME_FORMAT), 'word_html_id': word_html_id})
    push_history_to_github(_history)


def push_history_to_github(_history):
    [repo_slug, branch, user, token] = ['trexsatya/trexsatya.github.io', 'gh-pages', 'trexsatya',
                                        os.getenv("GITHUB_TOKEN")]
    branch_info = get_branch_info(repo_slug, branch, user, token)
    push_to_repo_branch(f'db/word_history.json', json.dumps(_history), branch_info, repo_slug, branch, user,
                        token)


def was_used_how_many_days_ago(x):
    return (time_now().replace(tzinfo=None) - datetime.datetime.strptime(x['time'], DATETIME_FORMAT)).days


def get_digest(days=7):
    history = requests.get(f"{base_url}/word_history.json").json()
    relevant = filter(lambda x: was_used_how_many_days_ago(x) <= days, history)

    _json = get_article()
    d = pq(lxml.html.fromstring(_json['content']))

    contents = []
    for it in list(relevant):
        contents.append(get_example_content(d, it['word_html_id']))

    return '<a href="https://satyendra.website/practice-words.html">Practice All</a> <br><br>' + '<br/><hr/><hr/><br/>'.join(
        contents)


def used_within_days(days, _history):
    return filter(lambda x: was_used_how_many_days_ago(x) <= days, _history)


def not_used_within_days(days, _history):
    return filter(lambda x: was_used_how_many_days_ago(x) > days, _history)


def is_local():
    with os.popen('hostname') as o:
        return o.read() == "C02GC4WQMD6R\n"


def get_words_from_example(d, ex):
    all_words = []
    for w in d(ex).find(".title-popup"):
        words = d(f"<span>{d(w).attr('title')}</span>").text()
        words = list(filter(lambda x: len(x) > 0, map(lambda x: x.strip(), words.split(";"))))
        all_words.extend(words)

    return all_words


def get_all_words(d):
    all_words = {}

    for ex in d(".example"):
        ex_id = d(ex).parent().attr("example-id")
        all_words[ex_id] = get_words_from_example(d, ex)

    return all_words


def job(_article_html, _history, _time, _day):
    print("Time=", datetime.datetime.now())

    def ids_used_within_days(d):
        return list(map(lambda x: x['word_html_id'], used_within_days(d, _history)))

    def ids_not_used_within_days(d):
        return list(map(lambda x: x['word_html_id'], not_used_within_days(d, _history)))

    pyquery_dollar = pq(lxml.html.fromstring(_article_html))

    all_words = get_all_words(pyquery_dollar)
    # print(all_words)

    def word_split(x, i):
        splits = x.split("=")
        if len(splits) < 2:
            return []
        return list(map(lambda _x: _x.strip().replace("vs. ", "").replace("vs. ", ""), splits[i].strip().split("/")))

    def are_related(x, y):
        x = x.lower()
        y = y.lower()
#         print("Are related?", x, y)
        return x == y or x in y or y in x

    def example_has_similarity_to_word_of_the_day(_id):
        if not word_of_the_day:
#             print("No word_of_the_day", _id)
            return True

        words_for_this_ex = all_words[_id]
        all_words_for_this_ex = ';'.join(words_for_this_ex)

        for pair in itertools.product(word_split(word_of_the_day, 0), itertools.chain(*map(lambda x: word_split(x, 0),
                                                                                           words_for_this_ex))):
            is_related = are_related(*pair)

            if is_related:
#                 print(f"Found match:\n  Words in ex: {all_words_for_this_ex}\n  WOTD: {word_of_the_day}", )
                return True
        return False

    [word_html_id, word_html] = find_random_word(lambda _id:
                                                 (_id not in ids_used_within_days(30)) and
                                                 example_has_similarity_to_word_of_the_day(_id),
                                                 pyquery_dollar)

    set_word_of_the_day_if_null(random.choice(all_words[word_html_id]))

    print(f"Chosen Word(s)= ID: {word_html_id}, {all_words[word_html_id]}" )

    link = ""

    if _time == "20:30:00":
        link = f"<br><br> <a href=\"https://satyendra.website/practice-words.html\">Practice Words</a> <br><br>"

    send_email('På Svenska!', f"{word_html} {link}")
    try:
        record_it(word_html_id, _history)
    except Exception as e:
        print(e)

    return [word_html_id, word_html]


def set_word_of_the_day(choice):
    global word_of_the_day
    word_of_the_day = choice


def set_word_of_the_day_if_null(choice):
    global word_of_the_day
    if not word_of_the_day:
        new_word_of_the_day = choice
        print("Setting word_of_the_day:", new_word_of_the_day)
        word_of_the_day = new_word_of_the_day


def time_now():
    return datetime.datetime.now().astimezone(pytz.timezone('Europe/Stockholm'))


# send_email("På Svenska, Weekly Revision!", get_digest())


def run_loop():
    while True:
        times = ["08:30", "11:30", "14:30", "17:30", "20:30"]
        now = time_now()
        now_as_str = now.strftime("%H:%M:%S")

        if now_as_str == "08:30:00":
            reset_word_of_the_day()

        if now.weekday() == 6 and now_as_str == "21:51:00":
            send_email("På Svenska, Weekly Revision!", get_digest())
        else:
            for tm in times:
                if now_as_str == f"{tm}:00":
                    _history = requests.get(f"{base_url}/word_history.json").json()
                    _article = get_article()
                    job(_article['content'], _history, now_as_str, now.weekday())

        time.sleep(1)


def reset_word_of_the_day():
    global word_of_the_day
    word_of_the_day = None


if __name__ == '__main__':
    run_loop()
