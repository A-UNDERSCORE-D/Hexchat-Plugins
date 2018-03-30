import pickle
import re
from abc import ABC, abstractmethod
from argparse import ArgumentParser
from collections import namedtuple
from fnmatch import fnmatch, fnmatchcase
from pathlib import Path
from typing import Dict, List

import hexchat

__module_name__ = "BetterPing"
__module_version__ = "1.1.3"
__module_description__ = ""

config = None
config_dir = Path(hexchat.get_info("configdir")).resolve() / "adconfig"
config_dir.mkdir(exist_ok=True)
config_file = config_dir / "betterping.pickle"

checkers = []


class ListOption:
    def __init__(self, entry: str, blacklist=False):
        self.entry = entry
        self.blacklist = blacklist

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"ListOption(entry='{self.entry}', blacklist={self.blacklist})"


# TODO: network/channel blacklist check cache
class AbstractChecker(ABC):
    def __init__(self, check_str, blacklist, case_sensitive, networks: List[ListOption] = None,
                 channels: List[ListOption] = None, negate=False):
        self.str = check_str
        if networks is None:
            networks = []
        self.networks = networks

        if channels is None:
            channels = []
        self.channels = channels

        self.case_sensitive = case_sensitive
        self.blacklist = blacklist
        self.negate = negate

    @staticmethod
    def check_list(to_check: str, list_to_check: List[ListOption]) -> bool:
        for list_entry in list_to_check:
            entry = list_entry.entry.casefold()
            if list_entry.blacklist and entry == to_check:
                return False
            elif entry == to_check:
                return True
        return False

    def check_networks(self, net_to_check: str = None):
        if net_to_check is None:
            net_to_check = hexchat.get_info("network")
        net_to_check = net_to_check.casefold()
        return self.check_list(net_to_check, self.networks)

    def check_channels(self, chan_to_check: str = None) -> bool:
        if chan_to_check is None:
            chan_to_check = hexchat.get_info("channel")
        chan_to_check = chan_to_check.casefold()
        return self.check_list(chan_to_check, self.channels)

    def check_ok(self):
        # There does not seem to be a way to find a channel's type without hexchat.get_list("channels")[0].type
        # Which seems rather slow, to be tested.
        return self.check_networks() and self.check_channels() and not hexchat.get_info("channel").startswith(">>")

    def check(self, str_to_check):
        # TODO: This could cause slowdowns due to iteration. Could checking this once globally be better?
        if not self.check_ok():
            return False
        if self.negate:
            return not self._check(str_to_check)
        return self._check(str_to_check)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"{self.type_str}(check_str='{self.str}', " \
               f"blacklist={self.blacklist}, case_sensitive={self.case_sensitive}, " \
               f"networks={self.networks}, channels={self.channels}, negate={self.negate})"

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__str__() == other.__str__()

    def compile(self) -> bool:
        if not self.case_sensitive:
            self.str = self.str.casefold()
        return True

    def __getstate__(self):
        return self.str, self.case_sensitive, self.blacklist, self.networks, self.channels, self.negate

    def __setstate__(self, state):
        self.str, self.case_sensitive, self.blacklist, self.networks, self.channels, self.negate = state
        if not self.compile():
            raise pickle.UnpicklingError("Checker {} failed to recompile".format(self))

    @abstractmethod
    def _check(self, str_to_check: str) -> bool:
        ...

    @property
    def type_str(self):
        return self.__class__.__name__


# TODO: Allow for blacklist/whitelist for networks and channels, possibly discretely
class ContainsChecker(AbstractChecker):
    def _check(self, str_to_check):
        if self.case_sensitive:
            return self.str.casefold() in str_to_check.casefold()
        return self.str in str_to_check


