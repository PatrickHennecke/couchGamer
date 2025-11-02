import gi
import subprocess
import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame
import cairo
import math
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API*")
import ctypes
import configparser

try:
    fontconfig = ctypes.CDLL("libfontconfig.so.1")
    fontconfig.FcInit()
except Exception:
    pass

pygame.init()
pygame.joystick.init()
count = pygame.joystick.get_count()
if count != 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
def resource_path(relative_path):
    import sys
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), "config.ini")

TIMER_DURATION = int(config.get("Settings", "TIMER_DURATION", fallback="10"))
exec_script_path = config.get("Settings", "EXEC_SCRIPT", fallback="/usr/local/bin/cec_hdmi3.sh")
couch_path = resource_path("assets/couch.png")
desk_path = resource_path("assets/office_chair.png")

couch_pixbuf = GdkPixbuf.Pixbuf.new_from_file(couch_path)
desk_pixbuf = GdkPixbuf.Pixbuf.new_from_file(desk_path)

couch_icon = Gtk.Image.new_from_pixbuf(couch_pixbuf)
desk_icon = Gtk.Image.new_from_pixbuf(desk_pixbuf)

class MenuWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="GTK Menu")
        self.set_border_width(20)
        self.fullscreen()

        self.remaining_time = TIMER_DURATION
        self.choice_made = False

        grid = Gtk.Grid()
        grid.set_column_spacing(10)  # 10px gap between buttons
        grid.set_row_spacing(10)
        grid.set_column_homogeneous(False)
        grid.set_row_homogeneous(False)
        self.add(grid)

        self.left_button = Gtk.Button()
        self.left_button.set_image(couch_icon)
        self.left_button.set_name("couch-button")
        self.left_button.connect("clicked", self.on_left_clicked)

        self.right_button = Gtk.Button()
        self.right_button.set_image(desk_icon)
        self.right_button.set_name("desk-button")
        self.right_button.connect("clicked", self.on_right_clicked)
        self.right_button.set_sensitive(True)

        self.overlay = Gtk.Overlay()
        self.progress = 0.0
        self.pulse = 1.0

        self.arc_draw_area = Gtk.DrawingArea()
        self.arc_draw_area.set_size_request(200, 200)
        self.arc_draw_area.set_halign(Gtk.Align.CENTER)
        self.arc_draw_area.set_valign(Gtk.Align.CENTER)
        self.arc_draw_area.connect("draw", self.on_border_draw)
        self.arc_draw_area.set_can_focus(False)
        self.arc_draw_area.set_has_window(False)

        self.overlay.add(self.right_button)
        self.overlay.add_overlay(self.arc_draw_area)
        self.overlay.set_overlay_pass_through(self.arc_draw_area, True)

        right_box = Gtk.Box()
        right_box.set_halign(Gtk.Align.CENTER)
        right_box.set_valign(Gtk.Align.CENTER)
        right_box.pack_start(self.overlay, True, True, 0)

        # Attach Box with Overlay to the grid
        grid.attach(right_box, 1, 0, 1, 1)

        # Add buttons to grid, centered
        grid.attach(self.left_button, 0, 0, 1, 1)

        self.connect("size-allocate", self.on_size_allocate)
        #inspect_all_theme_colors()
        self.start_time = GLib.get_monotonic_time()

        if count != 0:
            GLib.timeout_add(50, self.poll_joystick_events)
        GLib.timeout_add(100, self.animate)

    def highlight_button(self, index):
        if index == 0:
            self.left_button.grab_focus()
            #self.left_button.get_style_context().add_class("highlighted")
            #self.right_button.get_style_context().remove_class("highlighted")
        else:
            self.right_button.grab_focus()
            #self.right_button.get_style_context().add_class("highlighted")
            #self.left_button.get_style_context().remove_class("highlighted")

    def handle_joystick_motion(self, event):
        if event.type == pygame.JOYAXISMOTION and event.axis == 0:
            if event.value < -0.5:
                self.selected_index = 0
                self.highlight_button(0)
                #self.left_button.set_state_flags(Gtk.StateFlags.SELECTED, True)
                #self.right_button.unset_state_flags(Gtk.StateFlags.SELECTED)
                #print(f'joystick moved: {event.value}')
            elif event.value > 0.5:
                self.selected_index = 1
                self.highlight_button(1)
                #self.right_button.set_state_flags(Gtk.StateFlags.SELECTED, True)
                #self.left_button.unset_state_flags(Gtk.StateFlags.SELECTED)
                #print(f'joystick moved: {event.value}')

    def handle_hat_motion(self, event):
        if event.type == pygame.JOYHATMOTION:
            hat_x, hat_y = event.value
            if hat_x < 0:
                self.selected_index = 0
                self.left_button.set_state_flags(Gtk.StateFlags.SELECTED, True)
                self.right_button.unset_state_flags(Gtk.StateFlags.SELECTED)
                #print("D-pad left pressed")
            elif hat_x > 0:
                self.selected_index = 1
                self.right_button.set_state_flags(Gtk.StateFlags.SELECTED, True)
                self.left_button.unset_state_flags(Gtk.StateFlags.SELECTED)
                #print("D-pad right pressed")

    def handle_joystick_button(self, event):
        if event.type == pygame.JOYBUTTONDOWN and event.button == 0: #'A' button
            if self.selected_index == 0:
                self.left_button.clicked()
            elif self.selected_index == 1:
                self.right_button.clicked()

    def poll_joystick_events(self):
        for event in pygame.event.get():
            self.handle_joystick_motion(event)
            self.handle_joystick_button(event)
            self.handle_hat_motion(event)
        return True

    def on_size_allocate(self, widget, allocation):
        width = allocation.width
        height = allocation.height
        button_size = max(width, height) // 3

        self.left_button.set_size_request(button_size, button_size)
        self.right_button.set_size_request(button_size, button_size)
        self.arc_draw_area.set_size_request(allocation.width, allocation.height)
        self.arc_draw_area.queue_draw()

        # Center the grid
        self.get_child().set_valign(Gtk.Align.CENTER)
        self.get_child().set_halign(Gtk.Align.CENTER)

    def on_left_clicked(self, button):
        if not self.choice_made:
            self.choice_made = True
            try:
                subprocess.Popen([exec_script_path])
            except Exception as e:
                print(f'Error running script: {e}')
            Gtk.main_quit()

    def on_right_clicked(self, button):
        if not self.choice_made:
            self.choice_made = True
            Gtk.main_quit()

    def animate(self):
        if self.choice_made:
            return False

        elapsed = (GLib.get_monotonic_time() - self.start_time) / 1_000_000
        self.progress = min(elapsed / TIMER_DURATION, 1.0)

        self.pulse = 0.5 + 0.5 * math.sin(GLib.get_monotonic_time() / 1e6 * 2 * math.pi / 1.0)
        self.arc_draw_area.queue_draw()

        if self.progress >=1.0:
            self.choice_made = True
            self.right_button.set_name("highlighted")
            GLib.timeout_add(100, Gtk.main_quit)
            return False
        return True  # Keep running

    def on_border_draw(self, widget, cr):
        alloc = self.right_button.get_allocation()
        x, y = alloc.x, alloc.y
        x, y = self.right_button.translate_coordinates(self.arc_draw_area, 0, 0)
        w, h = alloc.width, alloc.height

        # Get theme color
        context = self.right_button.get_style_context()
        start_color = context.get_property("background-color", Gtk.StateFlags.NORMAL)
        end_color = context.get_property("color", Gtk.StateFlags.NORMAL)

        if isinstance(start_color, Gdk.RGBA) and isinstance(end_color, Gdk.RGBA):
            self.draw_animated_border(cr, x, y, w, h, self.progress, end_color)
        else:
            cr.set_source_rgba(0.5, 0.5, 0.5, 1.0)

        cr.set_line_width(6)
        cr.set_antialias(cairo.ANTIALIAS_BEST)

    def interpolate_color(self, c1, c2, t):
        return Gdk.RGBA(
            red   = c1.red   * (1 - t) + c2.red   * t,
            green = c1.green * (1 - t) + c2.green * t,
            blue  = c1.blue  * (1 - t) + c2.blue  * t,
            alpha = c1.alpha * (1 - t) + c2.alpha * t
        )

    def draw_animated_border(self, cr, x, y, w, h, progress, color):
        base_width = 6
        pulse_range = 2
        pulsed_width = base_width + pulse_range * self.pulse
        cr.set_line_width(pulsed_width)
        #cr.set_line_width(base_width)

        cr.set_source_rgba(
            color.red,
            color.green,
            color.blue,
            color.alpha * self.pulse  # Fade in/out
        )
        #cr.set_source_rgba(
            #color.red,
            #color.green,
            #color.blue,
            #color.alpha
        #)

        cr.set_antialias(cairo.ANTIALIAS_BEST)

        perimeter = 2 * (w + h)
        animated_length = perimeter * progress

        # Draw each side conditionally
        cr.new_path()

        # Top
        if animated_length > 0:
            length = min(animated_length, w)
            cr.move_to(x, y)
            cr.line_to(x + length, y)
            animated_length -= length

        # Right
        if animated_length > 0:
            length = min(animated_length, h)
            cr.move_to(x + w, y)
            cr.line_to(x + w, y + length)
            animated_length -= length

        # Bottom
        if animated_length > 0:
            length = min(animated_length, w)
            cr.move_to(x + w, y + h)
            cr.line_to(x + w - length, y + h)
            animated_length -= length

        # Left
        if animated_length > 0:
            length = min(animated_length, h)
            cr.move_to(x, y + h)
            cr.line_to(x, y + h - length)

        cr.stroke()

win = MenuWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
