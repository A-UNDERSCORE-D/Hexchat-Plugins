import re
from typing import Dict, List, NamedTuple, Pattern
import hexchat  # type: ignore # It exists PyLance, I promise
# spell-checker: words snote, xline, dnsbl, sacommand, sacommands, xlines, oper, SQUIT, opers
__module_name__ = "snote_forward"
__module_version__ = "2.1.3"
__module_description__ = ""


class SnoteMatcher(NamedTuple):
    type: str
    regexp: Pattern

    def matches(self, to_check: str) -> bool:
        return self.regexp.match(to_check) is not None


CATCHALL_NAME = "snote"
TRUNCATE_LENGTH = 10

spamfilter = SnoteMatcher('spamfilter', re.compile(r'^\*\*\* (?:Spamfilter added|\S+ removed Spamfilter).*$'))
squit = SnoteMatcher('squit', re.compile(r'^Received SQUIT .*'))
SNOTE_MATCHES: Dict[str, List[SnoteMatcher]] = {
    "xline": [
        SnoteMatcher('added/expired xline',
                     re.compile(r'^\*\*\*\s(Soft|Permanent|Expiring)?( Global)?\s?([QGZK]-Line|Exception).*$')),
        SnoteMatcher('removed xline', re.compile(r'^\*\*\* \S+ removed (Global )?([QGZK]-Line|[Ee]xception).*$')),
        spamfilter
    ],
    "connect": [
        SnoteMatcher('connect/disconnect', re.compile(r'^\*\*\* Client (?:connecting|exiting)')),
        SnoteMatcher('connflood', re.compile(r'^\*\*\* \[ConnThrottle\].*$'))
    ],
    "dnsbl": [SnoteMatcher('dnsbl', re.compile(r'^\[Blacklist\]'))],
    "sacommand": [
        SnoteMatcher('sacommands', re.compile(r'^\S+ used SA\S+.*$')),
        SnoteMatcher('oper override', re.compile(r'^\*\*\* OperOverride --.*$'))
    ],
    "spamfilter": [spamfilter, SnoteMatcher('spamfilter log', re.compile(r'^\[Spamfilter\].*$'))],
    "nicks": [
        SnoteMatcher('nick', re.compile(r'^\*\*\* \S+ \(\S+\) has changed their nickname to .*$')),
        SnoteMatcher('qlined', re.compile(r'^Q-Lined nick \S+ from .*$')),
        SnoteMatcher('Nick colission', re.compile(r'^Nick collision on.*$'))
    ],
    "chgstuff": [
        SnoteMatcher('chghost', re.compile(r'^\S+ changed the virtual hostname of.*$')),
        SnoteMatcher('chgident', re.compile(r'^\S+ changed the virtual ident of .* to be \S+$')),
        SnoteMatcher('chggecos', re.compile(r'^\S+ changed the GECOS of \S+.*to be.*$'))
    ],
    "rehash": [
        SnoteMatcher('local rehash', re.compile(r'^\*\*\* (?:Loading IRCd configuration|Configuration loaded)')),
        SnoteMatcher('rehash file', re.compile(r'^\S+ :Rehashing$')),
        SnoteMatcher('remote rehash', re.compile(r'^\S+ is remotely rehashing server \S+ config file$')),
    ],
    "kill": [SnoteMatcher('kill', re.compile(r'^\*\*\* Received KILL message for.*$'))],
    "flood": [SnoteMatcher('flood', re.compile(r'^Flood blocked.*$'))],
    'stats': [SnoteMatcher('stats', re.compile(r'^Stats \S+ requested by .*$'))],
    'squit': [squit],
    'opers': [
        SnoteMatcher('oper', re.compile(r'.* is now an operator$')),
        SnoteMatcher('failed oper', re.compile(r'^Failed OPER attempt by.*')),
        SnoteMatcher('insecure_oper', re.compile(r'OPER .* used an insecure (.*) connection to /OPER.'))
    ],
    'links': [
        squit,
        SnoteMatcher('link basic', re.compile(
            r'^(?:\*\*\* )?(?:\(link\)|ERROR from server|Lost server link to|Link|Network name mismatch|Trying to activate link with server)')),
        SnoteMatcher('lost link', re.compile(r'^No response.*closing link')),
        SnoteMatcher('ts issues', re.compile(r'^Possible negative TS split.*')),
        SnoteMatcher('ts issues', re.compile(
            r'^\*\*\* (Effective \(network-wide\)|Global link-security|More information).*$')),
        SnoteMatcher('Unable to link', re.compile(r'^Unable to link with server.*$')),
        SnoteMatcher('Module error', re.compile(r'^\[WARN\] Module marked.*$')),
        SnoteMatcher('banned server', re.compile(r'^Cancelling link.*'))
    ],
    'globops': [SnoteMatcher('globops', re.compile(r'^from \S+:.*$'))],
}


def handle_snote_2(word, word_eol, userdata):
    source: str = word[1]
    msg: str = word[0]
    msg_stripped: str = hexchat.strip(msg)
    matched_any = False
    for cat, matchers in SNOTE_MATCHES.items():
        if any(m.matches(msg_stripped) for m in matchers):
            formatted = f"\x0328-\x0329{source}\x0328-\x0F\t{msg[4:] if msg.startswith('*** ') else msg}"
            print_to_context(f'>>S-{cat}<<', formatted)
            matched_any = True

    if matched_any:
        return hexchat.EAT_HEXCHAT

    return hexchat.EAT_NONE


def print_to_context(name, msg):
    context = hexchat.find_context(hexchat.get_info("network"), name)
    if not context:
        hexchat.command("QUERY -nofocus {}".format(name))
        context = hexchat.find_context(hexchat.get_info("network"), name)

    context.prnt(msg)


try:
    file_name = __file__  # ... DONT REMOVE THIS SHIT HEXCHAT.
except NameError:
    file_name = "snote_forward.py"


hexchat.hook_print('Server Notice', handle_snote_2)
hexchat.hook_unload(lambda _: print(f"{file_name} version {__module_version__} unloaded"))
print(f"{file_name} version {__module_version__} loaded")
