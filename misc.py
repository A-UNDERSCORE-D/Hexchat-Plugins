import random

import hexchat

__module_name__ = "admisc"
__module_version__ = "1.0"
__module_description__ = "This script holds all my random things " \
                         "that don't fit anywhere else"

def poke(word, word_eol, userdata):
    pokes = ["with a stick", "with a twig"]
    innick = word[1]
    hexchat.command("me pokes {} {}".format(innick, random.choice(pokes)))
    return hexchat.EAT_ALL


def slap(word, word_eol, userdata):
    innick = word[1]
    inchan = hexchat.get_info("channel")
    inserver = hexchat.get_info("server")
    innetwork = hexchat.get_info("network")
    slaps = [
        "pokes {nick} with a tazer",
        "hurls the holy hand grenade of antioch at {nick}",
        "clears {nick}'s head with the help of a baseball bat",
        "applies a small amount of acid to {nick}",
        "begins to plot {nick}'s demise",
        "starts planning an accident for {nick}",
        "stores all of {nick}'s data on floppies next to an extremely "
        "strong magnet",
        "Throws a CRT monitor at {nick}",
        "sends all of {nick}'s usernames and passwords to {chan}",
        "drops a piano on {nick}",
        "drops a complete hardcopy log of {chan} on {nick}",
        "drops a 100EB NAS on {nick}",
        "drops {chan} on {nick}",
        "drops {nick} on {nick}",
        "shreds {nick}'s ram while their system is running",
        "slaps {nick} around with some soviet propaganda",
        "slaps {nick} with a sheet of {chan} propaganda",
        "drops the network on {nick}",
        "drops {network} on {nick}",
        "drops a server on {nick}",
        "drops {server} on {nick}",
        "causes a netsplit and blames {nick}",
        "splits out {server} and blames {nick}",
        "drops a planet on {nick}",
        "drops LV-426 on {nick}",
        "throws {nick} into a supermassive black hole",
        "throws {nick} into Sagittarius A*",
        "hits {nick} with a small moon",
        "covers {nick} in chlorine trifluoride, steps back and watches "
        "them burn",
        "drops {nick} into Mount Doom",
        "makes all {nick}'s messages be sent as WALLOPs",
        "makes all of {nick}'s messages be sent via WALLCHAN",
    ]
    hexchat.command("me {}".format(random.choice(slaps).format(nick=innick,
                                                               chan=inchan, server=inserver, network=innetwork)))
    return hexchat.EAT_ALL

def f_to_c(word, word_eol, userdata):
    if (len(word) < 2 and word[1] != "-o") or (len(word) < 3 and word[1] == "-o"):
        print("/ftoc requires a temprature to convert")
        return hexchat.EAT_ALL
    
    output = False
    if word[1] == "-o":
        output = True
    
    if output:
        hexchat.command(f"exec -o units 'tempF({word[2]})' tempC --one-line --verbose | perl -pe 's/\s+(.*)/\\1/'")
    else:
        hexchat.command(f"exec units 'tempF({word[1]})' tempC --one-line --verbose | perl -pe 's/\s+(.*)/\\1/'")
    return hexchat.EAT_ALL


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "plugin loaded")


hexchat.hook_command("poke", poke)
hexchat.hook_command("slap", slap)
hexchat.hook_command("ftoc", f_to_c)
print(__module_name__, "plugin loaded")
