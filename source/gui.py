import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import json
import re
import traceback
import os, sys
import time
import webbrowser
from functools import partial
from source import widgetlib
from source import ssDiagnostics as diagnostics
from source import ssTranslate as fish
from source import gamelib
from source import constants as CONST
from source.tkHyperlinkManager import HyperlinkManager
from source.tkSimpleStatusBar import StatusBar
from source import common

def make_GUI(command_line_args):
	root = tk.Tk()
	#the .ico file will not work in Linux or Mac, so this bypasses the icon for those OSes
	try:
		root.iconbitmap(default=common.get_resource('app.ico'))
	except Exception:
		pass
	root.geometry("800x600")       #window size
	root.configure(bg='#f0f0f0')   #background color
	main_frame = SpriteSomethingMainFrame(root, command_line_args)
	root.protocol("WM_DELETE_WINDOW", main_frame.exit)           #intercept when the user clicks the X

	def show_error(self, exception, message, callstack):
		if exception.__name__.upper() == "NOTIMPLEMENTEDERROR":
			messagebox.showerror(   "Not Yet Implemented",
									"This function is not yet implemented\n\n" + str(message)  )
		else:
			messagebox.showerror(   "FATAL ERROR",
									f"While running, encountered fatal error:\n\n" +
									f"{exception.__name__.upper()}\n" +
									f"{str(message)}\n"+
									f"{traceback.format_exc()}"
									)
	tk.Tk.report_callback_exception = show_error     #tie this in so we see errors when they happen

	root.mainloop()

