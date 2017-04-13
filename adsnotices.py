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
blockvisual = pref.getpref(__module_name__ + "_blockvisual", "|")


def onsnotice(word, word_eol, userdata):
    notice = word[0]
    eat = False
    if hexchat.get_info("network").lower() in allowednets:
        for mask in snotes:
            if re.match(snoteregex.format(snotes[mask]), notice):
                con.printtocontext(">>{}<<".format(mask), notice)
                if mask in ftsnotices:
                    con.printtocontext(">>S-Notices<<", notice)
                if mask in sendvisual:
                    sendnotif(notice)
                eat = True

        whois = re.match(whoisregex, notice)
        if whois:
            sendwhoisnotice(whois)

        if eat:
            eat = False
            return hexchat.EAT_ALL


def sendwhoisnotice(msg):
    hexchat.command("RECV :whois!whois@whois NOTICE {mynick} :{nmsg}".format(mynick=hexchat.get_info("nick"),
                                                                             nmsg=" ".join(msg.groups())))


def sendnotif(msg):
    smsg = msg.split()
    title = ""
    body = ""

    if "REMOTE" in msg:
        title = " ".join(smsg[1:4])
        body = " ".join(smsg[4:])
    elif smsg[1] == "GLOBOPS:":
        title = " ".join(smsg[1:4])
        body = " ".join(smsg[4:])
    else:
        title = smsg[1]
        body = " ".join(smsg[2:])

    for block in blockvisual:
        if block.lower() in body.lower():
            return

    Thread(target=lambda: runprocess(["notify-send", "-i", "hexchat", title, body])).start()


def addnet(net):
    pref.appendprefunique(__module_name__ + "_allowednetworks", net)
    global allowednets
    allowednets = pref.getpref(__module_name__ + "_allowednetworks")


def delnet(net):
    pref.removepref(__module_name__ + "_allowednetworks", net)
    global allowednets
    allowednets = pref.getpref(__module_name__ + "_allowednetworks")


def addvisual(snotice):
    pref.appendprefunique(__module_name__ + "_sendvisual", snotice)
    global sendvisual
    sendvisual = pref.getpref(__module_name__ + "_sendvisual")


def delvisual(snotice):
    pref.removepref(__module_name__ + "_sendvisual", snotice)
    global sendvisual
    sendvisual = pref.getpref(__module_name__ + "_sendvisual")


def addblockvisual(block):
    blockstr = " ".join(block).lower()
    temp = pref.getpref(__module_name__ + "_blockvisual", "|")
    if blockstr not in temp:
        pref.setpref(__module_name__ + "_blockvisual", temp + [blockstr], "|")
        global blockvisual
        blockvisual = pref.getpref(__module_name__ + "_blockvisual", "|")
        print(blockstr, "Added to list")


def delblockvisual(block):
    blockstr = " ".join(block).lower()
    temp = pref.getpref(__module_name__ + "_blockvisual", "|")
    if blockstr in temp:
        temp.remove(blockstr)
        print(temp)
        pref.setpref(__module_name__ + "_blockvisual", temp, "|")
        global blockvisual
        blockvisual = pref.getpref(__module_name__ + "_blockvisual", "|")
    else:
        print(blockstr, "not found in the list")


def addsnote(snotice):
    pref.appendprefunique(__module_name__ + "_forwardtosnotices", snotice)
    global ftsnotices
    ftsnotices = pref.getpref(__module_name__ + "_forwardtosnotices")


def delsnote(snotice):
    pref.removepref(__module_name__ + "_forwardtosnotices", snotice)
    global ftsnotices
    ftsnotices = pref.getpref(__module_name__ + "_forwardtosnotices")

commands = {
    "addnet": addnet,
    "delnet": delnet,
    "listnet": lambda x: print("networks:", ", ".join(allowednets)),
    "addvisual": addvisual,
    "delvisual": delvisual,
    "listvisual": lambda x: print("Snotes that are sent visually:", ", ".join(sendvisual)),
    "addsnote": addsnote,
    "delsnote": delsnote,
    "listsnote": lambda x: print("Snotes forwarded to >>S-Notices<<:", " ,".join(ftsnotices)),
    "addblockvisual": addblockvisual,
    "delblockvisual": delblockvisual,
    "listblockvisual": lambda x: print("Strings that are blocked in visual snotes:", ", ".join(blockvisual))
}


def oncmd(word, word_eol, userdata):
    if len(word) < 2:
        hexchat.command("HELP SNOTE")
    elif word[1].lower() in commands:
        print((word[2:] if len(word) >= 3 else None))
        commands[word[1]]((word[2:] if len(word) >= 3 else None))
    return hexchat.EAT_ALL


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "plugin unloaded")

hexchat.hook_print("Server Notice", onsnotice)
hexchat.hook_command("SNOTE", oncmd, help="USAGE: /SNOTE ADD/DEL/LIST NET|VISUAL|SNOTE|BLOCKVISUAL")
print(__module_name__, "plugin loaded")
