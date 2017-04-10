import hexchat
import re
from threading import Thread
from subprocess import run as runprocess
import sys
import os
sys.path = [os.path.join(hexchat.get_info("configdir"), "addons")] + sys.path
from adhexlib import pref
from adhexlib import context as con

__module_name__ = "adsnomasksDEV"
__module_description__ = "Sorts inspircd snotices into different queries, and sends specific ones to notify-send"
__module_version__ = "2.0"

whoisregex = r"(\*\*\*\s(?:[^\s]+))\s\([^@]+@[^)]+\)\s(did\sa\s/whois\son\syou)"
snoteregex = r"\*\*\*\s(:?REMOTE)?{}?:.*?$"

# TODO: update plugin prefs when changing rather than querying each time

snotes = {
    "S-Kills": "KILL",
    "S-Xlines": "XLINE",
    "S-Opers": "OPER",
    "S-Announcements": "ANNOUNCEMENT",
    "S-Globops": "GLOBOPS",
    "S-Operlogs": "OPERLOG",
    "S-Joins": "(JOIN|PART)",
    "S-Connects": "(CONNECT|QUIT)",
    "S-Floods": "FLOOD",
    "S-Nicks": "NICK",
    "S-Chans": "CHANCREATE",
    "S-Links": "LINK",
    "S-Operov": "SNO-v",
    "S-Stats": "STATS",
    "S-Debug": "DEBUG"
}

allowednets = pref.getpref(__module_name__ + "_allowednetworks")
ftsnotices = pref.getpref(__module_name__ + "_forwardtosnotices")
sendvisual = pref.getpref(__module_name__ + "_sendvisual")


def onsnotice(word, word_eol, userdata):
    notice = word[1]
    if hexchat.get_info("network").lower() in allowednets:
        for mask in snotes:
            if re.match(snoteregex.format(snotes[mask]), notice):
                con.printtocontext(">>{}<<".format(mask), notice)
                if mask in ftsnotices:
                    con.printtocontext(">>S-Notices<<", notice)
                if mask in sendvisual:
                    sendnotif(notice)

        whois = re.match(whoisregex, notice)
        if whois:
            sendwhoisnotice(whois)


def sendwhoisnotice(msg):
    hexchat.command("RECV :whois!whois@whois NOTICE {mynick} :{nmsg}".format(mynick=hexchat.get_info("nick"),
                                                                             nmsg=" ".join(msg.groups())))


def sendnotif(msg):
    matched = re.match(r"(\*\*\*\s(?:REMOTE)?.+?:)?\s(:?From\s.+?:)?.+?$", msg).groups()
    Thread(target=lambda: runprocess(["notify-send", "-i", "hexchat", matched[0], matched[1]])).start()


def addnet(net):
    pref.setpref(__module_name__ + "_allowednetworks", net)
    global allowednets
    allowednets = pref.getpref(__module_name__ + "_allowednetworks")


def delnet(net):
    pref.removepref(__module_name__ + "_allowednetworks", net)
    global allowednets
    allowednets = pref.getpref(__module_name__ + "_allowednetworks")


def addvisual(snotice):
    pref.appendpref(__module_name__ + "_sendvisual", snotice)
    global sendvisual
    sendvisual = pref.getpref(__module_name__ + "_sendvisual")


def delvisual(snotice):
    pref.removepref(__module_name__ + "_sendvisual", snotice)
    global sendvisual
    sendvisual = pref.getpref(__module_name__ + "_sendvisual")


def addsnote(snotice):
    pref.appendpref(__module_name__ + "_forwardtosnotices", snotice)
    global ftsnotices
    ftsnotices = pref.getpref(__module_name__ + "_forwardtosnotices")


def delsnote(snotice):
    pref.removepref(__module_name__ + "_forwardtosnotices", snotice)
    global ftsnotices
    ftsnotices = pref.getpref(__module_name__ + "_forwardtosnotices")

commands = {
    "addnet": addnet,
    "delnet": delnet,
    "addvisual": addvisual,
    "delvisual": delvisual,
    "addsnote": addsnote,
    "delsnote": delsnote
}


def oncmd(word, word_eol, userdata):
    if word[1] in commands:
        commands[word[1]](word[2:])


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "plugin unloaded")

hexchat.hook_print("Server Notice", onsnotice)
print(__module_name__, "plugin loaded")
