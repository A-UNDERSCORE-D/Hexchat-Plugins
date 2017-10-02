local plugin_name = "spamSaftey"
local plugin_description = "Removes laggy things when being pingspammed"
local plugin_version = "0.1"

hexchat.register(plugin_name, plugin_version, plugin_description)

local last = os.time()
local count = {0, 0}
local max = {30, 50}
local isoff = {false, false}
local wait = {(1000 * 60) * 1, (1000 * 60) * 1}
local timer = 0

local function cleanup(t)
    if timer ~= 0 then
    print("Removing timer and resetting to defauts")
    hexchat.unhook(timer)
    if t then
      count[t] = 0
    else
      count = {0, 0}
    end
    isoff[t] = false
    timer = 0
  end
end

local function nopms()
  hexchat.command("SET input_balloon_priv 0")
  hexchat.command("SET input_beep_priv 0")
  hexchat.command("SET input_flash_priv 0")
  hexchat.command("SET input_tray_priv 0")
  return hexchat.EAT_HEXCHAT
end

local function nohilights()
  hexchat.command("SET input_balloon_hilight 0")
  hexchat.command("SET input_beep_hilight 0")
  hexchat.command("SET input_flash_hilight 0")
  hexchat.command("SET input_tray_hilight 0")
  return hexchat.EAT_HEXCHAT
end

local function yespms(t)
  hexchat.command("SET input_balloon_priv 1")
  hexchat.command("SET input_beep_priv 1")
  hexchat.command("SET input_flash_priv 1")
  hexchat.command("SET input_tray_priv 1")
  cleanup(t)
  return hexchat.EAT_HEXCHAT
end

local function yeshilights(t)
  hexchat.command("SET input_balloon_hilight 1")
  hexchat.command("SET input_beep_hilight 1")
  hexchat.command("SET input_flash_hilight 1")
  hexchat.command("SET input_tray_hilight 1")
  cleanup(t)
  return hexchat.EAT_HEXCHAT
end

local function timercb(t)
  hexchat.find_context(hexchat.get_info("network"), nil):set()
  if t == 1 then
    yeshilights(t)
  elseif t == 2 then
    yespms(t)
  end
  print("Timer expired restoring standard behaviour")
  count[t] = 0
  isoff[t] = false
  return false
end

local function onPing(t)
  if (not isoff[t]) and (os.time() - last) < 10 then
    count[t] = count[t] + 1
  else
    count[t] = 0
  end
  if (not isoff[t]) and (count[t] > max[t]) then
    hexchat.find_context(hexchat.get_info("network"), nil):set()
    if t == 1 then
      print("You are being ping spammed. in order to prevent client lag ping sounds and notifications have been disabled.")
      nohilights(t)
    elseif t == 2 then
      print("You are being PM spammed")
      nopms(t)
    end
    timer = hexchat.hook_timer(wait[t], function() timercb(t) end)
    count[t] = 0
    isoff[t] = true
  end
  last = os.time()
end

hexchat.hook_unload(function()
  print(plugin_name .. " unloaded")
end)

hexchat.hook_command("PINGSPAMON", yeshilights)
hexchat.hook_command("PINGSPAMOFF", nohilights)
hexchat.hook_command("PMSPAMON", yespms)
hexchat.hook_command("PMSPAMOFF", nopms)

hexchat.hook_print("Channel Msg Hilight", function() onPing(1) end)
hexchat.hook_print("Channel Action Hilight", function() onPing(1) end)
hexchat.hook_print("Private Message to Dialog", function() onPing(2) end)
hexchat.hook_print("Private Action to Dialog", function() onPing(2) end)
print(plugin_name .. " loaded")
