import inspect
import json
import re
import subprocess
import time
from collections import OrderedDict
import hexchat
from pathlib import Path

__module_name__ = "adsnotices"
__module_description__ = "Sorts inspircd snotices into different queries, and sends specific ones to notify-send"
__module_version__ = "2.3"

whoisregex = re.compile(r"(\*\*\*\s(?:[^\s]+))\s\([^@]+@[^)]+\)\s(did\sa\s/whois\son\syou)")
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
allowcounterwhois_DEFAULT = True
highlight_DEFAULT = []

allowednets = allowednets_DEFAULT
sendvisual = sendvisual_DEFAULT
blockvisual = blockvisual_DEFAULT
whois_timeout = whois_timeout_DEFAULT
snote_timeout = snote_timeout_DEFAULT
snote_specific_timeout = snote_specific_timeout_DEFAULT
allowcounterwhois = allowcounterwhois_DEFAULT
highlight = highlight_DEFAULT
config_version = 1

conf_dir = Path(hexchat.get_info("configdir")).resolve() / "adconfig"
conf_dir.mkdir(exist_ok=True)
conf_file = conf_dir / "adsnotices.json"

snotes = {
    "S-Kills": re.compile(snoteregex.format("KILL")),
    "S-Xlines": re.compile(snoteregex.format("XLINE")),
    "S-Opers": re.compile(snoteregex.format("OPER")),
    "S-Announcements": re.compile(snoteregex.format("ANNOUNCEMENT")),
    "S-Globops": re.compile(snoteregex.format("GLOBOPS")),
    "S-Operlogs": re.compile(snoteregex.format("OPERLOG")),
    "S-Joins": re.compile(snoteregex.format("(JOIN|PART)")),
    "S-Connects": re.compile(snoteregex.format("(CONNECT|QUIT)")),
    "S-Floods": re.compile(snoteregex.format("FLOOD")),
    "S-Nicks": re.compile(snoteregex.format("NICK")),
    "S-Chans": re.compile(snoteregex.format("CHANCREATE")),
    "S-Links": re.compile(snoteregex.format("LINK")),
    "S-Operov": re.compile(snoteregex.format("SNO-v")),
    "S-Stats": re.compile(snoteregex.format("STATS")),
    "S-Debug": re.compile(snoteregex.format("DEBUG"))
}


def onsnotice(word, word_eol, userdata):
    notice = word[0]
    eat, is_not_whois, sent_to_ns = False, False, False
    if hexchat.get_info("network").lower() in allowednets:
        for mask in snotes:
            if snotes[mask].match(notice):
                printtocontext(">>{}<<".format(mask), notice)
                lowermask = mask.lower()
                if lowermask in sendvisual and checktimout(lowermask):
                    sendnotif(notice, lowermask)
                    sent_to_ns = True
                eat = True
                is_not_whois = True
                if checkhighlight(notice):
                    sendhighlightnotice(notice)
                break
        if not is_not_whois:
            whois = whoisregex.match(notice)
            if whois:
                sendwhoisnotice(whois)
                if allowcounterwhois:
                    counterwhois(whois.group(1).split()[1])

        if eat:
            return hexchat.EAT_ALL


def checkhighlight(snote):
    to_check = snote.lower()
    for phrase in highlight:
        if phrase.lower() in to_check:
            return True
    return False


def checktimout(lowermask):
    if lowermask in snote_timers:
        if (time.time() - snote_timers[lowermask]) >= snote_specific_timeout.get(lowermask, snote_timeout):
            snote_timers[lowermask] = time.time()
            return True
    elif lowermask not in snote_timers:
        snote_timers[lowermask] = time.time()
        return True
    return False


def sendwhoisnotice(msg):
    hexchat.command("RECV :whois!whois@whois NOTICE {mynick} :{nmsg}".format(mynick=hexchat.get_info("nick"),
                                                                             nmsg=" ".join(msg.groups())))


