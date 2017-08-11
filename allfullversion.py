import hexchat

__module_name__ = "allfullversion"
__module_version__ = "0.1"
__module_description__ = ""

hook, hookend = 0, 0


def fullversioncmd(word, word_eol, userdata):
    global hook, hookend
    hook = hexchat.hook_server("364", links_cb)
    hookend = hexchat.hook_server("365", links_cb)
    hexchat.command("LINKS")
    return hexchat.EAT_HEXCHAT


def links_cb(word, word_eol, userdata):
    if word[1] == "364":
        hexchat.command("FULLVERSION {}".format(word[3]))
    elif word[1] == "365":
        global hook, hookend
        hexchat.unhook(hook)
        hexchat.unhook(hookend)


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")

hexchat.hook_command("ALLFULLVERSION", fullversioncmd, help="versions every server in links")

print(__module_name__, "loaded")
