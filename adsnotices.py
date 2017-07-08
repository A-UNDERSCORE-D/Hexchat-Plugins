import json
import re
import subprocess
import time

import hexchat

__module_name__ = "adsnotices"
__module_description__ = "Sorts inspircd snotices into different queries, " \
                         "and sends specific ones to notify-send"
__module_version__ = "2.2"

whoisregex = re.compile(r"(\*\*\*\s(?:[^\s]+))\s\([^@]+@[^)]+\)"
                        r"\s(did\sa\s/whois\son\syou)")
snoteregex = r"\*\*\*\s(:?REMOTE)?{}?:.*?$"
users = {}
children = []
snote_timers = {}

allowednets_DEFAULT = []
sendvisual_DEFAULT = ['s-globops', 's-links', 's-announcements', 's-operov', 's-operlogs', 's-floods', 's-opers']
blockvisual_DEFAULT = {}
whois_timeout_DEFAULT = 180.0
snote_timeout_DEFAULT = 1.0
snote_specific_timeout_DEFAULT = {}


allowednets = allowednets_DEFAULT
sendvisual = sendvisual_DEFAULT
blockvisual = blockvisual_DEFAULT
whois_timeout = whois_timeout_DEFAULT
snote_timeout = snote_timeout_DEFAULT
snote_specific_timeout = snote_specific_timeout_DEFAULT

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


def onsnotice(word, word_eol, userdata):
    notice = word[0]
    eat = False
    if hexchat.get_info("network").lower() in allowednets:
        for mask in snotes:
            if re.match(snoteregex.format(snotes[mask]), notice):
                printtocontext(">>{}<<".format(mask), notice)
                lowermask = mask.lower()
                if lowermask in sendvisual:
                    if checktimout(lowermask):
                        sendnotif(notice, lowermask)

                eat = True

        whois = whoisregex.match(notice)
        if whois:
            sendwhoisnotice(whois)
            counterwhois(whois.group(1).split()[1])

        if eat:
            return hexchat.EAT_ALL


def checktimout(lowermask):
    if lowermask in snote_timers and (time.time() - snote_timers[lowermask]) >= snote_specific_timeout.get(lowermask, snote_timeout):
        snote_timers[lowermask] = time.time()
        return True
    elif lowermask not in snote_timers:
        snote_timers[lowermask] = time.time()
        return True
    return False


def sendwhoisnotice(msg):
    hexchat.command("RECV :whois!whois@whois NOTICE "
                    "{mynick} :{nmsg}".format(mynick=hexchat.get_info("nick"),
                                              nmsg=" ".join(msg.groups())))


def counterwhois(nick):
    if nick in users:
        if time.time() - users[nick] <= whois_timeout:
            users[nick] = time.time()
            return
    else:
        users[nick] = time.time()
    hexchat.command("WHOIS {0} {0}".format(nick))


def sendnotif(msg, ntype):
    smsg = msg.split()

    if "REMOTE" in msg:
        title = " ".join(smsg[1:4])
        body = " ".join(smsg[4:])
    elif smsg[1] == "GLOBOPS:":
        title = " ".join(smsg[1:4])
        body = " ".join(smsg[4:])
    else:
        title = smsg[1]
        body = " ".join(smsg[2:])

    def checkblock(iblock):
        return iblock.lower() in body.lower()

    if ntype in blockvisual:
        for block in blockvisual[ntype]:
            if checkblock(block):
                return

    if "all" in blockvisual:
        for block in blockvisual["all"]:
            if checkblock(block):
                return

    children.append(subprocess.Popen(
        ["notify-send", "-i", "hexchat", "--hint=int:transient:1",
         title.replace("\x02", ""), body.replace("\x02", "")]))


def procleanup(userdata):
    children[:] = [c for c in children if c.poll() is None]
    return True


def addnet(net):
    global allowednets
    allowednets.append(net)
    saveconfig()


def delnet(net):
    global allowednets
    if net in allowednets:
        allowednets.remove(net)
        saveconfig()
    else:
        print("{} is not in the allowed network list".format(net))


def addvisual(snotice):
    global sendvisual
    sendvisual.append(snotice.lower())
    saveconfig()


def delvisual(snotice):
    global sendvisual
    snotice = snotice.lower()
    if snotice in sendvisual:
        sendvisual.remove(snotice)
        saveconfig()
    else:
        print("{} is not in the list of visually send snotices".format(snotice))


def addblockvisual(block):
    global blockvisual
    if len(block.split()) >= 2:
        key, block = block.split(None, 1)
        key = key.lower()
        if key in blockvisual:
            if block in blockvisual[key]:
                print("'{}' is already in {}'s block list", block, key)
            else:
                blockvisual[key].append(block)
                saveconfig()
                print("'{}' added to {}'s block list".format(block, key))
        else:
            blockvisual[key] = [block]
            saveconfig()
            print("'{}' added to {}'s block list".format(block, key))
    else:
        print("I require an argument")
        return


def delblockvisual(block):
    global blockvisual
    if len(block.split()) >= 2:
        key, block = block.split(None, 1)
        key = key.lower()
        if key in blockvisual:
            blockvisual[key].remove(block)
            if not blockvisual[key]:
                del blockvisual[key]
            saveconfig()
            print("'{}' added to {}'s block list".format(key, block))
        else:
            print("{key} is not in the block visual list".format(key=key))
    else:
        print("I require an argument")
        return


