import pickle
import re
from argparse import ArgumentParser
from collections import namedtuple
from fnmatch import fnmatch, fnmatchcase
from pathlib import Path
from typing import Dict

import hexchat

__module_name__ = "BetterPing"
__module_version__ = "0.1"
__module_description__ = ""

config = None
config_dir = Path(hexchat.get_info("configdir")).resolve() / "adconfig"
config_dir.mkdir(exist_ok=True)
config_file = config_dir / "betterping.pickle"

# TODO: check if a set is really the best idea here
checkers = set()


# TODO: Allow for blacklist/whitelist for networks and channels, possibly discretely
class Checker:
    def __init__(self, check_str, case_sensitive=False, networks=None, channels=None):
        self.str = check_str
        self.type = "contains"
        if networks is None:
            networks = []
        self.nets = networks

        if channels is None:
            channels = []
        self.chans = channels

        self.case_sensitive = case_sensitive

    def check(self, str_to_check):
        cur_chan = hexchat.get_info("channel")
        cur_net = hexchat.get_info("network")

        # TODO: This could cause slowdowns due to iteration. Could checking this once globally be better?
        if not any(net.casefold() == cur_net for net in self.nets) or not \
                any(chan.casefold() == cur_chan for chan in self.chans):
            return False

        return self._check(str_to_check)

    def _check(self, str_to_check):
        if self.case_sensitive:
            return self.str.casefold() in str_to_check.casefold()
        return self.str in str_to_check

    def __str__(self):
        return "{}:{}".format(self.type, self.str)


# TODO: Maybe do some sort of timeout on the compilation here?
class RegexChecker(Checker):
    def __init__(self, check_str, case_sensitive=False, networks=None, channels=None):
        super().__init__(check_str, case_sensitive, networks, channels)
        self.case_sensitive = case_sensitive
        self.flags = re.IGNORECASE if not case_sensitive else 0
        self.type = "regex:{}".format("cs" if case_sensitive else "ci")
        try:
            self.regexp = re.compile(self.str, self.flags)
        except re.error as e:
            print("Regex compilation error: {}".format(e))

    def _check(self, str_to_check):
        match = self.regexp.match(str_to_check)
        return match is not None


class GlobChecker(Checker):
    def __init__(self, check_str, case_sensitive=False, networks=None, channels=None):
        super().__init__(check_str, case_sensitive, networks, channels)
        self.case = case_sensitive
        self.type = "glob:{}".format("ci" if not case_sensitive else "cs")

    def _check(self, str_to_check):
        if self.case:
            return fnmatchcase(str_to_check, self.str)
        return fnmatch(str_to_check, self.str)


class ExactChecker(Checker):
    def __init__(self, check_str, case_sensitive=False, networks=None, channels=None):
        super().__init__(check_str, case_sensitive, networks, channels)
        self.type = "exact:{}".format("ci" if not case_sensitive else "cs")

    def _check(self, str_to_check):
        if self.case_sensitive:
            return self.str == str_to_check
        return self.str.casefold() == str_to_check.casefold()


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
def command(cmd, min_args=1, usage="{cmd} requires at least {count_args} arguments", subcommand=True, help_msg=""):
    cmd = cmd.upper()

    def _decorate(f):
        def _check_args(word, word_eol, userdata):
            if len(word) < min_args:
                print(usage.format(cmd=cmd, count_args=min_args))
                return hexchat.EAT_ALL

            ret = f(word, word_eol, userdata)
            if ret is not None:
                return hexchat.EAT_ALL

            return ret

        if not subcommand:
            hexchat.hook_command(cmd, _check_args)
        else:
            assert cmd not in commands, "{cmd} already exists in the command list".format(cmd=cmd)
            commands[cmd] = command_tuple(f, help_msg)
        return _check_args

    return _decorate


def parse_true_false(str_to_parse):
    str_to_parse = str_to_parse.casefold()
    if str_to_parse in ("yes", "y", "ok", "true", "t"):
        return True
    elif str_to_parse in ("no", "false", "n", "f"):
        return False


@command("ping", 2, subcommand=False)
def main_command(word, word_eol, userdata):
    # No need to check length because that is done for me, to a point, anyway
    cmd = word[1].upper()
    if cmd in commands:
        commands[cmd].func(word[1:], word_eol[1:], userdata)
    else:
        print("Unknown command {}, try /ping help for a list of commands".format(cmd))


def msg_hook(f):
    hexchat.hook_print("Channel Message", f, userdata="Channel Msg Highlight")
    hexchat.hook_print("Private Message", f)
    hexchat.hook_print("Private Message to Dialog", f)


@command("debug")
def debug_cb(word, word_eol, userdata):
    for checker in checkers:
        print(checker)


@command("help")
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
            print("{cmd:<10} | {help_text}".format(cmd=cmd, help_text=commands[cmd].help_text))


# type: Dict[str, Checker]
checker_types = {
    "REGEX": RegexChecker,
    "CONTAINS": Checker,
    "EXACT": ExactChecker,
    "GLOB": GlobChecker
}

# TODO: Continue implementing this
parser = ArgumentParser(
    prog="betterPing",
    description="Better word highlight support for hexchat"
)
parser.add_argument("type", help="The type of checker you want to use", type=str.upper)
parser.add_argument("phrase", help="The string which you want to be used to match a message", nargs="+")
parser.add_argument("-b", "--blacklist", help="set the channel and network lists to blacklists",
                    action="store_true", default=False)
parser.add_argument("-c", "--channels", help="Set the channels in the whitelist or blacklist for this checker",
                    nargs="*", default=[])
parser.add_argument("-n", "--networks", help="Set the channels in the whitelist or blacklist for this checker",
                    nargs="*", default=[])
parser.add_argument("-s", "--case-sensitive",
                    help="Set whether or not this checker will evaluate case when checking messages",
                    default=False, action="store_true")


# /ping addchecker type case_sensistive allowed_networks allowed_channels whitelist/blacklist string
@command("addchecker", 2)
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
        print("{} is an unknown checker type. available types are: {}")
        return

    #     def __init__(self, check_str, case_sensitive=False, networks=None, channels=None):
    checker = checker_types[args.type](
        check_str=args.phrase,
        case_sensitive=args.case_sensitive,
        networks=args.networks,
        channels=args.channels,
    )
    if checker is None:
        print("Error occurred while creating new checker {} with params {}".format(checker, args.phrase))
        return

    checkers.add(checker)


@command("delchecker", 2)
def del_cb(word, word_eol, userdata):
    checker_str = word[1]
    for checker in checkers:
        if checker_str == checker.str:
            checkers.remove(checker)
            return

    print("Checker {} not found in checker list".format(checker_str))


def on_msg(word, word_eol, userdata):
    emit = False
    for checker in checkers:
        if checker.check(word[1]):
            emit = True
            break

    if emit:
        hexchat.emit_print(userdata, *word)


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")


print(__module_name__, "loaded")
