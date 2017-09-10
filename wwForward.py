import hexchat

__module_name__ = "wwForward"
__module_version__ = "0.1"
__module_description__ = "Forwards real host field from /WHOWAS"

hooks = []


def command_cb(word, word_eol, userdata):
    hooks.append(hexchat.hook_server("379", on_whowas))
    hooks.append(hexchat.hook_server("369", unhook))


def on_whowas(word, word_eol, userdata):
    hexchat.emit_print("WhoIs Special", word[3], word_eol[4][1:])
    return hexchat.EAT_HEXCHAT


def unhook(word, word_eol, userdata):
    for hook in hooks:
        hexchat.unhook(hook)
    hooks.clear()


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")


hexchat.hook_command("WW", command_cb)
hexchat.hook_command("WHOWAS", command_cb)
print(__module_name__, "loaded")
