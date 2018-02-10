import re
from fnmatch import fnmatch, fnmatchcase
from pathlib import Path

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
# TODO: func to parse string based bools, y/n, yes/no, true/false, etc.


class Checker:
    def __init__(self, check_str, case_sensitive=False, networks=None, channels=None):
        self.str = check_str
        self.type = "contains"
        self.nets = networks
        self.chans = channels
        self.case_sensitive = case_sensitive

    def check(self, str_to_check):
        cur_chan = hexchat.get_info("channel")
        cur_net = hexchat.get_info("network")

        # TODO: This could cause slowdowns due to iteration. Could checking this once globally be better?
        if not (self.nets is not None and any((True for net in self.nets if net.casefold() == cur_net))):
            return False
        if not (self.chans is not None and any((True for chan in self.nets if chan.casefold() == cur_chan))):
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
    def __init__(self, check_str, case_sensitive=False, networks=None, channels=None, full_match=False):
        super().__init__(check_str, case_sensitive, networks, channels)
        self.full_match = full_match
        self.case_sensitive = case_sensitive
        self.flags = re.IGNORECASE if not case_sensitive else 0
        self.type = "regex:{}".format("cs" if case_sensitive else "ci")
        try:
            self.regexp = re.compile(self.str, self.flags)
        except re.error as e:
            print("Regex compilation error: {}".format(e))
            raise

    def _check(self, str_to_check):
        if self.full_match:
            match = self.regexp.fullmatch(str_to_check)
        else:
            match = self.regexp.match(str_to_check)
        return match is not None


class GlobChecker(Checker):
    def __init__(self, check_str, networks=None, channels=None, case_sensitive=False):
        super().__init__(check_str, case_sensitive, networks, channels)
        self.case = case_sensitive
        self.type = "glob:{}".format("ci" if not case_sensitive else "cs")

    def _check(self, str_to_check):
        if self.case:
            return fnmatchcase(str_to_check, self.str)
        return fnmatch(str_to_check, self.str)


class ExactChecker(Checker):
    def __init__(self, check_str, networks=None, channels=None, case_sensitive=False):
        super().__init__(check_str, case_sensitive, networks, channels)
        self.type = "exact:{}".format("ci" if not case_sensitive else "cs")

    def _check(self, str_to_check):
        if self.case_sensitive:
            return self.str == str_to_check
        return self.str.casefold() == str_to_check.casefold()


def saveconfig(conf=config):
    with config_file.open("w") as f:
        ...


def getconfig():
    if not config_file.exists():
        ...


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")


print(__module_name__, "loaded")
