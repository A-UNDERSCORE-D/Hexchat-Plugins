import subprocess
import hexchat

__module_name__ = "adnowplaying"
__module_version__ = "1.0"
__module_description__ = "grabs nowplaying from deadbeef"


def nowplaying(word, word_eol, userdata):
    args = ["/opt/deadbeef/bin/deadbeef", "--nowplaying-tf",
            "\"%artist%\" - \"%title%\" on \"%album%\" "
            "(%codec% at %bitrate%kb/s - %filesize_natural%)"]
    np = subprocess.Popen(args, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL).communicate()[0].decode()
    hexchat.command("me is now playing {}".format(np))
    return hexchat.EAT_ALL


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "plugin unloaded")

hexchat.hook_command("DEADBEEF", nowplaying)

print(__module_name__, "plugin loaded")
