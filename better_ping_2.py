from __future__ import annotations

import argparse
import json
import pathlib
import re
import shlex
from abc import ABC, abstractmethod
from fnmatch import fnmatch, fnmatchcase
from typing import Any, Dict, List, NamedTuple, Optional

import hexchat

__module_name__ = 'better_ping_2'
__module_version__ = '0.1.2'
__module_description__ = 'More controllable highlights'

config_dir = pathlib.Path(str(hexchat.get_info("configdir"))).resolve() / "adconfig"
config_dir.mkdir(exist_ok=True)
config_file = config_dir / "betterping2.json"


class NegatableList(NamedTuple):
    list: List[str]
    negate: bool

    def check(self, s: str) -> bool:
        if len(self.list) == 0:
            return True  # we're an empty list. Thus we're ignored

        out = any(e == s or fnmatch(e, s) for e in self.list)
        if self.negate:
            return not out  # is s NOT in check

        return out

    def __repr__(self) -> str:
        return f'{"!" if self.negate else ""}{self.list}'


class AbstractChecker(ABC):
    def __init__(
        self, check_str: str, nicks: NegatableList, networks: NegatableList, channels: NegatableList,
        case_sensitive: bool = False, type: str = None
    ) -> None:

        self.check_str = check_str
        self.nicks = nicks
        self.channels = channels
        self.networks = networks
        self.case_sensitive = case_sensitive
        self.type = type

        if not self.compile():
            raise ValueError('Failed to compile')

    def compile(self) -> bool:
        return True

    def check(self, msg: str, source_nick: str, source_channel: str = None, source_network: str = None) -> bool:
        source_channel = source_channel if source_channel is not None else str(hexchat.get_info('channel'))
        source_network = source_network if source_network is not None else str(hexchat.get_info('network'))

        if source_channel.startswith(">>") and source_channel.endswith("<<"):
            return False  # dont match on magic channels

        if not (
            self.nicks.check(hexchat.strip(source_nick))
            and self.channels.check(source_channel)
            and self.networks.check(source_network)
        ):
            # we aren't allowed to check stuff for this checker for this message
            return False

        return self._check(msg)

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}({self.check_str=}, {self.nicks=},'
            f' {self.channels=}, {self.networks=}, {self.case_sensitive=})'
        )

    @abstractmethod
    def _check(self, str_to_check: str) -> bool:
        ...

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type':             self.type,
            'check_string':     self.check_str,
            'nicks':            self.nicks.list,
            'negate_nicks':     self.nicks.negate,
            'chans':            self.channels.list,
            'negate_chans':     self.channels.negate,
            'networks':         self.networks.list,
            'negate_networks':  self.networks.negate,
            'case_sensitive':   self.case_sensitive,
        }

    @classmethod
    def from_dict(cls, source: Dict[str, Any]) -> AbstractChecker:
        return cls(
            check_str=source['check_string'],
            nicks=NegatableList(source['nicks'], source['negate_nicks']),
            channels=NegatableList(source['chans'], source['negate_chans']),
            networks=NegatableList(source['networks'], source['negate_networks']),
            case_sensitive=source['case_sensitive'],
        )


class RegexChecker(AbstractChecker):
    def __init__(
        self, check_str: str, nicks: NegatableList, networks: NegatableList, channels: NegatableList,
        case_sensitive: bool
    ) -> None:
        self.regexp = None
        super().__init__(check_str, nicks, networks, channels, case_sensitive=case_sensitive, type='regex')

    def compile(self):
        try:
            self.regexp = re.compile(self.check_str, re.IGNORECASE if not self.case_sensitive else 0)
            return True

        except re.error as e:
            print('Regex compilation error: {}'.format(e))
            return False

    def _check(self, str_to_check):
        if self.regexp is None:
            raise ValueError('RegexChecker._check() called while regexp is uncompiled')

        match = self.regexp.search(str_to_check)
        return match is not None


class GlobChecker(AbstractChecker):
    def __init__(
        self, check_str: str, nicks: NegatableList, networks: NegatableList, channels: NegatableList,
        case_sensitive: bool
    ) -> None:
        super().__init__(check_str, nicks, networks, channels, case_sensitive=case_sensitive, type='glob')

    def _check(self, str_to_check):
        if self.case_sensitive:
            return fnmatchcase(str_to_check, self.check_str)

        print(f'{str_to_check=}  {self.check_str=}   {fnmatch(str_to_check, self.check_str)=}')
        return fnmatch(str_to_check, self.check_str)


class ExactChecker(AbstractChecker):
    def __init__(
        self, check_str: str, nicks: NegatableList, networks: NegatableList, channels: NegatableList,
        case_sensitive: bool
    ) -> None:
        super().__init__(check_str, nicks, networks, channels, case_sensitive=case_sensitive, type='exact')

    def _check(self, str_to_check):
        if self.case_sensitive:
            return self.check_str == str_to_check

        return self.check_str.casefold() == str_to_check.casefold()


