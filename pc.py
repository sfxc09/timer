from kivy.app import App
from kivy.config import Config
Config.set('graphics', 'width', '500')
Config.set('graphics', 'height', '750')
from kivy.lang.builder import Builder
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.audio import SoundLoader
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.properties import ListProperty
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.clock import Clock
import re, sqlite3, time

# globals for sound urls & names
end_tone, remind_tone = [None,None], [None,None]
#TODO replace reading/writing total_seconds to file with using global variable?

class Timer:
	def start(self):
		self.start_time = time.perf_counter()
		self.app = App.get_running_app()
		# countdown timer
		self.time = self.app.root.ids.time.text # time label
		self.hours = int(self.time[0] + self.time[1]) # xx:00:00
		self.minutes = int(self.time[3] + self.time[4]) # 00:xx:00
		self.seconds = int(self.time[6] + self.time[7])  # 00:00:xx
		
		self.current_total = (self.hours*60*60) + (self.minutes*60) + (self.seconds) # total seconds
		reminder_text = self.app.root.ids.reminder_spinner.text
        #TODO make 'Remind every.. [Off]' disappear when checkbutton makes the spinner active, and put it back when spinner is made inactive again. 
		if reminder_text not in 'Remind every.. [Off]' and self.app.root.ids.reminder_spinner.disabled is False:
			if reminder_text[2] == 'm' or reminder_text[3] == 'm':	# 1 or 2 digit number 'm'inutes
				self.reminder = int(reminder_text[0] + reminder_text[1]) * 60  # to seconds
			else: # 's'econds
				self.reminder = int(reminder_text[0] + reminder_text[1])
			with open('content/reminder', 'w') as f:
					f.write(str(self.reminder))
		
		self.clock_event = Clock.schedule_interval(self.update_time, 1) # call every second
				
	def update_time(self, dt): 
		if self.seconds == 0:
			if self.minutes > 0:
				self.minutes -= 1
				self.seconds = 60
			elif self.hours > 0:
				self.hours -= 1
				self.minutes = 59
				self.seconds = 60
			else: # if play is pressed when 00:00:00
				self.app.root.ids.play_pause.source = 'img/play.png'
				return self.stop()
		
		self.current_total -= 1 
		self.seconds -= 1 
		self.app.root.ids.timer_progress.value += 1
		
		def label_format(data): # add '0' before time if only 1 digit present (below 10)
			return str(data) if len(str(data)) == 2 else '0' + str(data)
		
		# reminder alarm -> self.reminder after self.reminder has passed -> (seconds_set - (seconds_set - seconds_passed)) - reminder_value
		try: # catch 'no self.reminder exists' if no reminder was set
			with open('content/total_time_set', 'r') as f: 
				total_seconds = int(f.read())
			if (((total_seconds - self.current_total) == self.reminder and self.current_total is not 0)): # not 0 to avoid conflicts with main alarm 
				with open('content/total_time_set', 'w') as f: 
					f.write(str(total_seconds - self.reminder))
				reminder_bell = SoundLoader.load(remind_tone[0])
				reminder_bell.play()
		except Exception as e:
			pass
		
		# update label	
		self.app.root.ids.time.text = label_format(self.hours) + ':' + label_format(self.minutes) + ':' + label_format(self.seconds)
		
		if self.current_total == 0: # countdown ended
			alarm = SoundLoader.load(end_tone[0])
			alarm.play()
			self.app.root.ids.play_pause.source = 'img/play.png'
			self.stop()	
		
	def stop(self):
		print('\n\n\n\n\n\n\n\n'+str((time.perf_counter()-self.start_time))+'\n\n\n\n\n\n\n\n\n')
		self.clock_event.cancel()
	
		
		
