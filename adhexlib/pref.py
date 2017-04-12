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


def appendpref(name: str, data):
    if type(data) is str:
        temp = getpref(name)
        setpref(name, temp + [data])
    elif type(data) is list:
        temp = getpref(name)
        setpref(name, temp + data)
    else:
        raise TypeError("unexpected type for data: {}".format(str(type(data))))


def removepref(name: str, data):
    temp = getpref(name)
    if type(data) is str:
        if data in temp:
            temp.remove(data)
            setpref(name, temp)
    elif type(data) is list:
        changed = False
        for item in data:
            if item in temp:
                temp.remove(item)
                changed = True
        if changed:
            setpref(name, temp)


def appendprefunique(name: str, data):
    if type(data) is str:
        temp = getpref(name)
        setpref(name, list(set(temp + [data])))
    elif type(data) is list:
        temp = getpref(name)
        setpref(name, list(set(temp + data)))