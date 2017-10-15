import hexchat
import time

__module_name__ = "addfilter"
__module_version__ = "0.1"
__module_description__ = "some wrapping to add standardised filter reasons"


def addfilter(word, word_eol, userdata):
    hexchat.command("FILTER {command} ({time_str})".format(
        command=word_eol[1],
        time_str=time.strftime(
            "%Y-%m-%d %H:%M:%S", time.gmtime()
        )
    ))


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")


hexchat.hook_command("ADDFILTER", addfilter)

print(__module_name__, "loaded")
