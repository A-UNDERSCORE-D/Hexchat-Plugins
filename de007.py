import hexchat

__module_name__ = "kill007"
__module_description__ = "removes 007s from raw lines"
__module_version__ = "0.5"


def remove(word, word_eol, userdata):
    if "\007" in word_eol[0]:
        hexchat.command("recv {}".format(word_eol[0].replace(
            "\007", "\\007")))
        return hexchat.EAT_ALL


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "plugin unloaded")

hexchat.hook_server("RAW LINE", remove)
print(__module_name__, "plugin loaded")
