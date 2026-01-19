import pygame
from pygame.locals import *
import math
from time import strftime
from datetime import timezone
from datetime import datetime
from datetime import timedelta
from datetime import datetime
import pygame.gfxdraw
from display_widgets.pygame_widgets.widget import Widget
from modules.common import hex_to_rgb

class Clock(Widget):
    """Base Clock class containing common functions and variables."""
    def __init__(self, widget_config_dict):
        super().__init__()
        #Config
        self.timezone = widget_config_dict["timezone"]
        self.timezone_label_enable = widget_config_dict["timezone_label_enable"]

        #Calculate timezone offset
        self.timezone_offset = self.calculate_utc_offset(self.timezone)
        utc_offset = timedelta(hours=self.timezone_offset)
        self.timezone_obj = timezone(offset=utc_offset)

        #Colours
        self.alarm_indicator_off_colour = (129, 129, 129) #Grey
        self.alarm_indicator_on_colour = (255, 0, 0) #Red
        self.alarm_indicator_current_colour = (129, 129, 129)

        #Alarm Indicator Flash Frequency
        self.flash_period = 400 #Time between flashes in ms
        self.alarm_indicator_flashing_state = False #Controls whetehr indicator is flashing
        self.change_time = 0 #Time for next flash in ms

    def alarm_indicator_flash(self):
        """Flashes an indicator given it's index, starting at 0, top down."""
        if self.alarm_indicator_flashing_state == True:
            #Get the current time in ms
            current_time = pygame.time.get_ticks()

            #If the current time is greater than the next change time and the indicator is in the flashing list
            #flash the indicator
            if current_time >= self.change_time:
                #Indicator on
                if self.alarm_indicator_current_colour == self.alarm_indicator_off_colour:
                    self.alarm_indicator_current_colour = self.alarm_indicator_on_colour

                #Indicator Off
                else:
                    self.alarm_indicator_current_colour = self.alarm_indicator_off_colour

                self.change_time = current_time + self.flash_period
        
    def alarm_indicator_flash_enable(self):
        """Turns Alarm indicator Flash on"""
        self.alarm_indicator_flashing_state = True

    def alarm_indicator_flash_disable(self):
        """Turns Alarm indicator Flash off"""
        self.alarm_indicator_flashing_state = False
        self.alarm_indicator_current_colour = self.alarm_indicator_off_colour

    def calculate_utc_offset(self, timezone_sting:str):
        offset = 0

        #Remove leading UTC
        timezone_string_rem_utc = timezone_sting.strip("UTC")

        #Split string at : delimiter
        timezone_sting_num_only = timezone_string_rem_utc.split(":")[0]

        #Determine whether positive or negative
        if timezone_sting_num_only[0] == "+":
            self.logger.debug("UTC Offset is positive")
            timezone_sting_num_only_positive = timezone_sting_num_only.strip("+")
            offset = int(timezone_sting_num_only_positive)
        
        elif timezone_sting_num_only[0] == "-":
            self.logger.debug("UTC Offset is negative")
            offset = int(timezone_sting_num_only)

        else:
            self.logger.debug("Incorrect timezone string provided. Returning an offset of 0.")

        return offset
        