def sendhighlightnotice(msg):
    hexchat.command("RECV :highlight!hl@hl NOTICE {mynick} :{nmsg}".format(mynick=hexchat.get_info("nick"),
                                                                           nmsg=msg))


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


commands = OrderedDict()


def command(cmd, cmdargs="", cmdhelp=""):
    def _decorate(func):
        assert cmd not in commands
        if cmdhelp:
            commands[cmd] = (func, cmdargs, cmdhelp)
        return func

    return _decorate


@command("net", "[add|remove|list] network name",
         "Adds a network to the list of networks where this script will function")
def net(arg):
    args = arg.split()
    global allowednets
    if args[0] == "add":
        if len(args) > 1:
            allowednets.append(args[1].lower())
            saveconfig()
        else:
            "I require an argument"

    elif args[0] == "del":
        if len(args) > 1:
            if args[1] in allowednets:
                allowednets.remove(args[1].lower())
                saveconfig()
            else:
                print("{} is not in the allowed network list".format(args[1]))
        else:
            print("I require an argument")

    elif args[0] == "list":
        print("networks:", ", ".join(allowednets))
    else:
        print("unknown subcommand for net")


@command("visual", "[add|list|del] [snote]", "Adds an snotice to the list of snotes that are sent to notify-send")
def visual(arg):
    args = arg.split()
    cmd = args.pop(0).lower()
    snotice = " ".join(args)
    global sendvisual
    if cmd == "add":
        if snotice:
            sendvisual.append(snotice.lower())
            saveconfig()
            print("'{}' added to list".format(snotice))
        else:
            print("I require an argument")
    elif cmd == "del":
        if snotice:
            if snotice in sendvisual:
                sendvisual.remove(snotice)
                saveconfig()
                print("'{}' removed from list".format(snotice))
            else:
                print("{} is not in the list of visually send snotices".format(snotice))
        else:
            print("I require an argument")
    elif cmd == "list":
        print("Snotes that are sent visually:", ", ".join(sendvisual))
    else:
        print("unknown subcommand for visual")


@command("blockvisual", "snote, phrase",
         "Adds a phrase to the list of phrases that block a snote from being sent to notify-send. "
         "You can use 'all' as the snote to check all snotices for a given phrase.")
def cmdblockvisual(arg):
    args = arg.split()
    cmd = args.pop(0).lower()
    block = " ".join(args)
    global blockvisual
    if cmd == "add":
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
    if cmd == "del":
        if len(block.split()) >= 2:
            key, block = block.split(None, 1)
            key = key.lower()
            if key in blockvisual:
                blockvisual[key].remove(block)
                if not blockvisual[key]:
                    del blockvisual[key]
                saveconfig()
                print("'{}' removed from {}'s block list".format(key, block))
            else:
                print("{key} is not in the block visual list".format(key=key))
        else:
            print("I require an argument")

    else:
        for ntype in blockvisual:
            print(ntype + ";")
            for block in blockvisual[ntype]:
                print(" `'{}'".format(block))


@command("whoistimeout", "number", "sets the global whois timeout. This is the minimum time between counterwhoises "
                                   "for a given user in seconds (fractions of a second are supported)")
def cmdwhoistimeout(arg):
    args = arg.split()
    cmd = args.pop(0)
    if cmd == "set":
        if len(args) > 0:
            global whois_timeout
            whois_timeout = float(args[0])
            saveconfig()
            print("whois timeout set to {}".format(whois_timeout))
        else:
            print("I need an argument")

    else:
        print("Whois timeout is: {}".format(whois_timeout))


@command("snotetimeout", "number",
         "Sets the global snotice timeout. This sets the minimum time between calls of notify-send in seconds "
         "(fractions of a second are supported)")
def cmdsnotetimeout(arg):
    args = arg.split()
    cmd = args.pop(0)
    if cmd == "set":
        if len(args) > 0:
            global snote_timeout
            snote_timeout = float(args[0])
            saveconfig()
            print("snote timeout set to {}".format(snote_timeout))
        else:
            print("I need an argument")

    else:
        print("Snote timeout is: {}".format(snote_timeout))


