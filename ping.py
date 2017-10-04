import hexchat
__module_name__ = "adping"
__module_version__ = "2.1"
__module_description__ = "writes pings and notices to an additional channel"

WINDOW_FMT = ">>{name}<<"
emitting_notice = False
emitting_wallops = False
# TODO: make this use a pluginpref and default to True
use_emit_print = False  # Use emit print for notices an wallops


def get_window(name, server=None):
    name = WINDOW_FMT.format(name=name)
    if server is None:
        server = hexchat.get_info("network")
    ctx = hexchat.find_context(server=server, channel=name)
    if ctx is None:
        server_ctx = hexchat.find_context(server=server)
        server_ctx.command("query -nofocus {}".format(name))
        ctx = hexchat.find_context(server=server, channel=name)
    return ctx


def log_ping(event_type, nick, message, chan=None):
    if chan is None:
        chan = hexchat.get_info("channel")
    con = get_window("pings")
    source = "{}/{}".format(chan, nick)
    con.emit_print(event_type, source, message, "", "")


def ping_handler(event_type):
    def _handle(word, word_eol, userdata):
        log_ping(event_type, word[0], word[1])

    return _handle


def incomingnotice(word, word_eol, userdata):
    global emitting_notice
    if emitting_notice:
        return
    con = get_window("notices")
    emitting_notice = True
    if use_emit_print:
        con.emit_print("Notice", word[0], word[1])
    else:
        con.prnt("\x0328-\x0329{}\x0328-\x0F\t{}".format(word[0], word[1]))
    emitting_notice = False
    return hexchat.EAT_NONE


def incomingwallops(word, word_eol, userdata):
    global emitting_wallops
    if emitting_wallops:
        return
    con = get_window("wallops")
    emitting_wallops = True
    if use_emit_print:
        con.emit_print("Receive Wallops", word[0], word[1])
    else:
        con.prnt("\x0328-\x0329{}/Wallops\x0328-\x0F\t{}".format(word[0], word[1]))
    emitting_wallops = False
    return hexchat.EAT_NONE


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "plugin unloaded")


hexchat.hook_print("Channel Msg Hilight", ping_handler("Channel Message"))
hexchat.hook_print("Channel Action Hilight", ping_handler("Channel Action"))
hexchat.hook_print("Notice", incomingnotice)
hexchat.hook_print("Receive Wallops", incomingwallops)
print(__module_name__, "plugin loaded")