class Analogue_Clock(Clock):
    def __init__(self, parent_surface, widget_config_dict:dict):
        super().__init__(widget_config_dict)

        #Store reference to the surface
        self.display_surface :pygame.Surface = parent_surface

        #Config
        self.clock_face_colour = hex_to_rgb(widget_config_dict["clock_face_colour"])
        self.legend_colour = hex_to_rgb(widget_config_dict["legend_colour"])
        self.hours_hand_colour = hex_to_rgb(widget_config_dict["hours_hand_colour"])
        self.minutes_hand_colour = hex_to_rgb(widget_config_dict["minutes_hand_colour"])
        self.seconds_hand_colour = hex_to_rgb(widget_config_dict["seconds_hand_colour"])
        self.smooth_tick = widget_config_dict["smooth_tick"]

        #Display Colours
        self.bg_colour = (0,0,0) #Black
        self.center_cover_colour = self.legend_colour #Red

        #Angles Between Indicators
        self.seconds_angle = 6 #360 degrees / 60 = 6
        self.hours_angle = 30

        #Get the resolution of the surface
        self.display_width = self.display_surface.get_width()
        self.display_height = self.display_surface.get_height()
        self.logger.debug(f"Traditional Clock Display Area:{self.display_width},{self.display_height}")

        #Work out which is the smallest dimension
        if self.display_width <= self.display_height:
            smallest_dimension = self.display_width
        else:
            smallest_dimension = self.display_height
            
        #Scale Variables for seconds and hours indicators
        self.seconds_height = smallest_dimension*0.02
        self.hours_height = smallest_dimension*0.04

        #Distance from center of window to center of indicators
        self.seconds_center_distance = (smallest_dimension / 2.05) - (self.seconds_height/2)
        self.hours_center_distance = (self.seconds_center_distance + self.seconds_height/2) - (self.hours_height/2)
        
        #Display Attributes
        self.hands_width = int(smallest_dimension*0.015)
        self.face_radius = smallest_dimension / 2.0
        
        #Find the centre of the display
        self.horizontal_center = self.display_width / 2
        self.vertical_center = self.display_height / 2

        #Text Size and font
        self.label_text_size = int(smallest_dimension*0.07)
        self.font = pygame.font.SysFont('arial', self.label_text_size)

        #Timezone label config
        self.timezone_label_distance = self.face_radius * 0.55
        self.timezone_label_text_size = int(smallest_dimension*0.04)
        self.timezone_font = pygame.font.SysFont('arial', self.timezone_label_text_size)

        #Alarm indicator config
        self.alarm_indicator_radius = int(self.face_radius*0.02)
        self.alarm_indicator_distance = int(self.face_radius*0.66)

        #Draw the clock
        self.add_function_to_render(self.draw_face)
        self.add_function_to_render(self.draw_timezone_label)
        self.add_function_to_render(self.draw_labels)
        self.add_function_to_render(self.draw_bg)
        self.add_function_to_render(self.draw_alarm_indicator)
        self.add_function_to_render(self.update_analogue_time)
        self.add_function_to_render(self.draw_center_cover)
        self.add_function_to_render(self.alarm_indicator_flash)
 
