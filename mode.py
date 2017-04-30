import hexchat

__module_name__ = "admode"
__module_description__ = "testing for mode forward"
__module_version__ = "1.0"


def modechange(word, word_eol, userdata):
    if hexchat.get_info("network").lower() == "snoonet":
        if "#" in word[2]:
            if len(word[3]) > 5:
                hexchat.command("query -nofocus >>modes<<")
                modecon = hexchat.find_context(None, ">>modes<<")
                modecon.emit_print("Raw Modes", "{}/{}".format(
                    word[0].split("!")[0][1:], word[2]), word_eol[3])
    return hexchat.EAT_NONE


@hexchat.hook_unload
def unload(userdata):
    print(__module_name__, "plugin unloaded")


hexchat.hook_server("MODE", modechange)
print(__module_name__, "plugin loaded")
