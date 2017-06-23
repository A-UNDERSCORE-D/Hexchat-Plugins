import hexchat
import re
import subprocess
import time
import json

__module_name__ = "adsnotices"
__module_description__ = "Sorts inspircd snotices into different queries, " \
                         "and sends specific ones to notify-send"
__module_version__ = "2.2"

whoisregex = re.compile(r"(\*\*\*\s(?:[^\s]+))\s\([^@]+@[^)]+\)"
                        r"\s(did\sa\s/whois\son\syou)")
snoteregex = r"\*\*\*\s(:?REMOTE)?{}?:.*?$"
TIMEOUT = 180 
users = {}
children = []

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
                if mask.lower() in sendvisual:
                    sendnotif(notice, mask.lower())
                eat = True

        whois = whoisregex.match(notice)
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
    allowednets = appendpref("allowednetworks", net)


def delnet(net):
    global allowednets
    allowednets = removepref("allowednetworks", net)


def addvisual(snotice):
    global sendvisual
    sendvisual = appendpref("sendvisual", snotice)


def delvisual(snotice):
    global sendvisual
    sendvisual = removepref("sendvisual", snotice)


def addblockvisual(block):
    global blockvisual
    if len(block.split()) >= 2:
        key, block = block.split(None, 1)
    else:
        print("I require an argument")
        return
    blockvisual = appendpref("blockvisual", block, key=key)
    # print("{phrase} added to {snote}".format(phrase=block, snote=key))


def delblockvisual(block):
    global blockvisual
    if len(block.split()) >= 2:
        key, block = block.split(None, 1)
    else:
        print("I require an argument")
        return
    blockvisual = removepref("blockvisual", block, key=key)
    # print("{phrase} removed from {snote}".format(phrase=block, snote=key))


def listblockvisual(*args, **kwargs):
    print("Strings blocked in snotices:")
    for ntype in blockvisual:
        print(ntype, ";")
        for block in blockvisual[ntype]:
            print(" `", block)

commands = {
    "addnet": addnet,
    "delnet": delnet,
    "listnet": lambda x: print("networks:", ", ".join(allowednets)),

    "addvisual": addvisual,
    "delvisual": delvisual,
    "listvisual": lambda x: print("Snotes that are sent visually:",
                                  ", ".join(sendvisual)),

    "addblockvisual": addblockvisual,
    "delblockvisual": delblockvisual,
    "listblockvisual": listblockvisual
}


def oncmd(word, word_eol, userdata):
    if len(word) < 2:
        hexchat.command("HELP SNOTE")
    elif word[1].lower() in commands:
        commands[word[1]]((" ".join(word[2:]) if len(word) >= 3 else None))
    else:
        hexchat.command("HELP SNOTE")
    return hexchat.EAT_ALL


def getpref(name, default=None):
    if default is None:
        default = []
    name = __module_name__ + "_" + name
    temp = hexchat.get_pluginpref(name)
    if not temp:
        hexchat.set_pluginpref(name, json.dumps(default))
    return json.loads(temp)


def setpref(name, data):
    name = __module_name__ + "_" + name
    data = json.dumps(data)
    hexchat.set_pluginpref(name, data)
    return data


def appendpref(name, data, key=None):
    temp = getpref(name)
    if isinstance(temp, list):
        temp.append(data)
    elif isinstance(temp, dict):
        if key in temp:
            temp[key].append(data)
        else:
            temp[key] = [data]
        print("{phrase} added to {snote}".format(phrase=data, snote=key))
    else:
        print("unknown data type")
    setpref(name, temp)
    return temp


def removepref(name, data, key=None):
    temp = getpref(name)
    if isinstance(temp, list):
        if data in temp:
            temp.remove(data)
            setpref(name, temp)
        else:
            print("{} not found".format(data))

    elif isinstance(temp, dict):
        if key in temp:
            if data in temp[key]:
                temp[key].remove(data)
                if not temp[key]:
                    del temp[key]
                setpref(name, temp)
                print("{phrase} removed from {snote}".format(phrase=data,
                                                             snote=key))
            else:
                print("{} not found in {}".format(data, key))
        else:
            print("{} not found".format(key))
    return temp


allowednets = getpref("allowednetworks")
sendvisual = getpref("sendvisual",
                     ['s-globops', 's-links', 's-announcements', 's-operov',
                      's-operlogs', 's-floods', 's-opers'])

blockvisual = getpref("blockvisual", {})


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

hexchat.hook_print("Server Notice", onsnotice)
hexchat.hook_command("SNOTE", oncmd, help="USAGE: /SNOTE ADD/DEL/LIST "
                                          "NET|VISUAL|BLOCKVISUAL")
hexchat.hook_timer(15 * 1000, procleanup)
print(__module_name__, "plugin loaded")