#----------------------------------Module Specific Code---------------------------------

    #Calculates coords give an angle and distance from the centre of the window
    def find_coords_from_center(self, angle, distance):
        """Angle given in degrees"""
        #Convert Angle to Radians
        rad_angle = math.radians(angle)
        #Calculate the coordinates
        x_coord = distance * math.cos(rad_angle) + self.horizontal_center
        y_coord = distance * math.sin(rad_angle) + self.vertical_center

        return x_coord, y_coord
    
    #Calculates coords give an angle and distance from a specified point
    def find_coords_from_point(self, angle, distance, x, y):
        """Calculates coords give an angle in radians and distance from a specified point"""
        #Calculate the coordinates
        x_coord = distance * math.cos(angle) + x
        y_coord = distance * math.sin(angle) + y

        return x_coord, y_coord
    
    def find_hypotenuse_pythag(self, a, b):
        c = math.sqrt(a*a + b*b)
        #self.logger.debug(f"Hypotenuse: {c}")
        return c

    def find_rectangle_points(self, angle_of_orientation, rectangle_height, rectangle_width, distance_from_center):
        """Find the coordinates of the vertices of a rectangle, given it's sloping angle, width and height, returns a list of tuples containing coordinates of the verticies"""
        #Convert angle to radians
        angle_of_orientation_rads = math.radians(angle_of_orientation)

        #Find the coordinates to place the circle
        center_x, center_y = self.find_coords_from_center(angle_of_orientation, distance_from_center)

        #Find each point of the rectangle from the center of the rectangle
        distance = self.find_hypotenuse_pythag(rectangle_height/2, rectangle_width/2)
        angle_to_point_1 = angle_of_orientation_rads + math.atan((rectangle_width/2)/(rectangle_height/2))
        #self.logger.debug(f"Angle 1: {angle_to_point_1}")
        x1, y1 = self.find_coords_from_point(angle_to_point_1, distance, center_x, center_y)

        angle_to_point_2 = angle_of_orientation_rads - math.atan((rectangle_width/2)/(rectangle_height/2))
        #self.logger.debug(f"Angle 2: {angle_to_point_2}")
        x2, y2 = self.find_coords_from_point(angle_to_point_2, distance, center_x, center_y)

        angle_to_point_3 = angle_of_orientation_rads + math.pi + math.atan((rectangle_width/2)/(rectangle_height/2))
        #self.logger.debug(f"Angle 3: {angle_to_point_3}")
        x3, y3 = self.find_coords_from_point(angle_to_point_3, distance, center_x, center_y)

        angle_to_point_4 = angle_of_orientation_rads + math.pi - math.atan((rectangle_width/2)/(rectangle_height/2))
        #self.logger.debug(f"Angle 4 : {angle_to_point_4}")
        x4, y4 = self.find_coords_from_point(angle_to_point_4, distance, center_x, center_y)

        points = [(x1,y1),(x2,y2),(x3,y3),(x4,y4)]
        #self.logger.debug(f"Points: {points}")

        return points

    def draw_bg(self):
        """Draw the indicators."""
        width = self.hands_width
        hour_markers = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]

        for i in range(0,60):
            #Distance from center of window to center of indicator
            center_distance = None

            #Work out whther the indicator should be a second or hour marker and set the center distance and height
            if i in hour_markers:
                center_distance = self.hours_center_distance
                height = self.hours_height
            else:
                center_distance = self.seconds_center_distance
                height = self.seconds_height

            #Calculate the current angle the indicator will be drawn at from display center
            current_angle = i*self.seconds_angle
            
            #Find the coordinates of the rectangle's verticies
            points = self.find_rectangle_points(current_angle, height, width, center_distance)

            #Draw the line indicators
            #pygame.gfxdraw.line(self.display_surface, x1, y1, x2, y2, self.seconds_colour)
            pygame.gfxdraw.aapolygon(self.display_surface, points, self.legend_colour)
            pygame.gfxdraw.filled_polygon(self.display_surface, points, self.legend_colour)

    def draw_timezone_label(self):
        if self.timezone_label_enable == "Yes":
            # create a text surface object and a rectangular object for the text surface object
            label = self.timezone_font.render(self.timezone, True, self.legend_colour, self.clock_face_colour)
            label_rect = label.get_rect()

            #Get the text height
            text_height = label_rect.bottom - label_rect.top
            text_width = label_rect.right - label_rect.left
            #self.logger.debug(F"Label Width:{text_width}, Label height:{text_height}")

            #Find the largest dimension
            if text_height > text_width:
                largest_dimension = text_height
            else:
                largest_dimension = text_width

            distance_from_center = self.timezone_label_distance

            #Find the coordinates to place the text
            x,y = self.find_coords_from_center(90, distance_from_center)
    
            #Set the position of the rectangular object.
            label_rect.center = (x, y)

            #Copy the text surface object to the display surface object at the center coordinate.
            self.display_surface.blit(label, label_rect)

    def draw_labels(self):
        """Draw the clock text labels"""
        for i in range(0,13):
            label_text = str(i)

            #Calculate the current angle the indicator will be drawn at from display center
            current_angle = -90 + (i*self.hours_angle)

            # create a text surface object and a rectangular object for the text surface object
            label = self.font.render(label_text, True, self.legend_colour, self.clock_face_colour)
            label_rect = label.get_rect()
            
            #Get the text height
            text_height = label_rect.bottom - label_rect.top
            text_width = label_rect.right - label_rect.left
            #self.logger.debug(F"Label Width:{text_width}, Label height:{text_height}")

            #Find the largest dimension
            if text_height > text_width:
                largest_dimension = text_height
            else:
                largest_dimension = text_width

            distance_from_center = (self.hours_center_distance - (self.hours_height/2)) - largest_dimension/1.5

            #Find the coordinates to place the text
            x,y = self.find_coords_from_center(current_angle, distance_from_center)
    
            #Set the position of the rectangular object.
            label_rect.center = (x, y)

            #Copy the text surface object to the display surface object at the center coordinate.
            self.display_surface.blit(label, label_rect)

    def draw_alarm_indicator(self):
        x, y =self.find_coords_from_center(90, self.alarm_indicator_distance)

        pygame.gfxdraw.aacircle(self.display_surface, int(x), int(y), self.alarm_indicator_radius, self.alarm_indicator_current_colour)
        pygame.gfxdraw.filled_circle(self.display_surface, int(x), int(y), self.alarm_indicator_radius, self.alarm_indicator_current_colour)

    def draw_center_cover(self):
        """Draw the centre hands cover"""
        #Draw the circle
        pygame.gfxdraw.aacircle(self.display_surface, int(self.horizontal_center), int(self.vertical_center), self.hands_width, self.legend_colour)
        pygame.gfxdraw.filled_circle(self.display_surface, int(self.horizontal_center), int(self.vertical_center), self.hands_width, self.legend_colour)

    def draw_face(self):
        """Draws the clock face circle background"""
        #Fill the screen with a color to wipe away anything from last frame
        self.display_surface.fill(self.bg_colour)

        #Calculate the radius of the circle with padding
        radius = int(self.face_radius)

        #Draw the circle
        pygame.gfxdraw.aacircle(self.display_surface, int(self.horizontal_center), int(self.vertical_center), radius, self.clock_face_colour)
        pygame.gfxdraw.filled_circle(self.display_surface, int(self.horizontal_center), int(self.vertical_center), radius, self.clock_face_colour)

    #Draw the Hour indicators
    def draw_hours_hand(self, time_hours, time_minutes):

        #Calculate the current angle the indicator will be drawn at from display center
        current_angle = -90 + ((time_hours+(time_minutes/60))*self.hours_angle)
        
        #Find the height of the hours hand
        height = self.seconds_center_distance * 0.5
        width = self.hands_width

        #Find the coordinates of the rectangle's verticies
        points = self.find_rectangle_points(current_angle, height, width, height/2)

        #Draw the hand
        pygame.gfxdraw.aapolygon(self.display_surface, points, self.hours_hand_colour)
        pygame.gfxdraw.filled_polygon(self.display_surface, points, self.hours_hand_colour)

    #Draw the Minutes indicators
    def draw_minutes_hand(self, time_minutes, time_seconds):

        #Calculate the current angle the circle will be drawn at from display center
        current_angle = -90 + ((time_minutes+(time_seconds/60))*self.seconds_angle)
        
        #Find the height of the seconds hand
        height = self.seconds_center_distance * 0.75
        width = self.hands_width

        #Find the coordinates of the rectangle's verticies
        points = self.find_rectangle_points(current_angle, height, width, height/2)

        #Draw the hand
        pygame.gfxdraw.aapolygon(self.display_surface, points, self.minutes_hand_colour)
        pygame.gfxdraw.filled_polygon(self.display_surface, points, self.minutes_hand_colour)

    #Draw the Seconds indicators
    def draw_seconds_hand(self, seconds, milliseconds):
        #Additional angle added to enable smoothtick
        if self.smooth_tick == "Yes":
            smooth_tick_angle = milliseconds*self.seconds_angle
        else:
            smooth_tick_angle = 0

        #Calculate the current angle the circle will be drawn at from display center
        current_angle = -90 + (seconds*self.seconds_angle) + (smooth_tick_angle)
        
        #Find the height of the seconds hand
        height = self.seconds_center_distance
        width =  self.hands_width

        #Find the coordinates of the rectangle's verticies
        points = self.find_rectangle_points(current_angle, height, width, height/2)

        #Draw the hand
        pygame.gfxdraw.aapolygon(self.display_surface, points, self.seconds_hand_colour)
        pygame.gfxdraw.filled_polygon(self.display_surface, points, self.seconds_hand_colour)

    def update_analogue_time(self):
        """Get the current time and update the clock graphics"""
        #Get the current time, adjusting for the selected timezone
        offset_time = datetime.now(self.timezone_obj)
        #Get the current time in hours
        time_hours = offset_time.hour
        #Get the current time in minutes
        time_minutes = offset_time.minute
        #Get the current time in seconds
        time_seconds = offset_time.second
        #Get the current time in milliseconds
        time_microseconds = offset_time.microsecond / 1000000

        self.draw_seconds_hand(time_seconds, time_microseconds)
        self.draw_minutes_hand(time_minutes, time_seconds)
        self.draw_hours_hand(time_hours, time_minutes)

