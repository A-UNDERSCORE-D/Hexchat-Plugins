local plugin_name = "spamSaftey"
local plugin_description = "Removes laggy things when being pingspammed"
local plugin_version = "0.1"

hexchat.register(plugin_name, plugin_version, plugin_description)

local last = os.time()
local count = 0
local max = 20
local isoff = false
local wait = (1000 * 60) * 1 -- One minute
local timer = 0

local function timercb()
  hexchat.command("PINGSPAMON")
  print("Timer expired or was manually removed, restoring standard behaviour")
  count = 0
  isoff = false
  return false
end

local function onPing()
  if (not isoff) and (os.time() - last) < 10 then
    count = count + 1
  end
  if (not isoff) and (count > max) then
    hexchat.command("PINGSPAMOFF")
    print("You are being ping spammed. in order to prevent client lag ping sounds and notifications have been disabled.")
    timer = hexchat.hook_timer(wait, timercb)
    count = 0
    isoff = true
  end
  last = os.time()
end

local function nohilights()
  hexchat.command("SET input_balloon_hilight 0")
  hexchat.command("SET input_beep_hilight 0")
  hexchat.command("SET input_flash_hilight 0")
  hexchat.command("SET input_tray_hilight 0")
  return hexchat.EAT_HEXCHAT
end

local function yeshilights()
  hexchat.command("SET input_balloon_hilight 1")
  hexchat.command("SET input_beep_hilight 1")
  hexchat.command("SET input_flash_hilight 1")
  hexchat.command("SET input_tray_hilight 1")
  if timer ~= 0 then
    print("Removing timer and resetting to defauts")
    hexchat.unhook(timer)
    count = 0
    isoff = false
    timer = 0
  end
  return hexchat.EAT_HEXCHAT
end

hexchat.hook_unload(function()
  print(plugin_name .. " unloaded")
end)

hexchat.hook_command("PINGSPAMON", yeshilights)
hexchat.hook_command("PINGSPAMOFF", nohilights)

hexchat.hook_print("Channel Msg Hilight", onPing)
hexchat.hook_print("Channel Action Hilight", onPing)
print(plugin_name .. " loaded")
