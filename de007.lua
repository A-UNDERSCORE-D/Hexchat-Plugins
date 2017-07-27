local plugin_name = "de007lua"
local plugin_description = "Lua based script for removing 007 from raw lines"
local plugin_version = "1"
hexchat.register(plugin_name, plugin_version, plugin_description)

local function onraw (_, word_eol)
local line = word_eol[1]
  if line:find("\a") then
    local msg, _ = word_eol[1]:gsub("\a", "\\007")
    hexchat.command("RECV " .. msg)
    return hexchat.EAT_ALL
    end
 end

hexchat.hook_server("RAW LINE", onraw, hexchat.PRI_HIGHEST)

hexchat.hook_unload(
  function (_)
    print(plugin_name .. " unloaded")
  end)
print(plugin_name .. " loaded")
