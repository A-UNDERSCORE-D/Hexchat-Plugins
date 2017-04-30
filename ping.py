import hexchat
__module_name__ = "adping"
__module_version__ = "2.0"
__module_description__ = "writes pings and notices to an additional channel"


def incomingping(word, word_eol, userdata):
    hexchat.command("query -nofocus >>pings<<")
    con = hexchat.find_context(server=hexchat.get_info("network"),
                               channel=">>pings<<")
    con.emit_print("Channel Message", word[0], word[1],
                   "", "{}/".format(hexchat.get_info("channel")))
    return hexchat.EAT_NONE


def incomingaping(word, word_eol, userdata):
    hexchat.command("query -nofocus >>pings<<")
    con = hexchat.find_context(server=hexchat.get_info("network"),
                               channel=">>pings<<")
    con.emit_print("Channel Action", "{}/{}".format(
        hexchat.get_info("channel"), word[0]), word[1], "", "")
    return hexchat.EAT_NONE


def incomingnotice(word, word_eol, userdata):
    hexchat.command("query -nofocus >>notices<<")
    con = hexchat.find_context(server=hexchat.get_info("network"),
                               channel=">>notices<<")
    con.prnt("\00328-\00329{}\00328-\003\t{}".format(word[0], word[1]))
    return hexchat.EAT_NONE


def incomingwallops(word, word_eol, userdata):
    hexchat.command("query -nofocus >>wallops<<")
    con = hexchat.find_context(server=hexchat.get_info("network"),
                               channel=">>wallops<<")
    con.prnt("\00328-\00329{}/Wallops\00328-\003\t{}".format(word[0], word[1]))
    return hexchat.EAT_NONE


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "plugin unloaded")


hexchat.hook_print("Channel Msg Hilight", incomingping)
hexchat.hook_print("Channel Action Hilight", incomingaping)
hexchat.hook_print("Notice", incomingnotice)
hexchat.hook_print("Receive Wallops", incomingwallops)
print(__module_name__, "plugin loaded")