# TODO: Maybe do some sort of timeout on the compilation here?
class RegexChecker(AbstractChecker):
    def __init__(self, check_str, blacklist=True, case_sensitive=False, networks=None, channels=None, negate=False):
        super().__init__(
            check_str=check_str,
            blacklist=blacklist,
            case_sensitive=case_sensitive,
            networks=networks,
            channels=channels,
            negate=negate
        )
        self.flags = re.IGNORECASE if not case_sensitive else 0
        self.regexp = None

    def compile(self):
        try:
            self.regexp = re.compile(self.str, self.flags)
            return True
        except re.error as e:
            print("Regex compilation error: {}".format(e))
            return False

    def _check(self, str_to_check):
        if self.regexp is None:
            raise ValueError("RegexChecker._check() called while regexp is uncompiled")
        match = self.regexp.search(str_to_check)
        return match is not None

    def __getstate__(self):
        return self.str, self.case_sensitive, self.blacklist, self.nets, self.chans, self.negate, self.flags

    def __setstate__(self, state):
        self.str, self.case_sensitive, self.blacklist, self.nets, self.chans, self.negate, self.flags = state
        if not self.compile():
            raise pickle.UnpicklingError("Checker {} failed to recompile".format(self))


class GlobChecker(AbstractChecker):
    def __init__(self, check_str, blacklist=True, case_sensitive=False, networks=None, channels=None, negate=False):
        super().__init__(
            check_str=check_str,
            blacklist=blacklist,
            case_sensitive=case_sensitive,
            networks=networks,
            channels=channels,
            negate=negate
        )

    def _check(self, str_to_check):
        if self.case_sensitive:
            return fnmatchcase(str_to_check, self.str)
        return fnmatch(str_to_check, self.str)


class ExactChecker(AbstractChecker):
    def __init__(self, check_str, blacklist=True, case_sensitive=False, networks=None, channels=None, negate=False):
        super().__init__(
            check_str=check_str,
            blacklist=blacklist,
            case_sensitive=case_sensitive,
            networks=networks,
            channels=channels,
            negate=negate
        )

    def _check(self, str_to_check):
        if self.case_sensitive:
            return self.str == str_to_check
        return self.str == str_to_check.casefold()


def save_checkers():
    with config_file.open("wb") as f:
        pickle.dump(checkers, f)


def get_checkers():
    if not config_file.exists():
        return checkers
    with config_file.open("rb") as f:
        return pickle.load(f)


# Start of hexchat commands etc.
commands = {}
command_tuple = namedtuple("command_tuple", "func help_text")


# Because Im lazy and I think this helps readability. while removing repeated code
def command(cmd, min_args=1, usage="{cmd} requires at least {count_args} arguments", sub_command=True, help_msg=""):
    cmd = cmd.upper()

    def _decorate(f):
        def _check_args(word, word_eol, userdata):
            if len(word) < min_args:
                print(usage.format(cmd=cmd, count_args=min_args))
                return hexchat.EAT_ALL

            ret = f(word, word_eol, userdata)
            if ret is None:
                return hexchat.EAT_ALL

            return ret

        if not sub_command:
            hexchat.hook_command(cmd, _check_args)
        else:
            assert cmd not in commands, "{cmd} already exists in the command list".format(cmd=cmd)
            commands[cmd] = command_tuple(f, help_msg)
        return _check_args

    return _decorate


@command("bping", 2, sub_command=False)
def main_command(word, word_eol, userdata):
    # No need to check length because that is done for me, to a point, anyway
    cmd = word[1].upper()
    if cmd in commands:
        commands[cmd].func(word[1:], word_eol[1:], userdata)
    else:
        print("Unknown command {}, try /bping help for a list of commands".format(cmd))


def msg_hook(f):
    hexchat.hook_print("Channel Message", f, userdata="Channel Msg Hilight")
    hexchat.hook_print("Channel Action", f, userdata="Channel Action Hilight")


@command("debug", help_msg="Debug command used to print all currently loaded checkers")
def debug_cb(word, word_eol, userdata):
    if not checkers:
        print("There are no checkers currently loaded")
        return
    print("Checkers list is as follows:")
    for checker in checkers:
        print("{!r}".format(checker))


@command("help", help_msg="Prints this message")
def help_cb(word, word_eol, userdata):
    if len(word) > 1:
        cmd = word[1].upper()
        if cmd not in commands:
            print("Unknown command")
            return

        print("help for {command}: {help_text}".format(command=cmd, help_text=commands[cmd].help_text))

    else:
        print("Available commands:")
        for cmd in commands:
            print("{cmd}\t{help_text}".format(cmd=cmd, help_text=commands[cmd].help_text))


