# Kunal Naik
# Reddit TIL Feed App
# Version 2.1 - 09/1/15

# Importing modules
import json												# reddit api provides JSON
import urllib2 											# used to connect to reddit
import wx 												# app gui
import threading 										# threading for text sending loop
from twilio.rest import TwilioRestClient 				# twilio client for sending texts
from twilio.rest.exceptions import TwilioRestException 	# catching exception for invalid numbers

# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()

def EVT_RESULT(win, func):
	# define result event
	win.Connect(-1, -1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
	# simple event to carry arbitrary result data
	def __init__(self, data):
		# initialize result event
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_RESULT_ID)
		self.data = data

# thread for geting fact and sending texts
class sendThread(threading.Thread):

	# init thread class
	def __init__(self, wxObject):
		threading.Thread.__init__(self)
		self.wxObject = wxObject
		self.daemon = True
		self.stop_event = threading.Event()
		# start the thread
		self.start()

	# run thread
	def run(self):
		try:
			# function that uses twilio api to send sms
			def send_sms(msg, to, user_sid, user_token, user_t_number):
				sid = user_sid
				auth_token = user_token
				twilio_number = user_t_number
				client = TwilioRestClient(sid, auth_token)
				message = client.messages.create(body=msg, \
					from_=twilio_number, to=to)
			# repeat fact check variables
			fact = ""
			old_fact = ""
			til_url = "http://www.reddit.com/r/todayilearned/new/.json?limit=1"
			# gets new fact and calls send_sms
			while(not self.stop_event.is_set()):
				request = urllib2.Request(til_url, headers={ 'User-Agent': \
					'TIL_Feed/2.1 (by kunalnaik)' })
				json_obj = urllib2.urlopen(request)
				json_data = json.load(json_obj)
				# access title and puts it into a string
				fact = json_data["data"]["children"][0]["data"]["title"]
				# check if fact is a repeat
				if (fact != old_fact):
					send_sms(fact, to, user_sid, user_token, user_t_number)
				old_fact = fact
				# delay before retrying
				self.stop_event.wait(35)
			wx.PostEvent(self.wxObject, ResultEvent("status: STOPPED"))

		except TwilioRestException as e:
			print e
			wx.PostEvent(self.wxObject, ResultEvent("Invalid Number"))

	def abort(self):
		self.stop_event.set()

# class for app gui
class MyFrame(wx.Frame):

	def __init__(self, parent, title):
		# main frame and panel
		wx.Frame.__init__(self, parent, title=title, size=(300,200))
		panel = wx.Panel(self)
		# set frame icon
		self.icon = wx.Icon("icon.ico", wx.BITMAP_TYPE_ICO)
		self.SetIcon(self.icon)
		# info text
		welcome = ("Welcome to TIL Feed!\nThis program texts you whenever "
					"a\nnew fact is posted on /r/todayilearned.")
		info_text = wx.StaticText(panel, label=welcome, style=wx.ALIGN_CENTRE, \
			pos=(37,23))
		# start Button
		global start_button
		start_button = wx.Button(panel, label="start", pos=(80, 82), \
			size=(50,30))
		start_button.Disable()
		self.Bind(wx.EVT_BUTTON, self.start_thread, start_button)
		# exit Button
		stop_button = wx.Button(panel, label="stop", pos=(150, 82), \
			size=(50,30))
		self.Bind(wx.EVT_BUTTON, self.stop_thread, stop_button)
		# settings Button
		settings_button = wx.StaticBitmap(panel, -1, wx.Bitmap("gear.png", \
			wx.BITMAP_TYPE_ANY), (255, 133), (25, 25))
		settings_button.Bind(wx.EVT_LEFT_DOWN, self.open_settings)
		# status text
		self.status_text = wx.StaticText(panel, label="status: STOPPED", \
			style=wx.ALIGN_CENTRE, pos=(95,125))
		# Set up event handler for any worker thread results
		EVT_RESULT(self, self.update_display)
		# show frame
		self.Centre()
		self.Show(True)

	# starts thread
	def start_thread(self, event):
		# phone number input
		num_box = wx.TextEntryDialog(None, "Enter your phone number:", \
			"Phone Number", "+12345678900")
		if num_box.ShowModal()==wx.ID_OK:
			# sets number to be texted
			global to
			to = num_box.GetValue()
			# changes status to running and starts thread
			self.status_text.SetLabel("status: RUNNING")
			self.send_text = sendThread(self)
			# disables start button to prevent multiple thread calls
			start_button.Disable()

	# stops thread
	def stop_thread(self, event):
		self.send_text.abort()

	# opens settings menu
	def open_settings(self, event):

		global user_sid
		global user_token
		global user_t_number
		sid_box = wx.TextEntryDialog(None, "Enter your Account SID:", "Account SID", \
			"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
		if sid_box.ShowModal()==wx.ID_OK:
			user_sid = sid_box.GetValue()
			token_box = wx.TextEntryDialog(None, "Enter your Auth Token:", "Auth Token", \
				"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
			if token_box.ShowModal()==wx.ID_OK:
				user_token = token_box.GetValue()
				t_number_box = wx.TextEntryDialog(None, "Enter your twilio phone number:", \
					"Twilio Phone Number", "+12345678900")
				if t_number_box.ShowModal()==wx.ID_OK:
					user_t_number = t_number_box.GetValue()
					start_button.Enable()
				else:
					user_sid = None
					user_token = None
			else:
				user_sid = None

	# updates status when needed
	def update_display(self, msg):
		t = msg.data
		self.status_text.SetLabel("%s" % t)
		# re-enables start button when thread complete
		start_button.Enable()


# main
if __name__=='__main__':
	app = wx.App(False)
	frame = MyFrame(None, 'TIL Feed')
	app.MainLoop()
