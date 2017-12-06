import hexchat

__module_name__ = "adopscript"
__module_version__ = "1.0"
__module_description__ = "This script helps me in my endevours to destroy " \
                         "channels"


# this command runs a mass kick with a reason,
def masskick(word, word_eol, userdata):
    reason = "{}".format(hexchat.get_info("nick"))
    if len(word) < 2:
        print("I need an argument")
    else:
        reason = "No reason specified"
        i = 0
        for words in word:
            if words.startswith(":"):
                reason = " ".join(word[i:])
                reason = reason[1:]
                word = word[1:i]
                break
            i += 1
    for nicks in word:
        hexchat.command("QUOTE KICK {} {} :{}".format(
            hexchat.get_info("channel"), nicks, reason))
    return hexchat.EAT_ALL


def add_invite(word, word_eol, userdata):
    if len(word) < 2:
        hexchat.command("ECHO Not enough arguments")
        return hexchat.EAT_HEXCHAT
    nick = word[1]
    if word_eol[2].startswith("Account unknown"):
        print("Not adding {} as they do not have a known account".format(nick))
    else:
        hexchat.command("MODE +I R:{}".format(word[2]))


def menu_items(add=True):
    if add:
        hexchat.command("MENU ADD \"$NICK/Set Invite\" \"ADD_INVITE %s %u\"")
    else:
        hexchat.command("MENU DEL \"$NICK/Set Invite\"")


@hexchat.hook_unload
def onunload(userdata):
    menu_items(False)
    print(__module_name__, "Plugin Unloaded")


# hooks for commands stored below
hexchat.hook_command("FUCKOFF", masskick)
hexchat.hook_command("ADD_INVITE", add_invite)
menu_items(True)
print(__module_name__, "Plugin Loaded")
