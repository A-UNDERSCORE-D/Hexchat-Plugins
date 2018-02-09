import re
from fnmatch import fnmatch, fnmatchcase
from pathlib import Path

import hexchat

__module_name__ = "BetterPing"
__module_version__ = "0.1"
__module_description__ = ""

config = None
conf_dir = Path(hexchat.get_info("configdir")).resolve() / "adconfig"
conf_dir.mkdir(exist_ok=True)
conf_file = conf_dir / "betterping.json"

checkers = set()


class Checker:
    def __init__(self, check_str):
        self.str = check_str
        self.type = "contains"

    def check(self, str_to_check):
        return self.str in str_to_check

    def __str__(self):
        return "{}:{}".format(self.type, self.str)


class RegexChecker(Checker):
    def __init__(self, check_str, full_match=False, case_sensitive=False):
        super().__init__(check_str)
        self.full_match = full_match
        self.case_sensitive = case_sensitive
        self.flags = re.IGNORECASE if not case_sensitive else 0
        self.type = "regex:{}".format("cs" if case_sensitive else "ci")
        try:
            self.regexp = re.compile(self.str, self.flags)
        except re.error as e:
            print("Regex compilation error: {}".format(e))
            raise

    def check(self, str_to_check):
        if self.full_match:
            match = self.regexp.fullmatch(str_to_check)
        else:
            match = self.regexp.match(str_to_check)
        return match is not None


class GlobChecker(Checker):
    def __init__(self, check_str, case_sensitive=False):
        super().__init__(check_str)
        self.case = case_sensitive
        self.type = "glob:{}".format("ci" if not case_sensitive else "cs")

    def check(self, str_to_check):
        if self.case:
            return fnmatchcase(str_to_check, self.str)
        return fnmatch(str_to_check, self.str)


def getconfig():
    ...


@hexchat.hook_unload
def onunload(userdata):
    print(__module_name__, "unloaded")


print(__module_name__, "loaded")
