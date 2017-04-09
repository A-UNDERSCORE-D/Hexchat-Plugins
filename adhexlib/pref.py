import hexchat
from typing import Union


def setpref(name: str, data: Union(str, list)):
    if type(data) is str:
        hexchat.set_pluginpref(name, data)
    elif type(data) is list:
        hexchat.set_pluginpref(name, " ".join(data))
    else:
        raise TypeError("unexpected type for data: {}".format(str(type(data))))


def getpref(name: str) -> list:
    temp = hexchat.get_pluginpref(name)
    if not temp:
        return []
    else:
        return [temp] if " " not in temp else temp.split()


def appendpref(name: str, data: Union(list, str)):
    if type(data) is str:
        temp = getpref(name)
        setpref(name, list(set(temp + [data])))
    elif type(data) is list:
        temp = getpref(name)
        setpref(name, list(set(temp + data)))
    else:
        raise TypeError("unexpected type for data: {}".format(str(type(data))))

