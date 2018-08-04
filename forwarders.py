import uuid
from typing import Dict

import hexchat
__module_name__ = "forwarders"
__module_version__ = "1.0"
__module_description__ = "Forwards specific command's responses to the current server window"

hooks: Dict[uuid.UUID, int] = {}


def cleanup(uid):
    if uid in hooks:
        hook = hooks[uid]
        hexchat.unhook(hook)
        del hooks[uid]

    return False


def tline_forward(word, word_eol, userdata):
    msg = word[0]
    if not msg.startswith("*** TLINE"):
        return
    s_msg = msg.split()
    ip = s_msg[6][1:-1]
    if ip != userdata[1]:
        return

    hexchat.find_context().prnt(msg)
    cleanup(userdata[0])
    return hexchat.EAT_HEXCHAT


def tline_callback(word, word_eol, userdata):
    if len(word) < 2:
        print("I require an argument")
        return

    ip = word[1]
    uid = uuid.uuid4()
    hooks[uid] = hexchat.hook_print("Server Notice", tline_forward, (uid, ip))
    hexchat.hook_timer(1000 * 3, cleanup, uid)


def check_forward(word, word_eol, userdata):
    print(word_eol[3][1:])


def debug_cb(word, word_eol, userdata):
    print(hooks)


@hexchat.hook_unload
def onunload(userdata):
    print(f"{__module_name__} unloaded")


hexchat.hook_command("TLINE", tline_callback)
hexchat.hook_command("FORWARDER_DEBUG", debug_cb)
hexchat.hook_server("304", check_forward)
print(f"{__module_name__} loaded")