class Studio_Clock(Clock):
    def __init__(self, parent_surface, widget_config_dict:dict):
        super().__init__(widget_config_dict)

        #Store reference to the surface
        self.display_surface = parent_surface

        #Config
        self.legend_colour = hex_to_rgb(widget_config_dict["legend_colour"])

        #Display Colours
        self.bg_colour = (0,0,0) #Black
        self.off_colour = (129, 129, 129) #Grey

        #Angles Between Indicators
        self.seconds_angle = 6 #360 degrees / 60 = 6
        self.hours_angle = 30

        #Variables used when drawing display
        self.horizontal_center = None
        self.vertical_center = None

        self.seconds_distance = None
        self.hours_distance = None
        self.indicator_distance = None

        #Get the resolution of the surface
        self.display_width = self.display_surface.get_width()
        self.display_height = self.display_surface.get_height()
        self.logger.debug(f"Studio Clock Display Area:{self.display_width},{self.display_height}")

        #Work out which is the smallest dimension
        if self.display_width <= self.display_height:
            smallest_dimension = self.display_width
        else:
            smallest_dimension = self.display_height
            
        #Scale Variables
        self.seconds_radius = int(smallest_dimension*0.02)
        self.hours_radius = int(smallest_dimension*0.025)
        self.digital_clock_text_size = int(smallest_dimension/6)
        self.face_radius = smallest_dimension / 2.0

        #Radius of circle
        self.seconds_distance = (smallest_dimension / 2.05) - (self.seconds_radius/2)
        self.hours_distance = (smallest_dimension / 2.3) - (self.hours_radius/2)
        self.indicator_distance = (smallest_dimension / 2.5) - (self.hours_radius/2)

        #Timezone label config
        self.timezone_label_distance = (self.seconds_distance + self.seconds_radius) * 0.55
        self.timezone_label_text_size = int(smallest_dimension*0.04)
        self.timezone_font = pygame.font.SysFont('arial', self.timezone_label_text_size)

        #Alarm indicator config
        self.alarm_indicator_radius = int(self.face_radius*0.02)
        self.alarm_indicator_distance = int(self.face_radius*0.66)

        #Find the centre of the display
        self.horizontal_center = self.display_width / 2
        self.vertical_center = self.display_height / 2

        self.font = pygame.font.SysFont('arial', self.digital_clock_text_size)

        #Draw the clock
        self.add_function_to_render(self.draw_bg)
        self.add_function_to_render(self.draw_timezone_label)
        self.add_function_to_render(self.draw_hours)
        self.add_function_to_render(self.draw_alarm_indicator)
        self.add_function_to_render(self.update_analogue_time)
        self.add_function_to_render(self.update_digital_time)
        self.add_function_to_render(self.alarm_indicator_flash)
 
