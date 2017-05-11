import hexchat
import re
from threading import Thread
from subprocess import run as runprocess
import sys
import os
import time
sys.path = [os.path.join(hexchat.get_info("configdir"), "addons")] + sys.path
from adhexlib import pref
from adhexlib import context as con

__module_name__ = "adsnomasks"
__module_description__ = "Sorts inspircd snotices into different queries, " \
                         "and sends specific ones to notify-send"
__module_version__ = "2.1"

whoisregex = r"(\*\*\*\s(?:[^\s]+))\s\([^@]+@[^)]+\)\s" \
             r"(did\sa\s/whois\son\syou)"
snoteregex = r"\*\*\*\s(:?REMOTE)?{}?:.*?$"
TIMEOUT = 60
users = {}

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
            counterwhois(whois.group(1).split()[1])

        if eat:
            return hexchat.EAT_ALL


def sendwhoisnotice(msg):
    hexchat.command("RECV :whois!whois@whois NOTICE "
                    "{mynick} :{nmsg}".format(mynick=hexchat.get_info("nick"),
                                              nmsg=" ".join(msg.groups())))


def counterwhois(nick):
    if nick in users:
        if time.time() - users[nick] <= TIMEOUT:
            users[nick] = time.time()
            return
    else:
        users[nick] = time.time()
    hexchat.command("WHOIS {0} {0}".format(nick))


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

    Thread(target=lambda: runprocess(
        ["notify-send", "-i", "hexchat", "--hint=int:transient:1",
         title.replace("\x02", ""), body.replace("\x02", "")])
           ).start()


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


def addblockvisualtest(block):
    pref.appendpref(__module_name__ + "_blockvisual", block, "|")
    global blockvisual
    blockvisual = pref.getpref(__module_name__ + "_blockvisual", "|")


def delblockvisualtest(block):
    pref.removepref(__module_name__ + "_blockvisual", block, "|")
    global blockvisual
    blockvisual = pref.getpref(__module_name__ + "_blockvisual", "|")


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
    "listvisual": lambda x: print("Snotes that are sent visually:",
                                  ", ".join(sendvisual)),
    "addsnote": addsnote,
    "delsnote": delsnote,
    "listsnote": lambda x: print("Snotes forwarded to >>S-Notices<<:",
                                 " ,".join(ftsnotices)),
    "addblockvisual": addblockvisualtest,
    "delblockvisual": delblockvisualtest,
    "listblockvisual": lambda x: print(
        "Strings that are blocked in visual snotes: ", "\"{}".format(
                                           "\", \"".join(blockvisual)))
}


def oncmd(word, word_eol, userdata):
    if len(word) < 2:
        hexchat.command("HELP SNOTE")
    elif word[1].lower() in commands:
        commands[word[1]]((word[2:] if len(word) >= 3 else None))
    else:
        hexchat.command("HELP SNOTE")
    return hexchat.EAT_ALL


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "plugin unloaded")

hexchat.hook_print("Server Notice", onsnotice)
hexchat.hook_command("SNOTE", oncmd, help="USAGE: /SNOTE ADD/DEL/LIST "
                                          "NET|VISUAL|SNOTE|BLOCKVISUAL")
print(__module_name__, "plugin loaded")
