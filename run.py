import subprocess
import os
from threading import Thread


def __execute__(cmd, cwd, env):
    my_env = os.environ.copy()
    if not env:
        env = {}
    my_env.update(env)

    def fn():
        popen = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE, universal_newlines=True, cwd=cwd, env=my_env)
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line
        popen.stdout.close()
        return_code = popen.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)
    for ln in fn():
        print(ln, end='')


def execute(cmd, cwd, env):
    t = Thread(target=__execute__, args=[cmd, cwd, env])
    t.start()


execute("yarn serve", "/Users/satyendra.kumar/Documents/PersonalProjects/cupitor/frontend/vue3/cupitor-frontend", None)
execute("node translatte-server.js", "/Users/satyendra.kumar/Documents/PersonalProjects/mediaelement/translatte-server", None)
execute("env USER_PASSWORD=satya-varsha GITHUB_TOKEN=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 python3 app.py", "/Users/satyendra.kumar/Documents/PersonalProjects/mediaelement/server", None)
execute("web-ext run", "/Users/satyendra.kumar/Documents/PersonalProjects/mediaelement/browser-extensions/svt-player", {})