# type: Dict[str, ContainsChecker]
checker_types = {
    "REGEX": RegexChecker,
    "CONTAINS": ContainsChecker,
    "EXACT": ExactChecker,
    "GLOB": GlobChecker
}

# TODO: Continue implementing this
parser = ArgumentParser(
    prog="/bping addchecker",
    description="Better word highlight support for hexchat"
)
parser.add_argument("type", help="The type of checker you want to use", type=str.upper)
parser.add_argument("phrase", help="The string which you want to be used to match a message", nargs="+")
parser.add_argument("-b", "--blacklist", help="set the channel and network lists to blacklists",
                    action="store_false", default=True)
parser.add_argument("-c", "--channels", help="Set the channels in the whitelist or blacklist for this checker",
                    nargs="+", default=[])
parser.add_argument("-n", "--networks", help="Set the channels in the whitelist or blacklist for this checker",
                    nargs="+", default=[])
parser.add_argument("-s", "--case-sensitive",
                    help="Set whether or not this checker will evaluate case when checking messages",
                    default=False, action="store_true")
parser.add_argument("--negate", help="inverts a checker's string", default=False, action="store_true")


# /ping addchecker type case_sensistive allowed_networks allowed_channels whitelist/blacklist string
@command("addchecker", 2, help_msg="Adds a checker to the checker list, run /bping addchecker -h for options")
def add_cb(word, word_eol, userdata):
    try:
        args = parser.parse_args(word[1:])
    except SystemExit:
        # -h was used or bad args passed, either way, we have nothing more to do, but we must catch SystemExit, because
        # a SystemExit will close HexChat
        return
    # Convert 'phrase' from a list to a string, this way you can use spaces in a phrase, though you probably shouldn't
    # Use a regexp with \s instead because phrase 'test             test' will become 'test test'
    args.phrase = " ".join(args.phrase)
    if args.type not in checker_types:
        print("{} is an unknown checker type. available types are: {}".format(args.type, ",".join(checker_types)))
        return

    checker = checker_types[args.type](
        check_str=args.phrase,
        case_sensitive=args.case_sensitive,
        networks=args.networks,
        channels=args.channels,
        blacklist=args.blacklist,
        negate=args.negate
    )
    if not checker.compile():
        print("Error occurred while creating new checker {} with params {}".format(checker, args.phrase))
        return
    if checker in checkers:
        print("checker {} already exists in the checker list.".format(checker))
        return
    checkers.append(checker)
    save_checkers()
    print("Added checker {}".format(checker))


@command("delchecker", 2, help_msg="Deletes a checker from the checker list and saves changes to disk")
def del_cb(word, word_eol, userdata):
    checker_str = word_eol[1]
    for checker in checkers:
        if checker_str == checker.str:
            checkers.remove(checker)
            save_checkers()
            print("deleted checker {}".format(checker))
            return

    print("Checker {} not found in checker list".format(checker_str))


@command("manual_load", help_msg="Debug command used to force loading of checkers from disk")
def manual_load_cb(word, word_eol, userdata):
    global checkers
    print("Loading from disk")
    print("Current checkers: {}".format(checkers))
    checkers = get_checkers()
    print("New checkers: {}".format(checkers))


@command("manual_save", help_msg="Debug command used to force saving of checkers to disk")
def manual_save_cb(word, word_eol, userdata):
    print("Saving to disk")
    save_checkers()


@msg_hook
def on_msg(word, word_eol, userdata):
    if len(word) < 2:
        return hexchat.EAT_NONE
    msg = word[1]
    if any(checker.check(msg) for checker in checkers):
        word[0] = hexchat.strip(word[0])
        # Get the current context before emit_printing, because other plugins can change the current context
        ctx = hexchat.get_context()
        ctx.emit_print(userdata, *word)
        ctx.command("GUI COLOR 3")
        return hexchat.EAT_ALL


def onload():
    global checkers
    checkers = get_checkers()


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")


onload()
print(__module_name__, "loaded")
