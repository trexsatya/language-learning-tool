import requests
import base64
import json
import datetime

from utils import Nothing, Just


def find_in_list(func, items):
    filtered = list(filter(func, items))
    if not filtered:
        return Nothing
    return Just(filtered[0])


def __get_file_sha(treeurl, gitHubFileName, user, token):
    r2json = make_call(token, treeurl, user)
    # print(r2json)
    return find_in_list(lambda x: x['path'] == gitHubFileName, r2json['tree']).map(lambda x: x['sha']).orElse(None)


def get_file_sha(treeurl, path, user, token):
    if "/" not in path:
        return __get_file_sha(treeurl, path, user, token)

    [containing_dir, rest_of_path] = path.split("/", 1)
    r2json = make_call(token, treeurl, user)

    treeurl_maybe = find_in_list(lambda x: x['path'] == containing_dir and x["type"] == 'tree', r2json['tree'])

    return treeurl_maybe.map(lambda x: get_file_sha(x['url'], rest_of_path, user, token)).orElse(None)


def make_call(token, treeurl, user):
    r2 = requests.get(treeurl, auth=(user, token))
    if not r2.ok:
        print("Error when retrieving commit tree from %s" % treeurl)
        print("Reason: %s [%d]" % (r2.text, r2.status_code))
        raise Exception("")
    r2json = r2.json()
    return r2json


def get_branch_info(repo_slug, branch, user, token):
    path = "https://api.github.com/repos/%s/branches/%s" % (repo_slug, branch)

    r = requests.get(path, auth=(user, token))
    if not r.ok:
        print("Error when retrieving branch info from %s" % path)
        print("Reason: %s [%d]" % (r.text, r.status_code))
        raise Exception("")
    rjson = r.json()
    return rjson


def push_to_repo_branch(gitHubFileName, content, branch_info, repo_slug, branch, user, token):
    '''
    Push file update to GitHub repo

    :param gitHubFileName: the name of the file in the repo
    :param fileName: the name of the file on the local branch
    :param repo_slug: the github repo slug, i.e. username/repo
    :param branch: the name of the branch to push the file to
    :param user: github username
    :param token: github user token
    :return None
    :raises Exception: if file with the specified name cannot be found in the repo
    '''

    message = "Automated update " + str(datetime.datetime.now())
    # rjson = get_branch_info(repo_slug, branch, user, token)
    # print(rjson)
    # print("\n\n")

    root_dir_url = branch_info['commit']['commit']['tree']['url']
    sha = get_file_sha(root_dir_url, gitHubFileName, user, token)

    # if sha is None after the recursion, we did not find the file name!
    if sha is None:
        raise Exception("Could not find " + gitHubFileName + " in repos 'tree' ")

    # with open(fileName, "rb") as data:
    #     content = data.read()
    #     # print(dr)

    content = base64.b64encode(bytes(content, 'utf-8')).decode("ascii")

    # gathered all the data, now let's push
    inputdata = {}
    inputdata["path"] = gitHubFileName
    inputdata["branch"] = branch
    inputdata["message"] = message
    inputdata["content"] = content
    if sha:
        inputdata["sha"] = str(sha)

    updateURL = f"https://api.github.com/repos/{repo_slug}/contents/" + gitHubFileName
    try:
        rPut = requests.put(updateURL, auth=(user, token), data=json.dumps(inputdata))
        # print(rPut.text)
        if not rPut.ok:
            print("Error when pushing to %s" % updateURL)
            print("Reason: %s [%d]" % (rPut.text, rPut.status_code))
            raise Exception
    except requests.exceptions.RequestException as e:
        print('Something went wrong! I will print all the information that is available so you can figure out what '
              'happend!')
        print(rPut)
        print(rPut.headers)
        print(rPut.text)
        print(e)


