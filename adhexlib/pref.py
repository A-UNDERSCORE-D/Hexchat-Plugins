import hexchat
from typing import Union


def setpref(name: str, data, split: str =None):
    if type(data) is str:
        hexchat.set_pluginpref(name, data)
    elif type(data) is list:
        hexchat.set_pluginpref(name, (split if split else " ").join(data))
    else:
        raise TypeError("unexpected type for data: {}".format(str(type(data))))


def getpref(name: str, split: str =None) -> list:
    temp = hexchat.get_pluginpref(name)
    if not temp:
        return []
    else:
        return [temp] if (split if split else " ") not in temp else temp.split(split if split else " ")


def appendpref(name: str, data, split: str =None):
    if type(data) is str:
        temp = getpref(name)
        setpref(name, temp + [data], split)
    elif type(data) is list:
        temp = getpref(name)
        setpref(name, temp + (data if split not in " ".join(data) else " ".join(data).split(split)), split)
    else:
        raise TypeError("unexpected type for data: {}".format(str(type(data))))


def removepref(name: str, data, split: str =None):
    temp = getpref(name, split)
    if type(data) is str:
        if data in temp:
            temp.remove(data)
            setpref(name, temp, split)
    elif type(data) is list:
        changed = False
        for item in data if (split if split else " ") not in " ".join(data) else " ".join(data).split(split):
            if item in temp:
                temp.remove(item)
                changed = True
        if changed:
            setpref(name, temp, split)


def appendprefunique(name: str, data):
    temp = getpref(name)
    if type(data) is str:
        setpref(name, list(set(temp + [data])))
    elif type(data) is list:
        setpref(name, list(set(temp + data)))