@command("specifictimeout", "snote, timeout",
         "Adds overriding timeouts for a given snotice, these are used instead of the global one")
def specifictimeout(arg):
    args = arg.split()
    cmd = args.pop(0)
    if cmd == "set":
        if len(args) > 1:
            timeout = " ".join(args).lower()
            split = timeout.split()
            snote_specific_timeout[split[0]] = float(split[1])
            print("{}'s timeout set to {}".format(split[0], split[1]))
            saveconfig()
        else:
            print("I need an argument")
    elif cmd == "del":
        if len(args) > 1:
            timeout = " ".join(args).lower()
            split = timeout.split()
            if split[0] in snote_specific_timeout:
                del snote_specific_timeout[split[0]]
                saveconfig()
                print("{}'s specific timeout has been removed".format(split[0]))
    else:
        if snote_specific_timeout:
            print("Specific Snote Timeouts are as follows:")
            for k, v in snote_specific_timeout.items():
                print(k + ":", v)
        else:
            print("You have set no specific snote timeouts")


@command("help", cmdhelp="Shows help")
def commandhelp():
    printfmt = "{cmd}\t {args:<15} | {desc:<50}"
    print("{cmd:}\t {args:^15} | {desc:^50}".format(cmd="\x02Command\x02", args="Args", desc="Description"))
    print("-" * 110)
    for cmdname in commands:
        cmd = commands[cmdname]
        cmdargs = cmd[1] if cmd[1] else "None"
        cmdhelp = cmd[2] if cmd[2] else "No description provided"
        cmdprint = "\x02" + cmdname + "\x02"
        print(printfmt.format(cmd=cmdprint, args=cmdargs, desc=cmdhelp))
        print("-" * 110)


@command("debug", cmdhelp="debug command, lists a few variables and their types")
def debug(args):
    def printconf():
        print("allowednets: {} type: {}".format(allowednets, type(allowednets)))
        print("sendvisual: {} type: {}".format(sendvisual, type(sendvisual)))
        print("blocksendvisual: {} type: {}".format(blockvisual, type(blockvisual)))
        print("whoistimeout: {} type: {}".format(whois_timeout, type(whois_timeout)))
        print("snotetimeout: {} type: {}".format(snote_timeout, type(snote_timeout)))
        print("snote timers: {} type: {}".format(snote_timers, type(snote_timers)))
        print("whois timers: {} type: {}".format(users, type(users)))
        print("specific timers: {} type {}".format(snote_specific_timeout, type(snote_specific_timeout)))
        print("config version: {}".format(config_version))
    if "all" in args:
        printconf()
        print("Commands: {}".format(commands))
    if "conf" in args:
        printconf()


@command("counterwhois", "Yes or no", "Sets whether or not to whois anyone whoising you")
def cmdallowcounterwhois(args):
    if isinstance(args, str):
        global allowcounterwhois
        if args.lower() in ("yes", "y", "true"):
            allowcounterwhois = True
            print("Counterwhoises will now be performed")
        if args.lower() in ("no", "n", "false"):
            allowcounterwhois = False
            print("Counterwhoises will no longer be performed")
        saveconfig()


@command("highlight", "phrase", "adds or removes a phrase to the snote highlight list")
def cmdhighlight(args):
    sargs = args.split(" ")
    if len(sargs) >= 1:
        cmd = sargs.pop(0)
        has_phrase = False
        phrase = None

        def add(ph):
            highlight.append(ph)
            saveconfig()
            print("added '{}' to the highlight list".format(ph))

        if len(sargs) >= 1:
            has_phrase = True
            phrase = " ".join(sargs)

        if cmd == "add" and has_phrase:
            add(phrase)
        elif cmd == "del" and has_phrase:
            phrase = " ".join(sargs)
            if phrase in highlight:
                highlight.remove(phrase)
                saveconfig()
                print("removed '{}' from the highlight list".format(phrase))
            else:
                print("'{}' not found in the highlight list".format(phrase))
        elif cmd in ("list", ""):
            print("Phrases in the highlight list")
            for phrase in highlight:
                print("`'{}'".format(phrase))

        # assume I want to add one.
        elif args != "":
            add(args)

    else:
        print("You must provide a subcommand and phrase")


