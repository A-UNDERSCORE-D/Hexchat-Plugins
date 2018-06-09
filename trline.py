import re
from typing import List, Pattern, Tuple

import hexchat

__module_name__ = "trline"
__module_version__ = "0.1"
__module_description__ = "adds a command to test rlines"


class WhoReply:
    def __init__(self, who_entry: List[str]):
        self.channel = who_entry[3]
        self.ident = who_entry[4]
        self.host = who_entry[5]
        self.server = who_entry[6]
        self.nick = who_entry[7]
        self.realname = " ".join(who_entry[10:])

    def __str__(self):
        return self.rline_mask

    def __repr__(self):
        return f"WhoReply(channel='{self.channel}', ident='{self.ident}', host='{self.host}', server='{self.server}'," \
               f" nick='{self.nick}', realname='{self.realname}')"

    @property
    def rline_mask(self):
        return f"{self.nick}!{self.ident}@{self.host} {self.realname}"

    def test_rline(self, rline: Pattern):
        return rline.search(self.rline_mask) is not None


RPL_WHOREPLY, RPL_WHOEND = "352", "315"
running = False
hooks = [0, 0]


def on_who_reply(word, word_eol, userdata: Tuple[Pattern, 'hexchat.Context']):
    if not running:
        return hexchat.EAT_NONE
    entry = WhoReply(word)
    if userdata is None:
        raise ValueError("on_who_reply called with an unset rline")
    if entry.test_rline(userdata[0]):
        hexchat.command(f"ECHO '{entry}' matches {userdata[0].pattern}")


def on_who_end(word, word_eol, userdata):
    if word[3] == "0":
        global running
        running = False
        hexchat.unhook(hooks[0])
        hexchat.unhook(hooks[1])
        userdata.command("ECHO End of trline")


def trline(word, word_eol, userdata):
    if len(word) < 2:
        print("/trline requires an rline to test")
    global running
    to_compile = word[1]
    rline = re.compile(to_compile)
    running = True
    ctx = hexchat.get_context()
    hooks[0] = hexchat.hook_server(RPL_WHOREPLY, on_who_reply, (rline, ctx))
    hooks[1] = hexchat.hook_server(RPL_WHOEND, on_who_end, ctx)

    hexchat.command("WHO 0 uh")
    return hexchat.EAT_HEXCHAT


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")


hexchat.hook_command("trline", trline)

print(__module_name__, "loaded")
