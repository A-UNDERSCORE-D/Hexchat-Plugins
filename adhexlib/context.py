import hexchat


def printtocontext(name, msg):
    if hexchat.find_context(hexchat.get_info("network"), name):
        hexchat.find_context(hexchat.get_info("network"), name).prnt(msg)
    else:
        hexchat.command("QUERY -nofocus {}".format(name))
        hexchat.find_context(hexchat.get_info("network"), name).prnt(msg)
