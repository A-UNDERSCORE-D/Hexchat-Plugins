from typing import Any, List

import hexchat

__module_name__ = "opmsg_prefix"
__module_description__ = "Adds an indicator for channel messages to voice+"
__module_version__ = "0.0.1"

# This CAN be gotten dynamically from get_list('channels')[0].nickprefixes, HOWEVER, that channels list can be HUGE
# and colating it will take precious time away from the handler otherwise
prefixes = ('@', '%', "+")

# Unfortunately hexchat doesn't provide this information right in front. so lets do it the hard way.
# This may cause some slowdowns depending on message volume. However unloading the plugin instantly
# fixes that, and if it becomes too much of a problem, this can be reimplemented in C or lua
# The tl;dr for how this works is we just re-emit the line to the hexchat parsing engine with a note added


def on_privmsg(word: List[str], word_eol: List[str], userdata: Any) -> int:
    # Its a message from another user, thus it should always have a prefix. Test here and bail if not
    if word[0][0] != ':':
        return hexchat.EAT_NONE

    target = word[2]

    if target[0] == '#' or (len(target) >= 2 and target[1] != '#') or target[0] not in prefixes:
        return hexchat.EAT_NONE  # bail as fast as possible

    target_level = f'[{target[0]}]'
    msg = word_eol[3]
    if msg[0] == ':':
        msg = msg[1:]

    #                      :derg      PRIVMSG  #channel       [level] message
    hexchat.command(f'RECV {word[0]} {word[1]} {word[2][1:]} :{target_level} {msg}')

    return hexchat.EAT_ALL


# hexchat can be nasty with this.
m = __module_name__
v = __module_version__

hexchat.hook_server('PRIVMSG', on_privmsg)
print(f'{m} version {v} loaded')


hexchat.hook_unload(lambda _: print(f'unloading {m} version {v}'))  # type: ignore