@command("loadconf", "debug", "debug")
def lconf():
    getconfig()


def getconfig():
    def loadconfig():
        global allowednets, sendvisual, blockvisual, whois_timeout, snote_timeout, snote_specific_timeout, highlight
        global config_version
        allowednets = config.get("allowednets", allowednets_DEFAULT)
        sendvisual = config.get("sendvisual", sendvisual_DEFAULT)
        blockvisual = config.get("blockvisual", blockvisual_DEFAULT)
        whois_timeout = config.get("whoistimeout", whois_timeout_DEFAULT)
        snote_timeout = config.get("snotetimeout", snote_timeout_DEFAULT)
        snote_specific_timeout = config.get("snotespecific", snote_specific_timeout_DEFAULT)
        highlight = config.get("highlight", highlight_DEFAULT)
        config_version = config.get("conf_version", 1)

    if not conf_file.exists():
        ppref = hexchat.get_pluginpref(__module_name__ + "_config") or "[]"
        if ppref is not None:
            config = None
            try:
                config = json.loads(ppref)
            except (NameError, json.decoder.JSONDecodeError):
                print("An error occured while loading the adsnotices old config style. a default config will now be "
                      "loaded and saved using the new config system, your old config will now be printed to the screen "
                      "and removed.")
                print(ppref)

            if isinstance(config, dict):
                loadconfig()
        migrateconfig()

    with conf_file.open() as f:
        config = json.load(f)
        loadconfig()


def saveconfig():
    config = {
        "allowednets": allowednets,
        "sendvisual": sendvisual,
        "blockvisual": blockvisual,
        "whoistimeout": whois_timeout,
        "snotetimeout": snote_timeout,
        "snotespecific": snote_specific_timeout,
        "highlight": highlight,
        "conf_version": config_version
    }

    with conf_file.open(mode="w") as f:
        json.dump(config, f, indent=2)


def migrateconfig(del_old=True):
    saveconfig()
    if del_old:
        if not hexchat.del_pluginpref(__module_name__ + "_config"):
            print("An error occured while removing the old pluginpref")
    print("Migration complete")


def oncmd(word, word_eol, userdata):
    if len(word) >= 2:
        cmd = commands.get(word[1].lower())
        if cmd and cmd[0]:
            signature = inspect.signature(cmd[0])
            if len(signature.parameters) > 0:
                cmd[0](" ".join(word[2:]))
            else:
                cmd[0]()
        else:
            print("That is not a valid command, run '/SNOTE help' for information on syntax")
    else:
        hexchat.command("HELP SNOTE")
    return hexchat.EAT_HEXCHAT


def printtocontext(name, msg):
    context = hexchat.find_context(hexchat.get_info("network"), name)
    if not context:
        hexchat.command("QUERY -nofocus {}".format(name))
        context = hexchat.find_context(hexchat.get_info("network"), name)
    context.prnt(msg)


def menu_items(add=True):
    if add:
        hexchat.command("MENU ADD \"$NICK/Watch\" \"SNOTE highlight add %s\"")
    else:
        hexchat.command("MENU DEL \"$NICK/Watch\"")


@hexchat.hook_unload
def onunload(userdata):
    for child in children:
        if child.poll() is None:
            child.kill()
    menu_items(False)
    print(__module_name__, "plugin unloaded")


getconfig()
hexchat.hook_print("Server Notice", onsnotice)
hexchat.hook_command("SNOTE", oncmd, help="USAGE: for usage, run /snote help")
hexchat.hook_timer(15 * 1000, procleanup)
menu_items()

print(__module_name__, "plugin loaded")
