#!/user/bin/env python

import signal
import buttonshim
import time
import subprocess
import json
import requests

from board import SCL, SDA
import busio
import adafruit_ssd1306

from PIL import Image, ImageDraw, ImageFont

# pi-hole api
api_url = 'http://localhost/admin/api.php'

# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)

# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

# Clear display.
disp.fill(0)
disp.show()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position
# for drawing shapes.
x = 0

# Load nice silkscreen font
font = ImageFont.truetype('/home/pi/slkscr.ttf', 8)



print("""
	Pi-Hole Button Control Running....

	Press Ctrl+C to Exit.
	""")

#Cycle and clear LEDs on startup (visual indication the script is running)
buttonshim.set_pixel(255,0,0)
time.sleep(0.3)
buttonshim.set_pixel(0,255,0)
time.sleep(0.3)
buttonshim.set_pixel(0,0,255)
time.sleep(0.3)
buttonshim.set_pixel(0,0,0)
pressId = 0

while True:

	def getAndPrintStats():
		draw.rectangle((0, 0, width, height), outline=0, fill=0)

		# Shell scripts for system monitoring from here :
		# https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
		cmd = "hostname -I | cut -d\' \' -f1 | tr -d \'\\n\'"
		IP = subprocess.check_output(cmd, shell=True).decode("utf-8")
		cmd = "hostname | tr -d \'\\n\'"
		HOST = subprocess.check_output(cmd, shell=True).decode("utf-8")
		cmd = "top -bn1 | grep load | awk " \
			  "'{printf \"CPU Load: %.2f\", $(NF-2)}'"
		CPU = subprocess.check_output(cmd, shell=True).decode("utf-8")
		cmd = "free -m | awk 'NR==2{printf " \
			  "\"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
		MemUsage = subprocess.check_output(cmd, shell=True).decode("utf-8")
		cmd = "df -h | awk '$NF==\"/\"{printf " \
			  "\"Disk: %d/%dGB %s\", $3,$2,$5}'"
		Disk = subprocess.check_output(cmd, shell=True).decode("utf-8")

		# Pi Hole data!
		try:
			r = requests.get(api_url)
			data = json.loads(r.text)
			DNSQUERIES = data['dns_queries_today']
			ADSBLOCKED = data['ads_blocked_today']
			CLIENTS = data['unique_clients']
		except KeyError:
			time.sleep(1)

		draw.text((x, top), "IP: " + str(IP) +
				  "( " + HOST + ")", font=font, fill=255)
		draw.text((x, top + 8), "Ads Blocked: " +
				  str(ADSBLOCKED), font=font, fill=255)
		draw.text((x, top + 16), "Clients:     " +
				  str(CLIENTS), font=font, fill=255)
		draw.text((x, top + 24), "DNS Queries: " +
				  str(DNSQUERIES), font=font, fill=255)

		# skip over original stats
		# draw.text((x, top+8),     str(CPU), font=font, fill=255)
		# draw.text((x, top+16),    str(MemUsage),  font=font, fill=255)
		# draw.text((x, top+25),    str(Disk),  font=font, fill=255)

		# Display image.
		disp.image(image)
		disp.show()
		time.sleep(10)
		disp.fill(0)
		disp.show()

	def DisablePiholeTimer(numSecs):
		global pressId
		loopId = pressId
		for i in range(0,numSecs):
			disp.fill(0)
			disp.show()
			if ( loopId != pressId):
				print ("Ending loop with ID: " + str(loopId))
				return
			print ("Pi-Hole disabled for " + str(numSecs-i))
			draw.text((x, top + 24), "Pi-Hole disabled for " + str(numSecs-i), font=font, fill=255)
			disp.image(image)
			disp.show()
			buttonshim.set_pixel(255,255,0)
			time.sleep(0.5)
			buttonshim.set_pixel(255,150,0)
			time.sleep(0.5)
		buttonshim.set_pixel(0,0,0)
		disp.fill(0)
		disp.show()
		print ("Pi-Hole reenabled")

	def SuspendPihole():
		global pressId
		loopId = pressId
		print ("Pi-Hole suspended")
		while (loopId == pressId):
			buttonshim.set_pixel(255,0,0)
			time.sleep(0.5)
			buttonshim.set_pixel(0,0,0)
			time.sleep(0.5)

	def EnablePihole():
		global pressId
		loopId = pressId
		print ("Pi-Hole enabled")
		for i in range(0,2):
			buttonshim.set_pixel(0,255,0)
			time.sleep(0.3)
			buttonshim.set_pixel(0,0,0)
			time.sleep(0.3)


	@buttonshim.on_press(buttonshim.BUTTON_A)
	def button_a(button, pressed):
		print ("Disabling Pi-Hole for 3s")
		global pressId
		pressId += 1
		subprocess.call(['pihole','disable','3s'])
		DisablePiholeTimer(int(3))

	@buttonshim.on_press(buttonshim.BUTTON_B)
	def button_b(button, pressed):
		print ("Disabling Pi-Hole for 1800s")
		global pressId
		pressId += 1
		subprocess.call(['pihole','disable','1800s'])
		DisablePiholeTimer(int(1800))

	@buttonshim.on_press(buttonshim.BUTTON_C)
	def button_c(button, pressed):
		print ("getting stats...")
		global pressId
		pressId += 1
		getAndPrintStats()

	@buttonshim.on_press(buttonshim.BUTTON_D)
	def button_d(button, pressed):
		print ("Suspending Pi-Hole")
		global pressId
		pressId += 1
		subprocess.call(['pihole','disable'])
		SuspendPihole()

	@buttonshim.on_press(buttonshim.BUTTON_E)
	def button_e(button, pressed):
		print ("Enabling Pi-Hole")
		global pressId
		pressId += 1
		subprocess.call(['pihole','enable'])
		EnablePihole()



	signal.pause()