class ContainsChecker(AbstractChecker):
    def __init__(
        self, check_str: str, nicks: NegatableList, networks: NegatableList, channels: NegatableList,
        case_sensitive: bool
    ) -> None:
        super().__init__(check_str, nicks, networks, channels, case_sensitive=case_sensitive, type='contains')

    def _check(self, str_to_check: str) -> bool:
        if self.case_sensitive:
            return self.check_str in str_to_check

        return self.check_str.casefold() in str_to_check.casefold()


checkers: List[AbstractChecker] = []
checker_lut = {
    'regex': RegexChecker,
    'glob': GlobChecker,
    'contains': ContainsChecker,
    'exact': ExactChecker,
}


def add_checker(args: argparse.Namespace) -> None:
    checker = checker_lut.get(args.type.lower(), None)
    if checker is None:
        print(f'Unknown checker {args.type}')
        return

    nicks = NegatableList(list(args.nicks), args.nicks_blacklist)
    chans = NegatableList(list(args.channels), args.channels_blacklist)
    nets = NegatableList(list(args.networks), args.networks_blacklist)

    try:
        to_add = checker(  # type: ignore
            check_str=args.string, nicks=nicks, networks=nets, channels=chans, case_sensitive=args.case_sensitive
        )
        to_add.compile()

    except Exception as e:
        print(f'Could not create checker: {e}')
        return

    checkers.append(to_add)
    save_checkers()
    print(f'Added checker {to_add}')


def del_checker(args: argparse.Namespace) -> None:
    to_remove = None
    for checker in checkers:
        if checker.check_str == args.string:
            to_remove = checker
            break

    if to_remove is None:
        print(f'Unknown checker {args.string}')
        return

    checkers.remove(to_remove)
    print(f'Removed checker {to_remove}')
    save_checkers()


def list_checkers(args):
    print(f'There are {len(checkers)} loaded:')
    for checker in checkers:
        print(checker)


def save_checkers():
    with config_file.open('w') as f:
        json.dump([c.to_dict() for c in checkers], f, indent=4)


def load_checkers():
    if not config_file.exists():
        # none to load
        return

    with config_file.open() as f:
        loaded: List[Dict[str, Any]] = json.load(f)

    global checkers
    checkers = [checker_lut[x['type']].from_dict(x) for x in loaded]


# parsers for commands
parser = argparse.ArgumentParser(prog='/bping2', description='Better better highlight support for hexchat')


def on_command(word: List[Optional[str]], word_eol: List[Optional[str]], userdata: None) -> int:
    split = shlex.split(str(word_eol[1]))

    try:
        res = parser.parse_args(split)
    except SystemExit:
        # -h was added
        return hexchat.EAT_HEXCHAT

    res.func(res)

    return hexchat.EAT_HEXCHAT


def on_load():
    subparsers = parser.add_subparsers()

    add_cmd = subparsers.add_parser('add', help=f'Add a checker (one of {", ".join(checker_lut.keys())})')
    add_cmd.add_argument('type', help='checker type')
    add_cmd.add_argument('string', help='checker string')
    add_cmd.add_argument('--nicks', '-n', nargs='+', default=[], help='Nicks to whitelist')
    add_cmd.add_argument('--nicks-blacklist', action='store_true', help='Make Nicks a blacklist')
    add_cmd.add_argument('--channels', '-c', nargs='+', default=[], help='Channels to whitelist')
    add_cmd.add_argument('--channels-blacklist', action='store_true', help='Make channels a blacklist')
    add_cmd.add_argument('--networks', '-net', nargs='+', default=[], help='Networks to whitelist')
    add_cmd.add_argument('--networks-blacklist', action='store_true', help='Make networks a blacklist')
    add_cmd.add_argument('--case-sensitive', default=False, action='store_true')

    del_cmd = subparsers.add_parser('del', help='Remove a checker')
    del_cmd.add_argument('string', help='String to remove')

    list_cmd = subparsers.add_parser('list', help='List all checkers')

    add_cmd.set_defaults(func=add_checker)
    del_cmd.set_defaults(func=del_checker)
    list_cmd.set_defaults(func=list_checkers)

    load_checkers()


def on_message(word, word_eol, userdata):
    if len(word) < 2:
        return hexchat.EAT_NONE

    msg = word[1]
    nick = word[0]

    if any(checker.check(msg, nick) for checker in checkers):
        word[0] = hexchat.strip(word[0])
        # Get the current context before emit_printing, because other plugins can change the current context
        ctx = hexchat.get_context()
        ctx.emit_print(userdata, *word)
        ctx.command("GUI COLOR 3")
        return hexchat.EAT_ALL

    return hexchat.EAT_NONE


hexchat.hook_print("Channel Message", on_message, userdata="Channel Msg Hilight")
hexchat.hook_print("Channel Action", on_message, userdata="Channel Action Hilight")

hexchat.hook_unload(lambda _: print(f'better_ping 2 v{__module_version__} unloaded'))  # type: ignore
hexchat.hook_command("bping2", on_command)
on_load()
print(f'better_ping 2 v{__module_version__} loaded')