class CustomInput(TextInput):
	def __init__(self, **kwargs):
		# have to pass **kwargs because kwargs would just be a dictionary, so if arguments are __init__(kwarg1=something, kwarg2=something), 
		# a dict is passed, which ofc won't work as dict is positional argument
		# likewise if arguments are __init__(**kwargs), passing a dict is again, a positional argument, which won't work
		super().__init__(**kwargs)
		self.input_type = 'number'
		
	def insert_text(self, string, from_undo=False):
		if len(self.text) == 2 and re.compile('0\\d').search(self.text) is None: # is xx already present aka not '00'?
			return # don't allow any more chars to be entered if first digit is not 0
			
		if re.compile('\\d').search(string): # is inputted char a digit 0-9? 			
			if self.text == '':
				self.text = '0' + string # add 0 before to keep formatting after simple	
				return
			if re.compile('0\\d').search(self.text): # format is 0x?
				if re.compile('0[0-5]').search(self.text) is None: # format of 2nd char more than 0-5 - 2nd char because the currently entered 'string' has not been entered into the input yet, not self.text yet, 
																						# so previously entered value is the x in 0x
					self.text = '0' + string # remove the original 2nd char as format can't be more than '59'
				else:	 # format of 2nd char IS 0-5
					self.text = self.text[-1] + string # remove leading zero
			else: # if backspace and self.text is 1 char
				self.text = self.text + string
				return 
			
			

class SetTime(Popup):	
	def __init__(self):
		super(SetTime, self).__init__()
		
		self.app = App.get_running_app()
		
		# size of widgets must be in relation to window size. since most phones have similar screen proportions, you just need to ensure that the widgets are scaled in proportion to the entire window
		# the user wont be changing the actual window size, just the pixel density will change across devices, so you just need to ensure that what look aesthetically pleasing for one phone sized window is created based on window size.
		self.hrs_input = CustomInput(hint_text='hh', multiline=False, size_hint=(None,None), \
											size=(self.app.root.width/16,self.app.root.height/22), input_type='number')
		self.hrs_input.pos = (self.app.root.width / 2.35) - (self.hrs_input.width / 2), \
									(self.app.root.height / 2) - (self.hrs_input.height / 2)
		self.min_input = CustomInput(hint_text='mm', multiline=False, size_hint=(None,None), \
											size=(self.app.root.width/16,self.app.root.height/22)) 
		self.min_input.pos = (self.app.root.width / 2) - (self.min_input.width / 2), \
									(self.app.root.height / 2) - (self.min_input.height / 2)
		self.sec_input = CustomInput(hint_text='ss', multiline=False, size_hint=(None,None), \
											size=(self.app.root.width/16,self.app.root.height/22)) 
		self.sec_input.pos = (self.app.root.width / 1.75) - (self.sec_input.width / 2), \
									(self.app.root.height / 2) - (self.sec_input.height / 2)
		
		self.input_layout = FloatLayout(size_hint_x=None)
		self.input_layout.add_widget(self.hrs_input)
		self.input_layout.add_widget(self.min_input)
		self.input_layout.add_widget(self.sec_input)
		
		confirm_btn = Button(text='Confirm', size_hint=(None,None))
		confirm_btn.size = ((self.app.root.width / 1.55), (self.app.root.height / 14))
		confirm_btn.pos = ((self.app.root.width / 2) - (confirm_btn.width / 2), \
									(self.app.root.height / 2.35) - (confirm_btn.height / 2))
		confirm_btn.bind(on_press=self.confirm_btn_press)
		
		boxlayout = FloatLayout()
		boxlayout.add_widget(self.	input_layout)
		boxlayout.add_widget(confirm_btn)
		
		self.popup = Popup(title='Set time period', content=boxlayout, size_hint=(.7, .25))

	
	def load_popup(self):
		self.popup.open()
	def close_popup(self):	
		self.popup.dismiss()
	
	def confirm_btn_press(self, widget):
		app = App.get_running_app()
		# in case user didn't manually set '00'
		for inpt in [self.hrs_input, self.min_input, self.sec_input]:
			if inpt.text == '':
				inpt.text = '00'
			
		app.root.ids.time.text = ':'.join([self.hrs_input.text, self.min_input.text, self.sec_input.text])
		
		total_seconds = (int(self.hrs_input.text)*60*60) + (int(self.min_input.text)*60) + int(self.sec_input.text)
		with open('content/total_time_set', 'w') as f:  # total_seconds must not be dependent on play_pause
			f.write(str(total_seconds))
		
		app.root.ids.timer_progress.max = total_seconds 
		app.root.ids.timer_progress.value = 0
		self.close_popup()
		
		
		