#----------------------------------Module Specific Code---------------------------------

    #Calculates coords give an angle and distance from the centre of the window
    def find_coords_from_center(self, angle, distance):
        #Convert Angle to Radians
        rad_angle = math.radians(angle)
        #Calculate the coordinates
        x_coord = distance * math.cos(rad_angle) + self.horizontal_center
        y_coord = distance * math.sin(rad_angle) + self.vertical_center

        return x_coord, y_coord

    def draw_bg(self):
        #Fill the screen with a color to wipe away anything from last frame
        self.display_surface.fill(self.bg_colour)

    #Draw the Hour indicators
    def draw_hours(self):
        for i in range(0,13):
            #Calculate the current angle the circle will be drawn at from display center
            current_angle = i*self.hours_angle

            #Find the coordinates to place the circle
            x, y = self.find_coords_from_center(current_angle, self.hours_distance)

            #Draw the circle
            pygame.gfxdraw.aacircle(self.display_surface, int(x), int(y), self.hours_radius, self.legend_colour)
            pygame.gfxdraw.filled_circle(self.display_surface, int(x), int(y), self.hours_radius, self.legend_colour)

    def draw_timezone_label(self):
        if self.timezone_label_enable == "Yes":
            # create a text surface object and a rectangular object for the text surface object
            label = self.timezone_font.render(self.timezone, True, self.legend_colour, self.bg_colour)
            label_rect = label.get_rect()

            #Get the text height
            text_height = label_rect.bottom - label_rect.top
            text_width = label_rect.right - label_rect.left
            #self.logger.debug(F"Label Width:{text_width}, Label height:{text_height}")

            #Find the largest dimension
            if text_height > text_width:
                largest_dimension = text_height
            else:
                largest_dimension = text_width

            distance_from_center = self.timezone_label_distance

            #Find the coordinates to place the text
            x,y = self.find_coords_from_center(90, distance_from_center)
    
            #Set the position of the rectangular object.
            label_rect.center = (x, y)

            #Copy the text surface object to the display surface object at the center coordinate.
            self.display_surface.blit(label, label_rect)

    #Draw the seconds indicators
    def draw_seconds(self, i):
        for seconds in range(0,60):
            if seconds <= i:
                #Active Indicator Colour
                colour = self.legend_colour
            else:
                #Inactive indicator Colour
                colour = self.off_colour

            #Calculate the current angle the circle will be drawn at from display center
            current_angle = ((seconds*self.seconds_angle)-90)

            #Find the coordinates to place the circle
            x, y = self.find_coords_from_center(current_angle, self.seconds_distance)

            #Draw the circle
            pygame.gfxdraw.aacircle(self.display_surface, int(x), int(y), self.seconds_radius, colour)
            pygame.gfxdraw.filled_circle(self.display_surface, int(x), int(y), self.seconds_radius, colour)

    def draw_alarm_indicator(self):
        x, y =self.find_coords_from_center(90, self.alarm_indicator_distance)

        pygame.gfxdraw.aacircle(self.display_surface, int(x), int(y), self.alarm_indicator_radius, self.alarm_indicator_current_colour)
        pygame.gfxdraw.filled_circle(self.display_surface, int(x), int(y), self.alarm_indicator_radius, self.alarm_indicator_current_colour)

    def update_analogue_time(self):
        #Get the current time in seconds
        time_seconds = strftime('%S')
        #Draw analogue clock seconds
        self.draw_seconds(int(time_seconds))
        

    def update_digital_time(self):
        #Get the current time, adjusting for the selected timezone
        offset_time = datetime.now(self.timezone_obj)
        offset_time_seconds  = offset_time.strftime('%S')
        offset_time_string_hr_min = offset_time.strftime('%H:%M')

        # create a text surface object and a rectangular object for the text surface object
        text_hr_min = self.font.render(offset_time_string_hr_min, True, self.legend_colour, self.bg_colour)
        text_rect_hr_min = text_hr_min.get_rect()

        text_sec = self.font.render(offset_time_seconds, True, self.legend_colour, self.bg_colour)
        text_rect_sec = text_sec.get_rect()
        
        #Get the text height
        text_height = text_rect_hr_min.top - text_rect_hr_min.bottom

        #Set the center of the rectangular object.
        text_rect_hr_min.center = (self.horizontal_center, self.vertical_center+text_height/2)
        text_rect_sec.center = (self.horizontal_center, self.vertical_center-text_height/2)

        #Copy the text surface object to the display surface object at the center coordinate.
        self.display_surface.blit(text_hr_min, text_rect_hr_min)
        self.display_surface.blit(text_sec, text_rect_sec)

