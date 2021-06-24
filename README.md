# Hexchat Plugins

Plugins that I have written for hexchat

## Betterping is dead! Long live betterping2

Ive rewritten the BetterPing plugin to be saner.

## BetterPing breaking changes

The BetterPing plugin moves away from supporting the pickle module following commit
`41a1cf4d130fc3054f2ce659c39769492d110d05`. At said commit, the plugin will update
data stored using pickle to json based storage. Following the commit, pickle support
is removed entirely.