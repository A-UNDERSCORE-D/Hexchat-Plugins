import hexchat

__module_name__ = "ados"
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


# this bans multiple people in a list and kick them after the mode is set
def massban(word, word_eol, userdata):
    mlist = []
    if len(word) < 2:
        print("I need an argument")
    else:
        ulist = hexchat.get_list("users")
        nlist = word[1:]
        lword = len(word) - 1

        for user in ulist:
            for nick in nlist:
                if user.nick == nick:
                    mask = user.host
                    mask = mask.split("@")
                    mlist.append("*!*@" + mask[1])

        modelist = "b" * len(mlist)
        hexchat.command(
            "QUOTE MODE {} +{} {}".format(hexchat.get_info("channel"),
                                          modelist, " ".join(mlist)))
        masskick(word, word_eol, userdata)
    return hexchat.EAT_ALL


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "Plugin Unloaded")

# hooks for commands stored below
hexchat.hook_command("FUCKOFF", masskick)
hexchat.hook_command("mban", massban)
print(__module_name__, "Plugin Loaded")
