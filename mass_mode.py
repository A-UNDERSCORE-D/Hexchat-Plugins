import hexchat
from fnmatch import fnmatch

__module_name__ = "mass_mode"
__module_version__ = "0.1"
__module_description__ = "sets modes across all users in /who 0 u"

nick_list = []
hooks = {}


def who_hook(word, word_eol, userdata):
    if len(word) > 6 and not fnmatch(word[6], "*anope*"):
        nick_list.append(word[7])
    return hexchat.EAT_HEXCHAT


def do_mass_mode(userdata):
    nicks_to_mode = nick_list[:50]
    del nick_list[:50]
    if not nicks_to_mode:
        hexchat.command("Finished modes")
        return False
    for nick in nicks_to_mode:
        hexchat.command("OS UMODE {nick} {modes}".format(nick=nick, modes=userdata))
    return True


def end_who_hook(word, word_eol, userdata):
    if len(word) > 2 and word[3] == userdata[0]:
        hexchat.unhook(hooks["who"])
        hooks["who"] = 0
        hexchat.unhook(hooks["who_end"])
        hooks["who_end"] = 0
        hexchat.hook_timer(150, do_mass_mode, userdata[1])
        return hexchat.EAT_HEXCHAT


def cmd_cb(word, word_eol, userdata):
    if len(word) < 2:
        hexchat.command("ECHO I require an arg.")
        return hexchat.EAT_HEXCHAT
    nick_list.clear()
    hooks["who"] = hexchat.hook_server("352", who_hook)
    hooks["who_end"] = hexchat.hook_server("315", end_who_hook, ("0", word[1]))
    hexchat.command("WHO 0 u")
    return hexchat.EAT_HEXCHAT


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")


hexchat.hook_command("MASSUMODE", cmd_cb)
print(__module_name__, "loaded")
