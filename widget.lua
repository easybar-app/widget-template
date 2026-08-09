-- Minimal stateful widget: left-click toggles its local state.

local enabled = false
local widget

--- Renders the icon and label from the widget's current enabled state.
local function render()
	local color = enabled and easybar.theme.ref.success or easybar.theme.ref.muted

	widget:set({
		icon = {
			string = enabled and "●" or "○",
			color = color,
		},
		label = {
			string = enabled and "Enabled" or "Disabled",
			color = color,
		},
	})
end

widget = easybar.add(easybar.kind.item, "example_widget", {
	position = "right",
	order = 50,
})

widget:subscribe(easybar.events.forced, render)

widget:subscribe(easybar.events.mouse.clicked, function(event)
	if event.button == nil or event.button == easybar.events.mouse.left_button then
		enabled = not enabled
		render()
	end
end)

render()
