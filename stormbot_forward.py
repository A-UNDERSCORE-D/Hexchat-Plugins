import hexchat

__module_name__ = "stormbot_forward"
__module_version__ = "1.0"
__module_description__ = "Forwards stormbot messages to relevant channels"

PREFIX = "[VPNCHECK]"


def on_msg(word, word_eol, userdata):
    if hexchat.get_info("channel").lower() != "##stormbot" or word[0].lower() != "stormbot":
        return

    # x is using a vpn (vpnname) in #chan
    chan = word[1].split()[0]
    hexchat.command(f"RECV :StormBot!bot@snoonet/utility/StormBot PRIVMSG {chan} :{word[1]}")


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")


hexchat.hook_print("Channel Message", on_msg)

print(__module_name__, "loaded")
