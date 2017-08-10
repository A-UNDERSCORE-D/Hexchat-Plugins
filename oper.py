import hexchat
import random
from pprint import pprint
__module_name__ = "adoper"
__module_description__ = "Aliases to OperServ commands that I use often"
__module_version__ = "0.5"

kills_text = [
    "Roy Mustang puts on his ignition gloves and clicks his fingers in your direction. FWOOSH!",
    "It's a terrible day for rain.",
    "Here, have my axe.",
    "Hold this for me?",
    "Hey! catch!",
    "Have You Really Been Far Even as Decided to Use Even Go Want to do Look More Like?",
    "/okill",
    "Here, I'm going to let you hold my axe for a second... oops, seems it was too powerful",
    "Here, I'm going to let you hold my axe for a second... oops, seems I dropped instead",
    "Here, I'm going to let you hold my axe for a second... oops, seems you are too weak to wield such things",
    "Here, I'm going to let you hold my axe for a second...",
    ""
]

kills_images = [
    "http://i.imgur.com/O3DHIA5.gif",
    "http://i.imgur.com/A4XPmWT.gif",
]

kills = kills_text * 2 + kills_images


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


def printkills(word, word_eol, userdata):
    pprint(kills)


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "plugin unloaded")

hexchat.hook_command("okill", kill)
hexchat.hook_command("printkills", printkills)

print(__module_name__, "plugin loaded")
