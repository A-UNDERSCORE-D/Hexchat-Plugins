import hexchat
import uuid
__module_name__ = "opcmd"
__module_version__ = "1.0"
__module_description__ = "Runs a command when you are opped in a channel"

HOOKS = {}


def unhook(hid):
    hook = HOOKS.pop(hid, None)
    if hook is not None:
        hexchat.unhook(hook)
    return False


def cmd_cb(word, word_eol, userdata):
    if len(word) < 2:
        print("USAGE: /WHENIMOPPED <command to run after opped>")
        return hexchat.EAT_HEXCHAT
    cur_chan = hexchat.get_info("channel")
    cmd = word_eol[1]
    if cmd.startswith("/"):
        print("Stripping leading / from command")
        cmd = cmd[1:]
    print(f"Hooking `{cmd}` onto an op on {hexchat.get_info('nick')} in {cur_chan}. times out in 10 seconds")

    def on_op(w, w_eol, usrdata):
        print(userdata)
        if hexchat.get_info("channel") != cur_chan or w[1] != hexchat.get_info("nick"):
            return hexchat.EAT_NONE
        hexchat.command(cmd)
        unhook(usrdata)

    hid = uuid.uuid4()
    global HOOKS
    HOOKS[hid] = hexchat.hook_print("Channel Operator", on_op, hid)
    hexchat.hook_timer(5 * 1000, unhook, hid)

    return hexchat.EAT_HEXCHAT


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")


hexchat.hook_command("WHENIMOPPED", cmd_cb)
print(__module_name__, "loaded")
