import hexchat
import random

__module_name__ = "adoper"
__module_description__ = "Aliases to OperServ commands that I use often"
__module_version__ = "0.5"

kills_text = [
    "Roy Mustang puts on his ignition gloves and clicks his fingers in your direction. FWOOSH!",
    "It's a terrible day for rain.",
    "Here, have my axe.",
    "Hold this for me?",
    "Hey! catch!",
    "Have You Really Been So Far Even as Decided to Use Even Go Want to do Look More Like?",
    "/okill",
    "Here, I'm going to let you hold my axe for a second... oops, seems it was too powerful",
    "Here, I'm going to let you hold my axe for a second... oops, seems I dropped instead",
    "Here, I'm going to let you hold my axe for a second... oops, seems you are too weak to wield such things",
    "Here, I'm going to let you hold my axe for a second...",
    "You are the weakest link. Goodbye. ;)",
    "Next time its Mr Sledgy the Network Banhammer"
]

kills_images = [
    "http://i.imgur.com/O3DHIA5.gif",
    "http://i.imgur.com/A4XPmWT.gif",
    "http://i.imgur.com/Mu3tJ6T.jpg",
    "https://i.imgur.com/R9WnseD.gif",
    "https://i.imgur.com/xn4rF.gif",
    "https://i.imgur.com/rnwF0.gif",
    "https://i.imgur.com/g2Yo3.gif",
    "https://i.imgur.com/Z3ha5dA.gif",
]

kills = kills_text * 2 + kills_images

MENU_ITEMS = frozenset({
    ("$NICK/Operator Actions/OS KILL", "OKILL %s")
})


def kill(word, word_eol, userdata):
    if len(word) < 2:
        print("I need an argument, /okill nick [reason]")
    elif len(word) == 2:
        hexchat.command("msg OperServ KILL {nick} {reason}".format(nick=word[1], reason=random.choice(kills)))
    elif len(word) > 2:
        hexchat.command(
            "msg OperServ KILL {nick} {reason}".format(nick=word[1], reason=word_eol[2]))
    return hexchat.EAT_ALL


def masskill(word, word_eol, userdata):
    for nick in word[1:]:
        hexchat.command("OKILL {}".format(nick))


def menu_items(add=True):
    for name, cmd in MENU_ITEMS:
        if add:
            hexchat.command("MENU ADD \"{}\" \"{}\"".format(name, cmd))
        else:
            hexchat.command("MENU DEL \"{}\"".format(name))


@hexchat.hook_unload
def onunload(userdata):
    menu_items(False)
    print(__module_name__, "plugin unloaded")


hexchat.hook_command("okill", kill)
hexchat.hook_command("omkill", masskill)
menu_items()

print(__module_name__, "plugin loaded")
