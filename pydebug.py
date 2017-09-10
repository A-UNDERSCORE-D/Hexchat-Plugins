import hexchat
import traceback
import sys
import threading

__module_name__ = "pydebug"
__module_version__ = "0.1"
__module_description__ = ""


# Stolen from cloudbot
def get_thread_dump():
    code = []
    threads = [(get_name(thread_id), traceback.extract_stack(stack))
               for thread_id, stack in sys._current_frames().items()]
    for thread_name, stack in threads:
        code.append("# {}".format(thread_name))
        for filename, line_num, name, line in stack:
            code.append("{}:{} - {}".format(filename, line_num, name))
            if line:
                code.append("    {}".format(line.strip()))
        code.append("")  # new line

    return "\n".join(code)


def get_name(thread_id):
    current_thread = threading.current_thread()
    if thread_id == current_thread._ident:
        is_current = True
        thread = current_thread
    else:
        is_current = False
        thread = threading._active.get(thread_id)

    if thread is not None:
        if thread.name is not None:
            name = thread.name
        else:
            name = "Unnamed thread"
    else:
        name = "Unknown thread"

    name = "{} ({})".format(name, thread_id)
    if is_current:
        name += " - Current thread"

    return name


def command_cb(word, word_eol, userdata):
    print(get_thread_dump())


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")

hexchat.hook_command("PYDEBUG", command_cb)

print(__module_name__, "loaded")
