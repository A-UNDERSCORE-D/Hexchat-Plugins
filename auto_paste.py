import threading

import hexchat
import requests

__module_name__ = "auto_paste"
__module_version__ = "0.1"
__module_description__ = "Automatically pastes hexchat lines with newlines in them"

KEYIDs = {
    "65293": "enter",
    "121": "y",
    "110": "n",
    "109": "m",
    "99": "c",
    "112": "p"
}

waiting_on_response = False
waiting_on_message = False
message = ""
to_paste = ""

paste_target = "https://paste.ferricyanide.solutions"


def on_key(word, word_eol, userdata):
    keyid = word[0]
    if keyid not in KEYIDs:
        return
    key_name = KEYIDs[keyid]
    if key_name == "enter":
        return on_enter()

    global waiting_on_response
    if not waiting_on_response:
        return hexchat.EAT_NONE

    waiting_on_response = False
    clear_inputbox()
    if key_name == "y":
        return start_paste()

    if key_name == "n" or key_name == "c":
        return cancel()

    if key_name == "m":
        return grab_message()

    if key_name == "p":
        return dump_lines()


def grab_message():
    print("type the message and hit enter")
    global waiting_on_message
    waiting_on_message = True
    return hexchat.EAT_HEXCHAT


def cancel():
    print("cancelling")
    return hexchat.EAT_HEXCHAT


def start_paste():
    print("pasting data")
    global waiting_on_response, message
    t = threading.Thread(
        target=do_paste, args=[hexchat.get_context(), to_paste, message]
    )
    t.daemon = True
    t.start()
    waiting_on_response = False
    message = ""


def dump_lines():
    for line in to_paste.split("\n"):
        if not line:
            continue

        if line.startswith("//"):
            hexchat.command(f"say {line[1:]}")
        elif line.startswith("/"):
            hexchat.command(line[1:])
        else:
            hexchat.command(f"say {line}")


def on_enter():
    ib = get_inputbox()
    global waiting_on_message
    if waiting_on_message:
        global message
        message = ib
        waiting_on_message = False
        print("added message")
        clear_inputbox()
        start_paste()
        return hexchat.EAT_HEXCHAT

    if count_newlines(ib) > 5:
        print("multiline text detected. paste? yes, no, message, cancel, send as lines y/n/m/c/p")
        clear_inputbox()
        global to_paste
        to_paste = ib
        global waiting_on_response
        waiting_on_response = True
        return hexchat.EAT_HEXCHAT


def get_inputbox():
    return hexchat.get_info("inputbox")


def clear_inputbox():
    hexchat.command("settext ")


def count_newlines(string):
    count = 0
    for c in string:
        if c == "\n":
            count += 1

    return count


def do_paste(ctx, str_to_paste, msg):
    res = requests.post(paste_target + "/documents", data=str_to_paste)
    if res.status_code != 200:
        print(f"Paste failed: {res}")
        return
    key = res.json()["key"]
    url = f"{paste_target}/{key}"
    if msg:
        ctx.command(f"say {msg} {url}")
    else:
        ctx.command(f"say I sent a bunch of lines at once: {url}")


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")


hexchat.hook_print("Key Press", on_key)

print(__module_name__, "loaded")
