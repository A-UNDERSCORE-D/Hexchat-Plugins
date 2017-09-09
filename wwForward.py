import hexchat

__module_name__ = "wwForward"
__module_version__ = "0.1"
__module_description__ = "Forwards real host field from /WHOWAS"


def on_whowas(word, word_eol, userdata):
    hexchat.emit_print("WhoIs Special", word[3], word_eol[4][1:])


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")


hexchat.hook_server("379", on_whowas)
print(__module_name__, "loaded")