class SettingsPopup(Widget):
	def __init__(self):
		super().__init__()
		self.app = App.get_running_app()
		
		tone_label = Label(text='End tone ', size_hint=(None,None))
		tone_label.pos = (self.app.root.width / 3.3) - (tone_label.width / 2), \
								(self.app.root.height / 1.4) - (tone_label.height / 2)
		tone_spinner = Spinner(values=('sitar flute', 'sitar', 'tone 1', 'classical', 'tone 2', 'tone 3'),size_hint=(None,None), \
								size=(self.app.root.width / 3, self.app.root.height / 18), text=end_tone[1])
		tone_spinner.pos = (self.app.root.width / 1.7) - (tone_spinner.width / 2), \
									(self.app.root.height / 1.4) - (tone_spinner.height / 2)
		tone_spinner.bind(text=self.tone_set)
	
		notif_label = Label(text='Notif tone ', size_hint=(None,None))
		notif_label.pos = (self.app.root.width / 3.3) - (tone_label.width / 2), \
								(self.app.root.height / 1.65) - (tone_label.height / 2)
		notif_spinner = Spinner(values=('tone 1', 'bells ring', 'bells 1', 'bell 2', 'bell 3d'), size_hint=(None,None), \
								size=(self.app.root.width / 3, self.app.root.height / 18), text=remind_tone[1])
		notif_spinner.pos = (self.app.root.width / 1.7) - (notif_spinner.width / 2), \
									(self.app.root.height / 1.65) - (notif_spinner.height / 2)
		notif_spinner.bind(text=self.notif_set)
									
		background_label = Label(text='Background ', size_hint=(None,None))
		background_label.pos = (self.app.root.width / 3.3) - (background_label.width / 2), \
								(self.app.root.height / 2) - (background_label.height / 2)
		background_spinner = Spinner(values=('cyberpunk', 'abstract 1', 'unknown', 'abstract 2', 'abstract 3', 'default?'), size_hint=(None,None), \
								size=(self.app.root.width / 3, self.app.root.height / 18), text=self.app.background[1])
		background_spinner.pos = (self.app.root.width / 1.7) - (background_spinner.width / 2), \
									(self.app.root.height / 2) - (background_spinner.height / 2)
		background_spinner.bind(text=self.background_set)
		
		close_btn = Button(text='close [X]', size_hint=(None,None), \
									size=(self.app.root.width/6, self.app.root.height/18))
		close_btn.pos = (self.app.root.width / 1.35) - (close_btn.width / 2), \
								(self.app.root.height / 5) - (close_btn.height / 2)
		close_btn.bind(on_release=lambda instance: self.popup.dismiss())
		about_btn = Button(text='about?', size_hint=(None,None), background_normal='img/alpha.png', \
									size=(self.app.root.width/6, self.app.root.height/18))
		about_btn.bind(on_release=self.about_dialog)
		about_btn.pos = (self.app.root.width/4) - (about_btn.width / 2), \
								(self.app.root.height/5) - (about_btn.height / 2)
		
		floatlayout = FloatLayout()
		for widget in [tone_label, tone_spinner, notif_label, notif_spinner, close_btn, 
								about_btn, background_label, background_spinner]:
			floatlayout.add_widget(widget)
		
		self.popup = Popup(title='settings', content=floatlayout, size_hint=(.7, .7),auto_dismiss=False)
		self.popup.open()
		
	
	def tone_set(self, spinner, text):
		tone_urls = ['content/sitar_flute_rhythm_2.ogg', 'content/sitar.ogg', 'content/good-morning.ogg', \
							'content/classical_music.ogg', 'content/bell_sms.ogg', 'content/bell_message.ogg']
		global end_tone
		end_tone = [tone_urls[spinner.values.index(text)], text]  # tone_urls ordered same as spinner.values so selecting value will select appropriate url from tone_urls
		# edit settings database with relevant info so change remains on restart
		conn = sqlite3.connect('content/saved_settings.db')
		cursor = conn.cursor()
		cursor.execute('''UPDATE settings
								SET end_tone_url = ?,
										end_tone = ?''', (end_tone[0], end_tone[1]))
		conn.commit()
		conn.close()
	
		
	def notif_set(self, spinner, text):
		tone_urls = ['content/meditation.ogg', 'content/bells_ringing.ogg', 'content/bells_msg_tone.ogg', \
							'content/Bell1.wav', 'content/bell_3d_sms.ogg']
		global remind_tone
		remind_tone = [tone_urls[spinner.values.index(text)], text]
		# edit settings database with relevant info so change remains on restart
		conn = sqlite3.connect('content/saved_settings.db')
		cursor = conn.cursor()
		cursor.execute('''UPDATE settings
								SET remind_tone_url=?,
									remind_tone=?''',(remind_tone[0], remind_tone[1]))
		conn.commit()
		conn.close()
		
	def background_set(self, spinner, text):
		urls = ['img/background1.jpg','img/background2.jpg', 'img/background3.png', \
					'img/background4.png', 'img/background6.png', 'img/img3_blur.jpg']
		self.app.background = [urls[spinner.values.index(text)], text]
		# edit settings database with relevant info so change remains on restart
		conn = sqlite3.connect('content/saved_settings.db')
		cursor = conn.cursor()
		cursor.execute('''UPDATE settings SET background=?,background_url=?''', (self.app.background[1], self.app.background[0]))
		conn.commit()
		conn.close()
		
		
	def about_dialog(self, instance):
		label = Label(text='''Meditate is a timer - primarily for meditation use  Mediate was developed using Kivy and Python3, by a novice fellow seeking to further their programming \'expertise\' \n Work is still in progress :) \n\nCopyright © 2018 [font=content/TYPEWR_B.TTF]Wistful Creations[/font]\nLicensed under GPLv3''',halign='center', valign='center', markup=True)
		label.text_size = self.app.root.width / 2.5, self.app.root.height / 2.5
		popup = Popup(title='About', content=label, size_hint=(0.5,0.5))
		popup.open()
		


