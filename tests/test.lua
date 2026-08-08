local root = assert(arg[1], "repository root argument is required")

local state = {
	nodes = {},
}

local function new_node(name, props)
	local node = {
		name = name,
		props = props,
		subscriptions = {},
	}

	function node:set(next_props)
		self.props = next_props
	end

	function node:subscribe(event, callback)
		self.subscriptions[event] = callback
	end

	return node
end

local easybar = {
	kind = { item = "item" },
	theme = {
		ref = {
			success = "theme.success",
			muted = "theme.muted",
		},
	},
	events = {
		forced = "forced",
		mouse = {
			clicked = "mouse.clicked",
			left_button = "left",
			right_button = "right",
		},
	},
}

function easybar.add(kind, name, props)
	assert(kind == easybar.kind.item, "example widget must create an item")
	assert(state.nodes[name] == nil, "duplicate node: " .. name)
	local node = new_node(name, props)
	state.nodes[name] = node
	return node
end

local environment = setmetatable({ easybar = easybar }, { __index = _G })
local chunk, load_error = loadfile(root .. "/widget.lua", "t", environment)
assert(chunk, "widget failed to load: " .. tostring(load_error))

local ok, runtime_error = pcall(chunk)
assert(ok, "widget failed during startup: " .. tostring(runtime_error))

local widget = assert(state.nodes.example_widget, "widget must create example_widget")
assert(widget.props.label.string == "Disabled", "widget must start disabled")
assert(widget.props.icon.color == easybar.theme.ref.muted, "disabled widget must use the muted color")

local click = assert(widget.subscriptions[easybar.events.mouse.clicked], "widget must handle clicks")
click({ button = easybar.events.mouse.left_button })
assert(widget.props.label.string == "Enabled", "left-click must enable the widget")
assert(widget.props.icon.color == easybar.theme.ref.success, "enabled widget must use the success color")

click({ button = easybar.events.mouse.right_button })
assert(widget.props.label.string == "Enabled", "right-click must not toggle the widget")

local forced = assert(widget.subscriptions[easybar.events.forced], "widget must handle forced refreshes")
forced({})
assert(widget.props.label.string == "Enabled", "forced refresh must preserve widget state")

print("Example widget regression checks passed")
