import time
from collections import defaultdict
from typing import AnyStr, DefaultDict

import hexchat

__module_name__ = "join_flood"
__module_version__ = "0.1"
__module_description__ = "watches snotices for join floods and notifies the user"
MAX_JOINS = 10
JOIN_TIME = 10

HEAVY_CHANS = ["#chatsudcalifornianos"]
IGNORED_CHANS = ["#chatsudcalifornianos"]


class ChannelJoin:
    def __init__(self):
        self.last_join = 0
        self.join_count = 0

    def add_join(self, max_join):
        cur_time = time.time()
        if self.last_join - cur_time > JOIN_TIME:
            self.join_count = 1

        else:
            self.join_count += 1

        self.last_join = cur_time
        return self.check_joins(max_join)

    def check_joins(self, max_joins):
        return self.join_count > max_joins

    def reset(self):
        self.last_join = 0
        self.join_count = 0

    def __str__(self):
        return f"last: {self.last_join}, count: {self.join_count}"

    def __repr__(self):
        return f"ChannelJoin(last_join={self.last_join}, count={self.join_count})"


joins: DefaultDict[AnyStr, ChannelJoin] = defaultdict(ChannelJoin)


def on_snotice(word, word_eol, userdata, attrs):
    snote = word[0]
    split_snote = snote.split()
    cur_time = time.time()
    if len(split_snote) < 1 or split_snote[1][:-1] not in ("JOIN", "REMOTEJOIN"):
        return

    if attrs.time != 0 and cur_time - attrs.time > 10:
        print(
            f"Ignoring snote {snote!r} as there is a time discrepancy of more than ten seconds: {attrs.time - cur_time}"
        )

    joined_chan = split_snote[5]
    max_join = MAX_JOINS

    if joined_chan.lower() in IGNORED_CHANS:
        return

    if joined_chan.lower() in HEAVY_CHANS:
        max_join *= 3

    if joins[joined_chan].add_join(max_join):
        hexchat.command(
            f"RECV :JoinFlood!lol@no NOTICE {hexchat.get_info('nick')} :Join spam detected in {joined_chan}"
        )
        joins[joined_chan].reset()

    return hexchat.EAT_HEXCHAT


def debug(word, word_eol, userdata):
    for chan, join in joins.items():
        print(f"{chan}: {join}")

    print("End of join list")
    return hexchat.EAT_HEXCHAT


def cleanup(userdata):
    cur_time = time.time()
    to_del = set()
    for chan in joins:
        if cur_time - joins[chan].last_join > 60:
            to_del.add(chan)

    for chan in to_del:
        del joins[chan]

    return True


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")


hexchat.hook_print_attrs("Server Notice", on_snotice)
hexchat.hook_command("JOINFLOOD_DEBUG", debug)
hexchat.hook_timer(60*1000, cleanup)

print(__module_name__, "loaded")
