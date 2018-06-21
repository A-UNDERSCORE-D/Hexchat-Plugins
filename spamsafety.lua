local plugin_name = "spamSafety2"
local plugin_description = "Rewrite of spamSafety, removes weird bugs"
local plugin_version = "2.0"

hexchat.register(plugin_name, plugin_version, plugin_description)


local watchers = {}
local WatcherClass = {}
WatcherClass.__index = WatcherClass

function WatcherClass:new(wname, ts, wmessage)
  local ret = {
    name = wname,
    last = os.time(),
    max_count = 20,
    lock_time = 20,
    timeout = 2,
    count = 0,
    timer = 0,
    to_set = ts,
    triggered = false,
    message = wmessage,
    disable_timer_hook = 0
  }
  setmetatable(ret, WatcherClass)
  return ret
end


function WatcherClass:print_table()
  for k, v in pairs(self) do
    print(string.format("%s = %s", k, v))
  end
end


function WatcherClass:run_set(state)
  local to_set = "1"
  if state ~= true then to_set = "0" end
  for _, v in ipairs(self.to_set) do
    hexchat.command(string.format("SET -quiet %s %s", v, to_set))
  end
end

function WatcherClass:enable()
  self.disable_timer_hook = hexchat.hook_timer(self.lock_time * 1000, function() self:disable() self.disable_timer_hook = 0 return false end)
  self:run_set(false)
  self.triggered = true
end

function WatcherClass:disable()
  if not self.triggered then print("already disabled") return end
  self:run_set(true)
  self.triggered = false
  self.count = 0
  if self.disable_timer_hook ~= 0 then
    hexchat.unhook(self.disable_timer_hook)
    self.disable_timer_hook = 0
  end
  print("timer disabled")
end

function WatcherClass:check()
  if self.count >= self.max_count then
    print(self.message)
    self:enable()
  end
end

function WatcherClass:trigger()
  local curtime = os.time()
  if curtime - self.last < self.timeout and not self.triggered then
    self.count = self.count + 1
    self:check()
  elseif not self.triggered then
    self.count = 1
  end
  self.last = curtime
end

local function early_stop(word, word_eol, userdata)
  if #word < 2 then
    print("I require a watcher to disable")
    return
  end
  local watcher = watchers[word[2]]
  if watcher == nil then
    print(string.format("Watcher %s not found in watcher list.", word[2]))
    return
  end
  print(string.format("Disabling watcher %s", word[2]))
  watcher:disable()
end


-- TODO: make this doable on the fly. The ability to mark something specific as spammable is really handy.
watchers["ping"] = WatcherClass:new("ping", { "input_balloon_hilight", "input_beep_hilight", "input_flash_hilight", "input_tray_hilight" }, "Ping spam detected, enabling countermeasures")
watchers["pm"] = WatcherClass:new("pm", { "input_balloon_priv", "input_beep_priv", "input_flash_priv", "input_tray_priv" }, "PM spam detected, enabling countermeasures")
hexchat.hook_print("Private Message To Dialog", function() watchers["pm"]:trigger() end)
hexchat.hook_print("Channel Msg Hilight", function() watchers["ping"]:trigger() end)
hexchat.hook_print("Channel Action Hilight", function() watchers["ping"]:trigger() end)
hexchat.hook_command("stoptimeout", early_stop)

hexchat.hook_unload(function() print(plugin_name, "unloaded") end)
print(plugin_name, "loaded")
