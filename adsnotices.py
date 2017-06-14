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
                    sendnotif(notice)
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


def sendnotif(msg):
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

    for block in blockvisual:
        if block.lower() in body.lower():
            return

    subprocess.Popen(["notify-send", "-i", "hexchat", "--hint=int:transient:1",
                      title.replace("\x02", ""), body.replace("\x02", "")])


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
    blockvisual = appendpref("blockvisual", block)


def delblockvisual(block):
    global blockvisual
    blockvisual = removepref("blockvisual", block)

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
    "listblockvisual": lambda x: print(
        "Strings that are blocked in visual snotes:", "\"{}".format(
                                           "\", \"".join(blockvisual)) + "\"")
}


def oncmd(word, word_eol, userdata):
    if len(word) < 2:
        hexchat.command("HELP SNOTE")
    elif word[1].lower() in commands:
        commands[word[1]]((" ".join(word[2:]) if len(word) >= 3 else None))
    else:
        hexchat.command("HELP SNOTE")
    return hexchat.EAT_ALL


def getpref(name, default: list =[]):
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
        temp[key].append(data)
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
        if data in temp[key]:
            temp[key].remove(data)
        else:
            print("{} not found".format(data))
    return temp


allowednets = getpref("allowednetworks")
sendvisual = getpref("sendvisual",
                     ['S-Globops', 'S-Links', 'S-Announcements', 'S-Operov',
                      'S-OperLogs', 'S-Floods', 'S-Opers'])

blockvisual = getpref("blockvisual")


def printtocontext(name, msg):
    if hexchat.find_context(hexchat.get_info("network"), name):
        hexchat.find_context(hexchat.get_info("network"), name).prnt(msg)
    else:
        hexchat.command("QUERY -nofocus {}".format(name))
        hexchat.find_context(hexchat.get_info("network"), name).prnt(msg)


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "plugin unloaded")

hexchat.hook_print("Server Notice", onsnotice)
hexchat.hook_command("SNOTE", oncmd, help="USAGE: /SNOTE ADD/DEL/LIST "
                                          "NET|VISUAL|BLOCKVISUAL")
print(__module_name__, "plugin loaded")