def listblockvisual(*args, **kwargs):
    print("Strings blocked in snotices:")
    for ntype in blockvisual:
        print(ntype, ";")
        for block in blockvisual[ntype]:
            print(" `", block)


def setwhoistimeout(timeout):
    global whois_timeout
    whois_timeout = float(timeout)
    saveconfig()
    print("whois timeout set to {}".format(whois_timeout))


def setsnotetimeout(timeout):
    global snote_timeout
    snote_timeout = float(timeout)
    saveconfig()
    print("snote timeout set to {}".format(snote_timeout))


def addspecifictimeout(timeout):
    timeout = timeout.lower()
    split = timeout.split()
    if len(split) >= 2:
        snote_specific_timeout[split[0]] = float(split[1])
        print("{}'s timeout set to {}".format(split[0], split[1]))
        saveconfig()


def delspecifictimeout(timeout):
    timeout = timeout.lower()
    split = timeout.split()
    if split[0] in snote_specific_timeout:
        del snote_specific_timeout[split[0]]
        saveconfig()
        print("{}'s specific timeout has been removed".format(split[0]))


def getconfig():
    config = json.loads(hexchat.get_pluginpref(__module_name__ + "_config") or "[]")
    global allowednets, sendvisual, blockvisual, whois_timeout, snote_timeout, snote_specific_timeout
    if isinstance(config, dict):
        allowednets = config.get("allowednets", allowednets_DEFAULT)
        sendvisual = config.get("sendvisual", sendvisual_DEFAULT)
        blockvisual = config.get("blockvisual", blockvisual_DEFAULT)
        whois_timeout = config.get("whoistimeout", whois_timeout_DEFAULT)
        snote_timeout = config.get("snotetimeout", snote_timeout_DEFAULT)
        snote_specific_timeout = config.get("snotespecific", snote_specific_timeout_DEFAULT)
    else:
        saveconfig()


def saveconfig():
    config = {
        "allowednets": allowednets,
        "sendvisual": sendvisual,
        "blockvisual": blockvisual,
        "whoistimeout": whois_timeout,
        "snotetimeout": snote_timeout,
        "snotespecific": snote_specific_timeout
    }
    hexchat.set_pluginpref(__module_name__ + "_config", json.dumps(config))


def debug(*args):
    print("allowednets: {} type: {}".format(allowednets, type(allowednets)))
    print("sendvisual: {} type: {}".format(sendvisual, type(sendvisual)))
    print("blocksendvisual: {} type: {}".format(blockvisual, type(blockvisual)))
    print("whoistimeout: {} type: {}".format(whois_timeout, type(whois_timeout)))
    print("snotetimeout: {} type: {}".format(snote_timeout, type(snote_timeout)))
    print("snote timers: {} type: {}".format(snote_timers, type(snote_timers)))
    print("whois timers: {} type: {}".format(users, type(users)))
    print("specific timers: {} type {}".format(snote_specific_timeout, type(snote_specific_timeout)))


commands = {
    "addnet": addnet,
    "delnet": delnet,
    "listnet": lambda x: print("networks:", ", ".join(allowednets)),

    "addvisual": addvisual,
    "delvisual": delvisual,
    "listvisual": lambda x: print("Snotes that are sent visually:", ", ".join(sendvisual)),

    "addblockvisual": addblockvisual,
    "delblockvisual": delblockvisual,
    "listblockvisual": listblockvisual,
    "debug": debug,
    "setwhoistimeout": setwhoistimeout,
    "listwhoistimeout": lambda x: print("Whois timeout is: {}".format(whois_timeout)),
    "setsnotetimeout": setsnotetimeout,
    "listsnotetimeout": lambda x: print("Snote timeout is: {}".format(snote_timeout)),
    "setspecifictimeout": addspecifictimeout,
    "delspecifictimeout": delspecifictimeout,
}


def oncmd(word, word_eol, userdata):
    if len(word) < 2:
        hexchat.command("HELP SNOTE")
    elif word[1].lower() in commands:
        commands[word[1]]((" ".join(word[2:]) if len(word) >= 3 else None))
    else:
        hexchat.command("HELP SNOTE")
    return hexchat.EAT_ALL


def printtocontext(name, msg):
    context = hexchat.find_context(hexchat.get_info("network"), name)
    if not context:
        hexchat.command("QUERY -nofocus {}".format(name))
        context = hexchat.find_context(hexchat.get_info("network"), name)
    context.prnt(msg)


@hexchat.hook_unload
def onunload(userdata):
    for child in children:
        if child.poll() is None:
            child.kill()
    print(__module_name__, "plugin unloaded")


getconfig()
hexchat.hook_print("Server Notice", onsnotice)
hexchat.hook_command("SNOTE", oncmd, help="USAGE: /SNOTE ADD/DEL/LIST "
                                          "NET|VISUAL|BLOCKVISUAL")
hexchat.hook_timer(15 * 1000, procleanup)
print(__module_name__, "plugin loaded")