class Digital_Clock(Clock):
    def __init__(self, parent_surface, widget_config_dict:dict):
        super().__init__(widget_config_dict)

        #Store reference to the surface
        self.display_surface = parent_surface

        #Config
        self.time_format = widget_config_dict["time_format"]
        self.text_colour = hex_to_rgb(widget_config_dict["text_colour"])

        #Display Colours
        self.bg_colour = (0,0,0) #Black

        #Get the resolution of the surface
        self.display_width = self.display_surface.get_width()
        self.display_height = self.display_surface.get_height()
        self.logger.debug(f"Digital Clock Display Area:{self.display_width},{self.display_height}")

        #Find the centre of the display
        self.horizontal_center = self.display_width / 2
        self.vertical_center = self.display_height / 2

        #Work out which is the smallest dimension
        if self.display_width <= self.display_height:
            self.smallest_dimension = self.display_width
        else:
            self.smallest_dimension = self.display_height

        #Alarm indicator config
        self.alarm_indicator_radius = int(self.smallest_dimension*0.025)
        self.alarm_indicator_x_pos = 0
        self.alarm_indicator_y_pos = 0
        
        #Digital Clock Font - Overriden if calculate_digital_clock_text_scaling used
        self.digital_clock_text_size = int(self.display_height * 0.8)
        self.digital_clock_font = pygame.font.SysFont('arial', self.digital_clock_text_size)
        self.digital_clock_text_height = 0

        if self.timezone_label_enable == "Yes":
            self.digital_clock_text_max_height = self.display_height * 0.7
        else:
            self.digital_clock_text_max_height = self.display_height

        #Calculate Digital Clock Font Size to fit display surface
        self.calculate_digital_clock_text_scaling()
        
        #Timezone label Font - Overriden if calculate_timezone_label_scaling used
        self.timezone_label_text_size = int(self.digital_clock_text_size * 0.7)
        self.timezone_font = pygame.font.SysFont('arial', self.timezone_label_text_size)
        self.timezone_label_height = 0
        self.timezone_text_max_height = self.digital_clock_text_height * 0.3

        #Calculate Timezone Label Font Size to fit display surface
        self.calculate_timezone_label_scaling()

        #Calculate alarm indicator position
        self.calculate_alarm_indicator_position()
        
        #Draw the clock
        self.add_function_to_render(self.draw_bg)
        self.add_function_to_render(self.update_digital_time)
        self.add_function_to_render(self.draw_alarm_indicator)
        self.add_function_to_render(self.alarm_indicator_flash)
 
