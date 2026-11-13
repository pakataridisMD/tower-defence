class_name WeatherOverlay
extends ColorRect
## The near layer of the weather (see WeatherArt): rain, snow, ash or dust drawn over the whole battle
## view, under the HUD, with the edges of the view darkened or frosted. It follows the board's weather:
## the same kind, fading in and out with it, the same wind, and the lightning flashes.

const SHADER := preload("res://assets/shaders/weather_overlay.gdshader")
## Size of one weather pixel on a 1920x1080 screen, to match the art.
const PIXEL := 3.0

var sky: WeatherArt
## Set by the capture tool to hold the falling weather still.
var frozen_time := -1.0
var _time := 0.0
var _shader: ShaderMaterial


func setup(p_sky: WeatherArt, rect: Rect2) -> void:
	sky = p_sky
	name = "WeatherOverlay"
	position = rect.position
	size = rect.size
	# The shader draws every pixel itself; if it ever failed to load, a clear rectangle hides nothing.
	color = Color(1, 1, 1, 0)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_shader = ShaderMaterial.new()
	_shader.shader = SHADER
	material = _shader
	_shader.set_shader_parameter("rect_size", rect.size)
	_shader.set_shader_parameter("px", PIXEL)
	_shader.set_shader_parameter("void_land", sky.weather.biome == &"void")
	_apply()


func _process(delta: float) -> void:
	_time += delta
	_apply()


func _apply() -> void:
	if sky == null or not is_instance_valid(sky):
		visible = false
		return
	var showing := sky.kind != Weather.Kind.CLEAR and sky.intensity > 0.001
	visible = showing or sky.flash() > 0.01
	_shader.set_shader_parameter("kind", int(sky.kind))
	_shader.set_shader_parameter("intensity", sky.intensity if showing else 0.0)
	_shader.set_shader_parameter("wind", sky.weather.wind_dir * sky.wind_now)
	_shader.set_shader_parameter("flash", sky.flash())
	_shader.set_shader_parameter("t", _time if frozen_time < 0.0 else frozen_time)


## The shader's current settings, for tests.
func param(key: StringName) -> Variant:
	return _shader.get_shader_parameter(key)
