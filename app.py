import app
import settings
import socket
import network
import time
import neopixel
import ntptime
import apps.Ipsw_Tildagon_GPSUMap.maps_api as maps_api

from machine import Pin
from events.input import Buttons, BUTTON_TYPES, ButtonDownEvent, ButtonUpEvent
from system.eventbus import eventbus
from system.hexpansion.util import get_app_by_vid_pid

np = neopixel.NeoPixel(Pin(21), 6)

api = maps_api.MapsAPI(
    "https://maps-api.emfcamp.info",
    "1b4ee1a37eed742f6b49bdda58abb28de4eda309ef8f6a120d90951f711918e7"
)

class GPSUMap(app.App):

    def __init__(self):
                
        self.HTTP_SEND_MIN_INTERVAL_MS = 5000   # 5 seconds
        self.LAST_HTTP_SEND = 0

        # QR setup
        self.TARGET_SIZE = 140
        self.NATIVE_SIZE = 25

        # Center target dimensions within the -120 to +120 screen area
        self.START_X = -self.TARGET_SIZE // 2  # -70
        self.START_Y = -self.TARGET_SIZE // 2  # -70

        self.username = settings.get("name") or "Unknown"
        print("Badge user:", self.username)
        
        self.gpsumap_editkey = settings.get("gpsumap_editkey") or ""
        print("Badge Location Edit Key:", self.gpsumap_editkey)

        self.wlan = network.WLAN(network.STA_IF)

        while not self.wlan.isconnected():
            print("Connecting to network...")
            time.sleep(1)

        print("Connected! IP:", self.wlan.ifconfig()[0])
        self.rssi = self.wlan.status('rssi')
        
        self.gps = get_app_by_vid_pid(0x7CAB, 0xBEAC)

        self.last_position = None
        self.last_speed = 0
        self.last_bearing = 0

        if self.gps:
            eventbus.on(
                self.gps.GPSEvent,
                self.handle_gps_event,
                self
            )
            print("GPS Hexpansion found")
        else:
            print("GPS Hexpansion NOT found")

        self.sync_time()

        self.button_states = Buttons(self)
        eventbus.on(ButtonDownEvent, self._handle_buttondown, self)
        eventbus.on(ButtonUpEvent, self._handle_buttonup, self)

    def load_qr(self):
        self.native_qr = [
            [1,1,1,1,1,1,1,0,0,0,1,0,1,0,0,0,1,0,1,1,1,1,1,1,1],            
            [1,0,0,0,0,0,1,0,1,0,1,0,0,1,1,1,0,0,1,0,0,0,0,0,1],            
            [1,0,1,1,1,0,1,0,0,0,0,0,1,1,0,0,1,0,1,0,1,1,1,0,1],            
            [1,0,1,1,1,0,1,0,1,1,1,0,1,1,1,1,0,0,1,0,1,1,1,0,1],            
            [1,0,1,1,1,0,1,0,0,1,0,0,0,0,1,0,1,0,1,0,1,1,1,0,1],            
            [1,0,0,0,0,0,1,0,1,1,0,1,1,0,0,0,0,0,1,0,0,0,0,0,1],            
            [1,1,1,1,1,1,1,0,1,0,1,0,1,0,1,0,1,0,1,1,1,1,1,1,1],            
            [0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,1,0,0,0,0,0,0,0,0],            
            [1,1,1,1,1,0,1,1,1,1,0,1,0,0,0,1,1,1,0,1,0,1,0,1,0],
            [1,1,0,0,0,1,0,1,1,0,1,0,1,1,0,1,0,0,0,1,0,0,0,1,1],            
            [1,0,0,1,0,0,1,0,1,0,1,0,0,1,1,0,0,1,1,0,1,1,1,1,0],            
            [0,1,0,1,1,1,0,0,0,0,0,0,1,1,0,0,1,0,0,1,0,1,0,0,0],            
            [0,1,0,0,1,0,1,0,0,1,1,0,1,0,1,1,0,0,1,1,0,0,0,1,1],            
            [1,0,0,1,1,1,0,0,1,0,0,0,0,0,0,0,1,1,0,1,1,0,0,1,1],            
            [1,0,0,0,0,1,1,1,0,0,1,1,1,0,0,0,0,1,1,0,1,0,1,0,1],            
            [1,0,1,0,0,1,0,0,0,1,1,1,0,0,1,0,0,0,0,1,0,1,0,1,1],            
            [1,0,1,1,0,0,1,0,0,0,1,1,0,0,0,1,1,1,1,1,1,1,0,0,1],
            [0,0,0,0,0,0,0,0,1,0,1,0,1,1,1,1,1,0,0,0,1,0,0,0,1],            
            [1,1,1,1,1,1,1,0,1,0,0,0,0,1,1,1,1,0,1,0,1,0,1,1,1],            
            [1,0,0,0,0,0,1,0,0,0,0,0,1,1,0,1,1,0,0,0,1,1,0,0,0],            
            [1,0,1,1,1,0,1,0,1,1,0,0,1,0,1,1,1,1,1,1,1,0,1,0,0],            
            [1,0,1,1,1,0,1,0,1,1,1,0,0,0,0,0,1,0,1,1,0,1,0,1,1],            
            [1,0,1,1,1,0,1,0,1,0,0,1,1,0,0,0,0,1,1,1,0,1,1,0,1],            
            [1,0,0,0,0,0,1,0,1,0,1,1,0,0,1,0,0,1,1,0,1,0,1,1,0],            
            [1,1,1,1,1,1,1,0,1,1,1,1,0,0,0,0,1,0,0,1,0,1,1,1,1]
        ]

    def sync_time(self):
        try:
            ntptime.settime()
            return True
        except Exception as e:
            print("NTP failed:", e)
            return False

    def on_resume(self):
        print("resumed")
    
    def on_pause(self):
        print("paused")

    def _handle_buttondown(self, event: ButtonDownEvent):
        if BUTTON_TYPES["LEFT"] in event.button:
            print("Left Button Down")            
            self.send_location(self.last_position, self.last_speed, self.last_bearing,1)
            time.sleep(1)
            self.button_states.clear()

        if BUTTON_TYPES["RIGHT"] in event.button:
            print("Right Button Down")
            self.button_states.clear()

        if BUTTON_TYPES["DOWN"] in event.button:            
            self.button_states.clear()

        if BUTTON_TYPES["CANCEL"] in event.button:
            self.button_states.clear()
            self.minimise()
    
    def _handle_buttonup(self, event: ButtonUpEvent):
        if BUTTON_TYPES["LEFT"] in event.button:
            print("Left Button Up")
            self.button_states.clear()

        if BUTTON_TYPES["RIGHT"] in event.button:
            print("Right Button Up")
            self.button_states.clear()

    def on_destroy(self):
        print("I'm outta here!")
        

    def flasher(self):
        # alternate every 1 second
        return (time.ticks_ms() // 1000) % 2

    def maps_api_call(self,pos,speed,bearing,forced=0,use_test_data=0):        
        
        if use_test_data:
            lat = 52
            lon = 1
        else:
            lat, lon = pos
        
        # If I dont have an edit key
            #  create a location and get an edit key
    
        if settings.get("gpsumap_editkey") == "":
            print("No stored edit key, create a location")
        
            status, location = api.create_badge_location(
                name=self.username,
                latitude=lat,
                longitude=lon,
                description=""
            )
            
            # Check if the API call was a success
            if status == 201:
                print("Update successful for " + self.username)
                settings.set("gpsumap_editkey",location["editToken"])
                settings.save()
            else:
                print(f"HTTP: {status}")
                np[0] = (255, 0, 0)
                np.write()
                time.sleep(0.15)
                np[0] = (0, 0, 0)
                
        # I have an edit key, so lets check the GPS speed and see if I should send
        # an update with the key I have
        
        else:
        
            print("Using stored edit key")
        
            # only send if I am moving to save battery mostly
            if isinstance(speed, (int, float)) and (speed > 0 or forced == 1):

                print("I am moving (or forcing an update)")
                
                self.rssi = self.wlan.status('rssi')
                y, m, d, hh, mm, ss, wd, yd = time.localtime()
                self.time_string = f"{hh:02d}:{mm:02d}:{ss:02d}"
                
                status, updated = api.update_badge_location(
                    self.gpsumap_editkey,
                    self.username,
                    lat,
                    lon,
                    self.time_string + "UTC Speed: " + str(speed) + " Bearing: " + str(bearing) + " RSSI: " + str(self.rssi)
                )
                                
                # I need to check if the update was a success, as I might need to wipe a timed out edit key
                # Some LED debug also
                
                if status in {400,404}:
                    
                    print("Token I had didnt work, got HTTP: " + str(status))
                    
                    # clear working key
                    self.gpsumap_editkey = ""
                    
                    # clear saved key
                    settings.set("gpsumap_editkey","")
                    settings.save()
                    print("Invalid edit token, wiped stored token")
                    # flash a Neopixel LED Orange
                    np[0] = (255, 165, 0)
                    np.write()
                    time.sleep(0.15)
                    np[0] = (0, 0, 0)
                    np.write()
                elif status == 200:
                    
                    print("Updated for " + self.username)
                    
                    # flash a Neopixel LED Green
                    np[0] = (0, 255, 0)
                    np.write()
                    time.sleep(0.15)
                    np[0] = (0, 0, 0)
                    np.write()
                else:
                    
                    print("Some other error, I dunno")
                    
                    # flash a Neopixel LED Red
                    np[0] = (255, 0, 0)
                    np.write()
                    time.sleep(0.15)
                    np[0] = (0, 0, 0)
                    np.write()                    
                                
            else:
                
                print("Speed zero, not sending anything")
        
        
        
        
        

    def send_location(self, pos, speed, bearing, forced):
        
        # get badge username
        user = self.username
                        
        # Check if GPS is Fixed
        if ( isinstance(pos, (tuple, list)) and len(pos) == 2 ):
            
            # position, speed, bearing, force_update, use_test_data
            self.maps_api_call(pos,speed,bearing,forced,0)
                    
        else:
        
            # IS NOT FIXED          
            print("Not fixed...")
            
            # To facilitate indoor testing ! Comment out for release
            # self.maps_api_call(pos,0,2,1,1)
  

    def handle_gps_event(self, event):

        self.last_position = event.position
        self.last_speed = event.speed
        self.last_bearing = event.bearing

        print("GPS Event")
        print("Position:", event.position)
        print("Speed:", event.speed)
        print("Bearing:", event.bearing)
        
        now = time.ticks_ms()
        
        # Try not to spam
        if time.ticks_diff(now, self.LAST_HTTP_SEND) >= self.HTTP_SEND_MIN_INTERVAL_MS:
        
            #lat, lon = event.position
            self.send_location(event.position, event.speed, event.bearing, 0)
            self.LAST_HTTP_SEND = now
        

    def update(self, delta):
        pass

    def display_qr(self, ctx):
        ctx.rgb(1.0, 1.0, 1.0).rectangle(-120, -120, 240, 240).fill()
        
        self.load_qr()
        
        # Direct pixel transformation loop using your requested method injection chaining
        for r in range(self.TARGET_SIZE):
            source_r = int(r * self.NATIVE_SIZE / self.TARGET_SIZE)
            y_pos = self.START_Y + r
            
            for c in range(self.TARGET_SIZE):
                source_c = int(c * self.NATIVE_SIZE / self.TARGET_SIZE)
                x_pos = self.START_X + c
                
                # Assign 0.0 for black modules, 1.0 for white modules (Tildagon color standard)
                if self.native_qr[source_r][source_c] == 1:
                    ctx.rgb(0.0, 0.0, 0.0).rectangle(x_pos, y_pos, 1, 1).fill()
                else:
                    ctx.rgb(1.0, 1.0, 1.0).rectangle(x_pos, y_pos, 1, 1).fill()
        return

    def draw(self, ctx):

        ctx.rgb(0, 0.2, 0).rectangle(-120, -120, 240, 240).fill()                       

        if not self.gps:
            ctx.rgb(1, 0, 0)
            ctx.move_to(-100, 0).text("No GPS")
            time.sleep(5)
            self.__init__()
            return

        if not self.last_position:
            if self.flasher():
                ctx.rgb(0, 1, 0)
            else:
                ctx.rgb(0, 0.75, 0)
            ctx.move_to(-100, 0).text("GPS Syncing...")
            return

        self.display_qr(ctx)
        lat, lon = self.last_position

        ctx.rgb(1, 0, 0)
        ctx.move_to(-95, -60).text("-")
    
        if self.flasher():
            ctx.rgb(0, 1, 0)
        else:
            ctx.rgb(0, 0.75, 0)
        ctx.move_to(-55, 100).text("Synced")            
        return

        #ctx.move_to(-110, -40).text(
        #    "Lat: %.5f" % lat
        #)

        #ctx.move_to(-110, -10).text(
        #    "Lon: %.5f" % lon
        #)

        #ctx.move_to(-110, 20).text(
        #    "Spd: %.1f kt" % self.last_speed
        #)

        #ctx.move_to(-110, 50).text(
        #    "Brg: %.0f" % self.last_bearing
        #)


__app_export__ = GPSUMap