class ChangeButton(Button):
	def on_release(self):
		app = App.get_running_app()
		if app.root.ids.play_pause.source == 'img/play.png':
			SetTime().load_popup()
		

		
class PlayButton(Button, Timer):
	def on_press(self):
		app = App.get_running_app()
		if app.root.ids.play_pause.source == 'img/play.png':
			app.root.ids.play_pause.source = 'img/pause.png'
			self.start()
		else:
			app.root.ids.play_pause.source = 'img/play.png'
			self.stop()
			


class ResetButton(Button):
	def on_press(self):
		app = App.get_running_app()
		if app.root.ids.play_pause.source == 'img/play.png':
			app.root.ids.time.text = '00:00:00'
			app.root.ids.timer_progress.value = 0



class CustomCheckBox(CheckBox):
	def on_state(self, widget, value):
		if value=='down':
			App.get_running_app().root.ids.reminder_spinner.disabled = False
			self.active = True
		else:
			App.get_running_app().root.ids.reminder_spinner.disabled = True
			self.active = False	



class SettingsButton(Button):
	def on_release(self):
		SettingsPopup()



class BreathTimer(App):
	background = ListProperty([None,None])
	def build(self):
		global end_tone, remind_tone
		# database used to store chosen settings so they remain on restart
		#end_tone_url, end_tone, remind_tone_url, remind_tone, background, background_url, show_again - columns
		conn = sqlite3.connect('content/saved_settings.db')
		cursor = conn.cursor() # cursor obect required to access database
		cursor.execute('SELECT remind_tone_url FROM settings')
		remind_tone[0] = cursor.fetchone()[0]
		cursor.execute('SELECT remind_tone FROM settings')
		remind_tone[1] = cursor.fetchone()[0]
		cursor.execute('SELECT end_tone_url FROM settings')
		end_tone[0] = cursor.fetchone()[0]
		cursor.execute('SELECT end_tone FROM settings')
		end_tone[1] = cursor.fetchone()[0]
		cursor.execute('SELECT background_url FROM settings')
		self.background[0] = cursor.fetchone()[0]
		cursor.execute('SELECT background FROM settings')
		self.background[1] = cursor.fetchone()[0]
		conn.close()
		return Builder.load_file('design.kv')
		
		
		
		
BreathTimer().run()