class SpriteSomethingMainFrame(tk.Frame):
	def __init__(self, master, command_line_args):
		super().__init__(master)   #make the frame itself

		self.working_dirs = {
			"file.open": "./",
			"file.save": "./",
			"export.dest": "./",
			"export.source": "./",
			"export.sprite-as-rdc": "./",
			"export.frame-as-png": "./",
			"export.animation-as-gif": "./",
			"export.animation-as-hcollage": "./",
			"export.animation-as-vcollage": "./"
		}
		working_dir_path = os.path.join("resources","meta","working_dirs.json")
		if os.path.exists(working_dir_path):
			with open(working_dir_path) as json_file:
				data = json.load(json_file)
				for k,v in data.items():
					self.working_dirs[k] = v

		self.create_random_title()

		self.create_toolbar()

		self.pack(fill=tk.BOTH, expand=1)    #main frame should take up the whole window

		self.menu = self.create_menu_bar()

		self.panes = tk.PanedWindow(self, orient=tk.HORIZONTAL, name="two_columns")
		self.panes.pack(fill=tk.BOTH, expand=1)

		self.load_sprite(command_line_args["sprite"])

	def create_random_title(self):
		# Generate a new epic random title for this application
		name_dict = {}
		for filename in common.get_all_resources("app_names.json"):
			with open(filename) as name_file:
				for key,item in json.load(name_file).items():
					if key in name_dict:
						name_dict[key].extend(item)
					else:
						name_dict[key] = item
		app_name = []
		if random.choice([True,False]):
			app_name.append(random.choice(name_dict["pre"]))
		app_name.append("Sprite")         #Need to have "Sprite" in the name
		app_name.append(random.choice(name_dict["noun"]))
		if random.choice([True,False]):
			app_name.append(random.choice(name_dict["post"]))
		self.app_title = " ".join(app_name)
		self.master.title(self.app_title)

	def create_toolbar(self):
		toolbar = tk.Frame(self.master, bd=1, relief=tk.RAISED)
		def create_toolbar_button(fish_key, fish_subkey, image_filename="blank.png",command=None):
			icon_path = common.get_resource(image_filename,os.path.join("meta","icons"))
			img = tk.PhotoImage(file=icon_path)
			display_text = fish.translate(fish_key,fish_subkey,os.path.join("meta"))
			button = tk.Button(toolbar,image=img,relief=tk.FLAT,command=command)
			button.img = img
			widgetlib.ToolTip(button,display_text)
			button.pack(side=tk.LEFT,padx=2,pady=2)
			return button
		toolbar.pack(side=tk.TOP,fill=tk.X)
		toolbar_buttons = []

		open_button = create_toolbar_button("menu","file.open","open.png",self.open_file)
		toolbar_buttons.append(open_button)

		save_button = create_toolbar_button("menu","file.save","save.png",self.save_file_as)
		toolbar_buttons.append(save_button)

		inject_button = create_toolbar_button("menu","export.inject","inject.png",self.inject_into_ROM)
		toolbar_buttons.append(inject_button)

		inject_new_button = create_toolbar_button("menu","export.inject-new","inject-new.png",self.copy_into_ROM)
		toolbar_buttons.append(inject_new_button)

	def create_menu_bar(self):
		#create the menu bar
		menu = tk.Menu(self.master, name="menu_bar")
		self.master.configure(menu=menu)

		def create_cascade(name, internal_name, options_list):
			#options_list must be a list of 3-tuples containing
			# Display Name
			# image name (without the .png extension)
			# function to call
			cascade = tk.Menu(menu, tearoff=0, name=internal_name)
			cascade.images = {}
			for display_name,image_name,function_to_call in options_list:
				if (display_name,image_name,function_to_call) == (None,None,None):
					cascade.add_separator()
				else:
					if image_name:
						cascade.images[image_name] = tk.PhotoImage(file=common.get_resource(f"{image_name}.png",os.path.join("meta","icons")))
					else:
						cascade.images[image_name] = None
					cascade.add_command(label=display_name, image=cascade.images[image_name], compound=tk.LEFT, command=function_to_call, state="disabled" if function_to_call == None else "normal")
			menu.add_cascade(label=name, menu=cascade)
			return cascade

		menu_options = []

		#create the file menu
		file_menu = create_cascade(fish.translate("menu","file",os.path.join("meta")), "file_menu",
											[
													(fish.translate("menu","file.open",os.path.join("meta")),"open",self.open_file),
													(fish.translate("menu","file.save",os.path.join("meta")),"save",self.save_file_as),
													(fish.translate("menu","file.exit",os.path.join("meta")),"exit",self.exit),
											])
		menu_options.append(file_menu)

		#create the import menu
		import_menu = create_cascade(fish.translate("menu","export",os.path.join("meta")),"export_menu",
											[
													(fish.translate("menu","export.inject",os.path.join("meta")),"inject",self.inject_into_ROM),
													(fish.translate("menu","export.inject-new",os.path.join("meta")),"inject-new",self.copy_into_ROM),
													(fish.translate("menu","export.inject-bulk",os.path.join("meta")),None,self.inject_into_ROM_bulk),
													(None,None,None),
													(fish.translate("menu","export.frame-as-png",os.path.join("meta")),None,self.export_frame_as_png),
													(fish.translate("menu","export.animation-as-gif",os.path.join("meta")),None,None),#self.export_animation_as_gif),
													(fish.translate("menu","export.animation-as-hcollage",os.path.join("meta")),None,partial(self.export_animation_as_collage,"horizontal")),
													(fish.translate("menu","export.animation-as-vcollage",os.path.join("meta")),None,None),#partial(self.export_animation_as_collage,"vertical")),
											])
		menu_options.append(import_menu)

		#for future implementation
		plugins_menu = tk.Menu(menu, tearoff=0, name="plugins_menu")
		tools_menu = tk.Menu(menu, tearoff=0, name="tools_menu")
		tools_menu.add_cascade(label=fish.translate("menu","plugins",os.path.join("meta")), menu=plugins_menu)
		menu.add_cascade(label=fish.translate("menu","tools",os.path.join("meta")), menu=tools_menu)

		help_menu = create_cascade(fish.translate("menu","help",os.path.join("meta")),"help_menu",
											[
													(fish.translate("menu","help.diagnostics",os.path.join("meta")),None,self.diagnostics),
													(fish.translate("menu","help.about",os.path.join("meta")),None,self.about),
											])
		menu_options.append(help_menu)

		return menu

	def load_plugins(self):
		self.menu.children["plugins_menu"] = tk.Menu(self.menu, tearoff=0, name="plugins_menu")

		if self.game.plugins or self.sprite.plugins:
			if self.game.plugins:
				game_plugins_menu = tk.Menu(self.menu, tearoff=0, name="game_plugins_menu")
				for label, command in self.game.plugins:
					game_plugins_menu.add_command(label=label,command=command,state="disabled" if command == None else "normal")
				self.menu.children["plugins_menu"].add_cascade(label=fish.translate("menu","plugins.game",os.path.join("meta")),menu=game_plugins_menu)

			if self.sprite.plugins:
				sprite_plugins_menu = tk.Menu(self.menu, tearoff=0, name="sprite_plugins_menu")
				for label, command in self.sprite.plugins:
					sprite_plugins_menu.add_command(label=label,command=command,state="disabled" if command == None else "normal")
				self.menu.children["plugins_menu"].add_cascade(label=fish.translate("menu","plugins.sprite",os.path.join("meta")),menu=sprite_plugins_menu)
		else:
			self.menu.children["plugins_menu"].add_command(label=fish.translate("meta","none",os.path.join("meta")),state="disabled")

	def load_sprite(self, sprite_filename):
		self.game, self.sprite = gamelib.autodetect(sprite_filename)
		self.sprite_coord = (100,100)        #an arbitrary default
		self.attach_both_panels()            #remake the GUI panels
		self.load_plugins()
		self.initialize_sprite_animation()

	def attach_both_panels(self):
		#this same function can also be used to re-create the panels
		#have to make the canvas before the buttons so that the left panel buttons can manipulate it
		self.freeze_ray = True    #do not update the sprite while doing this
		if hasattr(self, "timer_callback"):
			self.master.after_cancel(self.timer_callback)
		if hasattr(self, "left_panel"):
			for widget in self.left_panel.winfo_children():
				if "direction_buttons" in widget.winfo_name():
					bindings = None
					bindings_filename = common.get_resource("bindings.json","meta")
					with open(bindings_filename,encoding="utf-8") as f:
						bindings = json.load(f)
					for subwidget in widget.winfo_children():
						if "_button" in subwidget.winfo_name():
							button_name = subwidget.winfo_name().replace("_button","")
							button_section = button_name[:button_name.find("_")]
							button_name = button_name[button_name.find("_")+1:]
							keypresses = None
							keypresses_switcher = bindings[button_section] if button_section in bindings else {}
							keypresses = keypresses_switcher.get(button_name.lower(),None)
							for keypress in keypresses:
								subwidget.unbind_all(keypress)
							subwidget.destroy()
		self.left_panel = tk.PanedWindow(self.panes, orient=tk.VERTICAL, name="left_panel",width=250,handlesize=0,sashwidth=0,sashpad=2)
		self.right_panel = ttk.Notebook(self.panes, name="right_pane")
		self.canvas = tk.Canvas(self.right_panel, name="main_canvas")
		self.overview_frame = tk.Frame(self.right_panel, name="overview_frame")
		self.overview_canvas = tk.Canvas(self.overview_frame, name="overview_canvas")
		self.attach_left_panel()
		self.attach_right_panel()
		self.create_status_bar()

	def attach_left_panel(self):
		#this same function can also be used to re-create the panel
		MINSIZE = 25
		vcr_controls = self.get_vcr_controls()  #have to do this early so that their values are available for other buttons
		self.left_panel.add(self.get_reload_button(),minsize=MINSIZE)
		self.sprite.attach_metadata_panel(self.left_panel)
		self.game.attach_background_panel(self.left_panel,self.canvas,self.zoom_getter,self.frame_getter)
		self.sprite.attach_animation_panel(self.left_panel,self.canvas,self.overview_canvas,self.zoom_getter,self.frame_getter,self.coord_getter)
		self.left_panel.add(vcr_controls,minsize=MINSIZE)
		self.panes.add(self.left_panel)

	def attach_right_panel(self):
		#this same function can also be used to re-create the panel
		self.attach_canvas()
		self.attach_overview()
		self.panes.add(self.right_panel)

	def create_status_bar(self):
		if not hasattr(self, "status_bar"):
			self.status_bar = StatusBar(self)
			self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
		self.status_bar.set(self.game.name + ': "' + self.sprite.classic_name + '"')

	def attach_canvas(self):
		def move_sprite(event):
			self.sprite_coord = [event.x/self.current_zoom, event.y/self.current_zoom]
			self.update_sprite_animation()
		self.canvas.bind("<Button-1>", move_sprite)   #hook this function to call when the canvas is left-clicked
		self.right_panel.add(self.canvas, text=fish.translate("tab","animations",os.path.join("meta")))

	def attach_overview(self):
		self.overview_frame.grid_rowconfigure(0, weight=1)
		self.overview_frame.grid_columnconfigure(0, weight=1)

		xscrollbar = tk.Scrollbar(self.overview_frame, orient=tk.HORIZONTAL)
		xscrollbar.grid(row=1, column=0, sticky=tk.EW)

		yscrollbar = tk.Scrollbar(self.overview_frame)
		yscrollbar.grid(row=0, column=1, sticky=tk.NS)

		self.overview_canvas.configure(scrollregion=self.overview_canvas.bbox(tk.ALL),xscrollcommand=xscrollbar.set, yscrollcommand=yscrollbar.set)
		self.overview_canvas.grid(row=0, column=0, sticky=tk.NSEW)

		xscrollbar.config(command=self.overview_canvas.xview)
		yscrollbar.config(command=self.overview_canvas.yview)

		self.right_panel.add(self.overview_frame, text=fish.translate("tab","overview",os.path.join("meta")))

	############################ ANIMATION FUNCTIONS HERE ################################

	def initialize_sprite_animation(self):
		self.frames_left_before_freeze = CONST.MAX_FRAMES
		self.freeze_ray = True
		self.frame_number = 0
		self.sprite_coord = (100,100)    #an arbitrary default
		self.start_global_frame_timer()

	def update_sprite_animation(self):
		self.sprite.update_animation()

	def start_global_frame_timer(self):
		#called by play button
		if self.freeze_ray:     #if we were frozen before
			self.frames_left_before_freeze = CONST.MAX_FRAMES
			self.freeze_ray = False
			self.time_marches_forward()

	def advance_global_frame_timer(self):
		#move frame timer forward
		self.frame_number += 1
		self.frames_left_before_freeze = max(0, self.frames_left_before_freeze - 1)
		if self.frame_number >= CONST.MAX_FRAMES:   #just in case someone leaves this running for, say...forever
			self.reset_global_frame_timer()
		self.update_sprite_animation()

	def play_once(self):
		self.frames_left_before_freeze = self.sprite.frames_in_this_animation()
		if self.freeze_ray:   #if we were frozen before
			self.freeze_ray = False
			self.time_marches_forward()

	def reset_global_frame_timer(self):
		#called by radio reset button
		self.frame_number = 0
		self.pause_global_frame_timer()

	def pause_global_frame_timer(self):
		#called by pause button
		self.frames_left_before_freeze = 0
		self.freeze_ray = True
		self.update_sprite_animation()

	def rewind_global_frame_timer(self):
		#called by step radio button to pause and step backward
		self.frame_number = max(0,self.frame_number - 1)
		self.pause_global_frame_timer()

	def step_global_frame_timer(self):
		#called by step radio button to pause and step forward
		self.pause_global_frame_timer()
		self.advance_global_frame_timer()

	def go_to_previous_pose(self):
		self.frame_number = max(0,self.frame_number - self.sprite.frames_to_previous_pose())
		self.pause_global_frame_timer()

	def go_to_next_pose(self):
		self.frame_number = self.frame_number + self.sprite.frames_left_in_this_pose()
		self.pause_global_frame_timer()

	def time_marches_forward(self):
		start_time = time.perf_counter()
		MIN_WAIT = 5      #have to give the rest of the program time to work, and tkInter is not thread-safe
		FRAME_DELAY = 17  #equal to about ceiling(1000/60) in order to simulate 60 Hz (can't go faster without skipping frames due to PC monitor refresh rate)
		if self.frames_left_before_freeze > 0 and not self.freeze_ray:
			self.advance_global_frame_timer()
			end_time = time.perf_counter()
			lag = (end_time-start_time)*1000
			wait_time = int(FRAME_DELAY/self.current_speed - lag)
			self.timer_callback = self.master.after(max(wait_time,5), self.time_marches_forward)     #schedule next tick of the clock
		else:
			self.pause_global_frame_timer()

	def zoom_getter(self):
		return self.current_zoom

	def frame_getter(self):
		return self.frame_number

	def coord_getter(self):
		return self.sprite_coord

	########################### VCR CONTROLS HERE ######################################

	def get_vcr_controls(self):
		control_section = tk.Frame(self.left_panel, name="vcr_controls_section")
		widgetlib.right_align_grid_in_frame(control_section)

		def zoom_out(*args):
			self.current_zoom = max(0.5, self.current_zoom - 0.1)
			set_zoom_text()
			self.game.update_background_image()
			self.update_sprite_animation()
		def zoom_in(*args):
			self.current_zoom = min(4.0, self.current_zoom + 0.1)
			set_zoom_text()
			self.game.update_background_image()
			self.update_sprite_animation()
		def set_zoom_text():
			self.zoom_factor.set('x' + str(round(self.current_zoom, 1)) + ' ')

		def speed_down(*args):
			self.current_speed = max(0.1, self.current_speed - 0.1)
			set_speed_text()
		def speed_up(*args):
			self.current_speed = min(2.0, self.current_speed + 0.1)
			set_speed_text()
		def set_speed_text():
			self.speed_factor.set(str(round(self.current_speed * 100)) + '%')

		if not hasattr(self,"current_zoom"):
			self.current_zoom = 2              #starting zoom, if app is just started
		if not hasattr(self,"current_speed"):
			self.current_speed = 1             #starting speed, if app is just started
		if not hasattr(self,"frame_number"):
			self.frame_number = 0              #starting frame, if app is just started
		self.zoom_factor = tk.StringVar(control_section)
		self.speed_factor = tk.StringVar(control_section)

		set_zoom_text()
		set_speed_text()

		BUTTON_WIDTH = 7
		self.current_grid_cell = 0

		def make_vcr_label(textvariable, icon_name):
			icon_path = common.get_resource(icon_name,os.path.join("meta","icons"))
			image = tk.PhotoImage(file=icon_path) if icon_path else None
			vcr_label = tk.Label(control_section, image=image, anchor='e', width=BUTTON_WIDTH, textvariable=textvariable)
			vcr_label.grid(row = self.current_grid_cell//3,
						column = 1 + (self.current_grid_cell % 3),
						sticky=['nes'])
			self.current_grid_cell += 1
			return vcr_label

		def make_vcr_button(text, icon_name, command, side="right"):
			icon_path = common.get_resource(icon_name,os.path.join("meta","icons"))
			image = tk.PhotoImage(file=icon_path) if icon_path else None
			if side == "right":
				side = tk.RIGHT
			elif side == "left":
				side = tk.LEFT
			else:
				side = tk.NONE
			vcr_button = tk.Button(control_section, image=image, text=text, compound=side, width=BUTTON_WIDTH, command=command)
			vcr_button.image = image
			vcr_button.grid(row = self.current_grid_cell//3,
						column = 1 + (self.current_grid_cell % 3),
						sticky=['nesw','nesw','nesw'][self.current_grid_cell % 3])
			self.current_grid_cell += 1
			return vcr_button

		vcr_buttons = []
		zoom_factor_label = make_vcr_label(self.zoom_factor, None)
		zoom_out_button = make_vcr_button(fish.translate("vcr-controls","zoom-minus",os.path.join("meta")),None,zoom_out)
		zoom_in_button = make_vcr_button(fish.translate("vcr-controls","zoom-plus",os.path.join("meta")),None,zoom_in)
		vcr_buttons.append((zoom_factor_label,zoom_out_button,zoom_in_button,))

		speed_factor_label = make_vcr_label(self.speed_factor,None)
		speed_down_button = make_vcr_button(fish.translate("vcr-controls","speed-minus",os.path.join("meta")),None,speed_down)
		speed_up_button = make_vcr_button(fish.translate("vcr-controls","speed-plus",os.path.join("meta")),None,speed_up)
		vcr_buttons.append((speed_factor_label,speed_down_button,speed_up_button,))

		play_button = make_vcr_button(fish.translate("vcr-controls","play",os.path.join("meta")), "play.png", self.start_global_frame_timer)
		play_one_button = make_vcr_button(fish.translate("vcr-controls","play-one",os.path.join("meta")), "play-one.png", self.play_once)
		reset_button = make_vcr_button(fish.translate("vcr-controls","reset",os.path.join("meta")), None, self.reset_global_frame_timer)
		vcr_buttons.append((play_button,play_one_button,reset_button,))

		frame_back_button = make_vcr_button(fish.translate("vcr-controls","frame-backward",os.path.join("meta")), "frame-backward.png", self.rewind_global_frame_timer,"left")
		pause_button = make_vcr_button(fish.translate("vcr-controls","pause",os.path.join("meta")), "pause.png", self.pause_global_frame_timer)
		frame_forward_button = make_vcr_button(fish.translate("vcr-controls","frame-forward",os.path.join("meta")), "frame-forward.png", self.step_global_frame_timer)
		vcr_buttons.append((frame_back_button,pause_button,frame_forward_button,))

		step_back_button = make_vcr_button(fish.translate("vcr-controls","pose-backward",os.path.join("meta")), "step-backward.png", self.go_to_previous_pose, "left")
		null_label = make_vcr_label("", None)
		step_forward_button = make_vcr_button(fish.translate("vcr-controls","pose-forward",os.path.join("meta")), "step-forward.png", self.go_to_next_pose)
		vcr_buttons.append((step_back_button,null_label,step_forward_button,))

		return control_section

	def get_reload_button(self):
		reload_section = tk.Frame(self.left_panel, name="reload_section")
		widgetlib.center_align_grid_in_frame(reload_section)
		reload_button = tk.Button(reload_section, text=fish.translate("meta","reload",os.path.join("meta")), padx=20, command=self.sprite.reload)
		reload_button.grid(row=0,column=1)
		return reload_section

	############################ MENU BAR FUNCTIONS HERE ################################

	def open_file(self):
		#TODO: Give the user a chance to regret not saving their work
		filename = filedialog.askopenfilename(initialdir=self.working_dirs["file.open"], title="Select Sprite", filetypes=(("Supported Types","*.zspr *.png *.sfc *.smc"),))
		if filename:
			self.working_dirs["file.open"] = filename[:filename.rfind('/')]
			self.load_sprite(filename)

	def save_file_as(self):
		# Save a ZSPR or PNG.  TODO: When ZSPR export is implemented, switch this around so that ZSPR is the default
		filetypes = (("Portable Network Graphics","*.png"),("ZSPR Sprite","*.zspr"),("Retro Data Container","*.rdc"))
		filename = filedialog.asksaveasfilename(defaultextension=(".png",".zspr",".rdc"), initialdir=self.working_dirs["file.save"], title="Save Sprite As...", filetypes=filetypes)
		if filename:
			returnvalue = self.sprite.save_as(filename)
			if returnvalue:
				self.working_dirs["file.save"] = filename[:filename.rfind('/')]
				messagebox.showinfo("Save Complete", f"Saved as {filename}")
			else:
				messagebox.showerror("Not Yet Implemented",os.path.splitext(filename)[1][1:].upper() + " format not yet available for " + self.game.name + '/' + self.sprite.classic_name + " Sprites.")
			return returnvalue
		else:    #user cancelled out of the prompt, in which case report that you did not save (i.e. for exiting the program)
			return False

	def copy_into_ROM(self, inject=False):
		dest_filename = None
		if inject:
			dest_filename = filedialog.asksaveasfilename(defaultextension=".sfc", initialdir=self.working_dirs["export.dest"], title="Select ROM to Modify...", filetypes=(("Game Files","*.sfc *.smc"),))
			source_filename = dest_filename
		else:
			source_filename = filedialog.askopenfilename(initialdir=self.working_dirs["export.source"], title="Select Source ROM", filetypes=(("Game Files","*.sfc *.smc"),))
			if source_filename:
				_,file_extension = os.path.splitext(source_filename)
				if file_extension.lower() in ['.sfc','.smc']:
					default_extension = file_extension.lower()
				else:
					default_extension = ".sfc"
				dest_filename = filedialog.asksaveasfilename(defaultextension=default_extension, initialdir=self.working_dirs["export.dest"], title="Save Modified ROM As...", filetypes=(("Game Files","*.sfc *.smc"),))
		if dest_filename:
			rom = self.game.get_rom_from_filename(source_filename)
			modified_rom = self.sprite.inject_into_ROM(rom)
			modified_rom.save(dest_filename, overwrite=True)
			self.working_dirs["export.dest"] = dest_filename[:dest_filename.rfind('/')]
			self.working_dirs["export.source"] = source_filename[:source_filename.rfind('/')]
			messagebox.showinfo("Export success",f"Saved injected ROM as {dest_filename}")

	def copy_into_ROM_bulk(self, inject=False):
		source_filepath = None
		if inject:
			source_filepath = filedialog.askdirectory()
		else:
			raise AssertionError("Unsure if making copies fits this purpose well")

		source_filenames = []
		for r,d,f in os.walk(source_filepath):
			for file in f:
				_,file_extension = os.path.splitext(file)
				if file_extension.lower() in ['.sfc','.smc']:
					source_filenames.append(os.path.join(r,file))
		for source_filename in source_filenames:
			dest_filename = source_filename
			rom = self.game.get_rom_from_filename(source_filename)
			same_internal_name = self.game.internal_name == gamelib.autodetect_game_type_from_rom_filename(source_filename)
			is_zsm = "ZSM" in str(rom.get_name())
			if same_internal_name or (is_zsm and self.sprite.classic_name in ["Link","Samus"]):
				modified_rom = self.sprite.inject_into_ROM(rom)
				modified_rom.save(dest_filename, overwrite=True)

	def inject_into_ROM(self):
		self.copy_into_ROM(inject=True)

	def inject_into_ROM_bulk(self):
		self.copy_into_ROM_bulk(inject=True)

	def export_frame_as_png(self):
		filetypes = (("Portable Network Graphics","*.png"),)
		filename = filedialog.asksaveasfilename(defaultextension=(".png"), initialdir=self.working_dirs["export.frame-as-png"], title="Save Frame As...", filetypes=filetypes)
		if filename:
			returnvalue = self.sprite.export_frame_as_PNG(filename)
			if returnvalue:
				self.working_dirs["export.frame-as-png"] = filename[:filename.rfind('/')]
				messagebox.showinfo("Save Complete", f"Saved as {filename}")
			return returnvalue
		else:    #user cancelled out of the prompt, in which case report that you did not save (i.e. for exiting the program)
			return False

	def export_animation_as_gif(self):
		raise NotImplementedError()

	def export_animation_as_collage(self,orientation="horizontal"):
		if orientation == "vertical":
			raise NotImplementedError()
		filetypes = (("Portable Network Graphics","*.png"),)
		filename = filedialog.asksaveasfilename(defaultextension=(".png"), initialdir=self.working_dirs["export.animation-as-" + orientation[:1] + "collage"], title="Save " + orientation[:1].upper() + orientation[1:] + " Collage As...", filetypes=filetypes)
		if filename:
			returnvalue = self.sprite.export_animation_as_collage(filename,orientation)
			if returnvalue:
				self.working_dirs["export.animation-as-collage"] = filename[:filename.rfind('/')]
				messagebox.showinfo("Save Complete", f"Saved as {filename}")
			return returnvalue
		else:    #user cancelled out of the prompt, in which case report that you did not save (i.e. for exiting the program)
			return False

	def diagnostics(self):
		# Debugging purposes
		dims = {
			"window": {
				"width": 800,
				"height": 500
			},
			"textarea.characters": {
				"width": 120,
				"height": 50
			}
		}
		diag = tk.Tk()
		diag.title("SpriteSomething Diagnostics")
		diag.geometry(str(dims["window"]["width"]) + 'x' + str(dims["window"]["height"]))
		text = tk.Text(diag, width=dims["textarea.characters"]["width"], height=dims["textarea.characters"]["height"])
		text.pack()
		self.add_text_link_array(diagnostics.output(), text)

	def about(self):
		# Credit where credit's due
		dims = {
			"window": {
				"width": 300,
				"height": 200
			},
			"textarea.characters": {
				"width": 60,
				"height": 100
			}
		}
		def txtEvent(event):
			return "break"
		lines = [
				  "SpriteSomething v" + CONST.APP_VERSION,
				  "",
				  "Created by:",
				  "Artheau & Mike Trethewey",
				  "",
				  "Based on:",
				  "[SpriteAnimator](http://github.com/spannerisms/SpriteAnimator) by Spannerisms",
				  "[ZSpriteTools](http://github.com/sosuke3/ZSpriteTools) by Sosuke3",
				  # Assets from ZSpriteTools used with permission
		]
		about = tk.Tk()
		about.title(f"About {self.app_title}")
		about.geometry(str(dims["window"]["width"]) + 'x' + str(dims["window"]["height"]))
		about.resizable(tk.FALSE,tk.FALSE)
		about.attributes("-toolwindow", 1)
		text = tk.Text(about, bg='#f0f0f0', font='TkDefaultFont', width=dims["textarea.characters"]["width"], height=dims["textarea.characters"]["height"])
		text.pack()
		text.configure(cursor="arrow")
		self.add_text_link_array(lines, text)
		text.bind("<Button-1>", lambda e: txtEvent(e))

	def save_working_dirs(self):
		f = open("./resources/meta/working_dirs.json","w+")
		f.write(json.dumps(self.working_dirs,indent=2))

	def exit(self):
		#Until some kind of useful change/edit feature is implemented, no need to ask if they want to save their changes
		save_before_exit = False #messagebox.askyesnocancel(self.app_title,"Do you want to save before exiting?")
		if save_before_exit != None:
			if save_before_exit:
				saved = self.save_file_as()
				if saved:
					self.save_working_dirs()
					sys.exit(0)
			else:
				#messagebox.showwarning(self.app_title, "Death in Super Metroid loses progress since last save." + "\n" + "You have been eaten by a grue.")
				self.save_working_dirs()
				sys.exit(0)

	######################### HELPER FUNCTIONS ARE BELOW HERE ###############################

	def add_text_link_array(self,lines,textObject):
		# Gui.class
		# Add an array of text lines, linkifying as necessary
		#ins:
		# lines: Lines of text to add
		# textObject: Text object to add lines to
		hyperlink = HyperlinkManager(textObject)
		for line in lines:
			matches = re.search(r'(.*)\[(.*)\]\((.*)\)(.*)',line)
			if matches:
				def click1(url=matches.group(3)):
					webbrowser.open_new(url)
				textObject.insert(tk.INSERT, matches.group(1))
				textObject.insert(tk.INSERT, matches.group(2), hyperlink.add(click1))
				textObject.insert(tk.INSERT, matches.group(4))
				textObject.insert(tk.INSERT, "\n")
			else:
				textObject.insert(tk.INSERT, line + "\n")