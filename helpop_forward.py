import hexchat

__module_name__ = "helpop_forward"
__module_version__ = "0.1"
__module_description__ = "Pushes HELPOP responses into your current channel, rather than to the server window"

hook = 0
msgbox = False
helpop_line = []


def numeric_cb(word, word_eol, userdata):
    line = word_eol[3][1:]
    print(line)
    if line == "*** End of HELPOP":
        hexchat.unhook(hook)
    return hexchat.EAT_HEXCHAT


def sanitise_line(line):
    replchar = "\xa0"
    if line:
        return line.replace(" ", replchar)
    else:
        return replchar


def helpop_cb(word, word_eol, userdata):
    global hook
    hook = hexchat.hook_server("292", numeric_cb)


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")


hexchat.hook_command("HELPOP", helpop_cb)
print(__module_name__, "loaded")