#----------------------------------Module Specific Code---------------------------------

    def draw_bg(self):
        #Fill the screen with a color to wipe away anything from last frame
        self.display_surface.fill(self.bg_colour)

    def draw_alarm_indicator(self):
        pygame.gfxdraw.aacircle(self.display_surface, int(self.alarm_indicator_x_pos), int(self.alarm_indicator_y_pos), self.alarm_indicator_radius, self.alarm_indicator_current_colour)
        pygame.gfxdraw.filled_circle(self.display_surface, int(self.alarm_indicator_x_pos), int(self.alarm_indicator_y_pos), self.alarm_indicator_radius, self.alarm_indicator_current_colour)

    def calculate_digital_clock_text_scaling(self):
        """Calculates the text size to fit the clock onto the display surface."""
        clock_fits_display = False
        digital_clock_text_size = int(self.display_height * 0.8)
        
        #Get the current time, adjusting for the selected timezone
        offset_time = datetime.now(self.timezone_obj)

        if self.time_format == "24 Hour":
            offset_time_string_hr_min_sec = offset_time.strftime('%H:%M:%S')

        else:
            offset_time_string_hr_min_sec = offset_time.strftime('%I:%M:%S %p')

        while clock_fits_display == False:
            #Digital Clock Font
            font = pygame.font.SysFont('arial', digital_clock_text_size)

            #Create a text surface object and a rectangular object for the text surface object
            text_hr_min_sec = font.render(offset_time_string_hr_min_sec, True, self.text_colour, self.bg_colour)
            text_rect_hr_min_sec = text_hr_min_sec.get_rect()
            
            #Get the text width / height
            text_width = text_rect_hr_min_sec.right - text_rect_hr_min_sec.left
            text_height = text_rect_hr_min_sec.bottom - text_rect_hr_min_sec.top
            self.logger.debug(f"Clock Text Width is: {text_width}, Clock Text Height is:{text_height}")

            #If it fits on the display surface
            if (text_width <= (self.display_width * 0.9)) and (text_height <= self.digital_clock_text_max_height):
                self.digital_clock_text_size = digital_clock_text_size
                self.digital_clock_font = pygame.font.SysFont('arial', self.digital_clock_text_size)
                self.digital_clock_text_height = text_rect_hr_min_sec.bottom - text_rect_hr_min_sec.top
                clock_fits_display = True

            #If it does not, make it a bit smaller!
            else:
                digital_clock_text_size =  int(digital_clock_text_size * 0.9)

    def calculate_timezone_label_scaling(self):
        """Calculates the text size to fit the timezone label onto the display surface."""
        timezone_fits_display = False
        timezone_text_size = int(self.timezone_text_max_height)
        
        while timezone_fits_display == False:
            #Timezone Font
            font = pygame.font.SysFont('arial', timezone_text_size)

            #Create a text surface object and a rectangular object for the text surface object
            text_timezone = font.render(self.timezone, True, self.text_colour, self.bg_colour)
            text_rect_timezone = text_timezone.get_rect()
            
            #Get the text width / height
            text_width = text_rect_timezone.right - text_rect_timezone.left
            text_height = text_rect_timezone.bottom - text_rect_timezone.top
            self.logger.debug(f"Timezone Label Text Width is: {text_width}, Timezone Label Text Height is:{text_height}")

            #If it fits on the display surface
            if (text_width <= (self.display_width * 0.9)) and (text_height <= self.timezone_text_max_height):
                self.timezone_label_text_size = timezone_text_size
                self.timezone_font = pygame.font.SysFont('arial', self.timezone_label_text_size)
                self.timezone_label_height = text_rect_timezone.bottom - text_rect_timezone.top
                timezone_fits_display = True

            #If it does not, make it a bit smaller!
            else:
                timezone_text_size =  int(timezone_text_size * 0.9)

    def calculate_alarm_indicator_position(self):
        """Works out where to put the alarm indicator."""

        if self.timezone_label_enable == "Yes":
            self.alarm_indicator_x_pos = self.display_width/2
            self.alarm_indicator_y_pos = self.digital_clock_text_height * 0.95
        else:
            self.alarm_indicator_x_pos = self.display_width/2
            self.alarm_indicator_y_pos = (self.vertical_center + (self.digital_clock_text_height / 2)) * 0.95

    def update_digital_time(self):
        """Renders the digital clock with current time."""
        
        #Get the current time, adjusting for the selected timezone
        offset_time = datetime.now(self.timezone_obj)
    
        #24 Hour Time
        if self.time_format == "24 Hour":
            offset_time_string_hr_min_sec = offset_time.strftime('%H:%M:%S')

        #12 Hour Time
        else:
            offset_time_string_hr_min_sec = offset_time.strftime('%I:%M:%S %p')

        #Create a text surface object and a rectangular object for the text surface object
        text_hr_min_sec = self.digital_clock_font.render(offset_time_string_hr_min_sec, True, self.text_colour, self.bg_colour)
        text_rect_hr_min_sec = text_hr_min_sec.get_rect()

        if self.timezone_label_enable == "Yes":
            text_rect_hr_min_sec.center = (self.horizontal_center, self.digital_clock_text_height/2)
            
            #Create a text surface object and a rectangular object for the text surface object
            timezone_label = self.timezone_font.render(self.timezone, True, self.text_colour, self.bg_colour)
            timezone_label_rect = timezone_label.get_rect()

            #Set the position of the rectangular object.
            remaining_display_height = (self.display_height - self.digital_clock_text_height)
            timezone_label_rect.center = (self.horizontal_center, (self.digital_clock_text_height + (0.3 * remaining_display_height)))

            #Copy the text surface object to the display surface object at the center coordinate.
            self.display_surface.blit(timezone_label, timezone_label_rect)

        else:
            #Set the center of the rectangular object.
            text_rect_hr_min_sec.center = (self.horizontal_center, self.vertical_center)
        
        #Copy the text surface object to the display surface object at the center coordinate.
        self.display_surface.blit(text_hr_min_sec, text_rect_hr_min_sec)






