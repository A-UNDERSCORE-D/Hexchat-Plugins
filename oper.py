import hexchat
import random
__module_name__ = "adoper"
__module_description__ = "Aliases to OperServ commands that I use often"
__module_version__ = "0.5"

kills = [
    "Roy Mustang puts on his ignition gloves and clicks his fingers in your "
    "direction. FWOOSH!",
    "It's a terrible day for rain.",
    "Here, have my axe.",
    "Hold this for me?",
    "Hey! catch!",
    "http://i.imgur.com/O3DHIA5.gif",
    "http://i.imgur.com/A4XPmWT.gif",
]


def kill(word, word_eol, userdata):
    if len(word) < 2:
        print("I need an argument, /okill nick [reason]")
    elif len(word) == 2:
        hexchat.command(
            "msg OperServ KILL {nick} {reason}".format(
                nick=word[1], reason=random.choice(kills))
        )
    elif len(word) > 2:
        hexchat.command(
            "msg OperServ KILL {nick} {reason} \"{reason2}\"".format(
                nick=word[1], reason=word_eol[2], reason2=random.choice(kills))
        )
    return hexchat.EAT_ALL


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "plugin unloaded")

hexchat.hook_command("okill", kill)

print(__module_name__, "plugin loaded")
