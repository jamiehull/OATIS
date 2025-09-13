import pygame
from pygame.locals import *
import math
from time import strftime
from datetime import datetime
import pygame.gfxdraw

class Traditional_Clock:
    def __init__(self, parent_surface):

        #Store reference to the surface
        self.display_surface :pygame.Surface = parent_surface

        #Display Colours
        self.bg_colour = (0,0,0) #Black
        self.face_colour = (43, 43, 43) #White
        self.label_colour = (255, 0, 0) #Red
        self.hour_colour = (255, 0, 0) #Red
        self.minutes_colour = (0, 255, 60) #Green
        self.seconds_colour = (255, 234, 0) #Yellow
        self.center_cover_colour = (255, 0, 0) #Red
        self.alarm_indicator_off_colour = (129, 129, 129) #Grey
        self.alarm_indicator_on_colour = (255, 0, 0) #Red
        self.alarm_indicator_current_colour = (129, 129, 129)

        #Angles Between Indicators
        self.seconds_angle = 6 #360 degrees / 60 = 6
        self.hours_angle = 30

        #Get the resolution of the surface
        self.display_width = self.display_surface.get_width()
        self.display_height = self.display_surface.get_height()
        print(f"Traditional Clock Display Area:{self.display_width},{self.display_height}")

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
        self.alarm_indicator_radius = int(self.hands_width/2)
        self.face_radius = smallest_dimension / 2.0

        #Find the centre of the display
        self.horizontal_center = self.display_width / 2
        self.vertical_center = self.display_height / 2

        #Text Size and font
        self.label_text_size = int(smallest_dimension*0.07)
        self.font = pygame.font.SysFont('arial', self.label_text_size)

        #Alarm Indicator Flash Frequency
        self.flash_period = 400 #Time between flashes in ms
        self.alarm_indicator_flashing_state = False #Controls whetehr indicator is flashing
        self.change_time = 0 #Time for next flash in ms

    #Update the Display
    def render(self):
        #Fill the screen with a color to wipe away anything from last frame
        self.display_surface.fill(self.bg_colour)

        #Draw the clock
        self.draw_face()
        self.draw_labels()
        self.draw_bg()
        self.draw_alarm_indicator()
        self.update_analogue_time()
        self.draw_center_cover()
        self.__flash()
        
 
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
        #print(f"Hypotenuse: {c}")
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
        #print(f"Angle 1: {angle_to_point_1}")
        x1, y1 = self.find_coords_from_point(angle_to_point_1, distance, center_x, center_y)

        angle_to_point_2 = angle_of_orientation_rads - math.atan((rectangle_width/2)/(rectangle_height/2))
        #print(f"Angle 2: {angle_to_point_2}")
        x2, y2 = self.find_coords_from_point(angle_to_point_2, distance, center_x, center_y)

        angle_to_point_3 = angle_of_orientation_rads + math.pi + math.atan((rectangle_width/2)/(rectangle_height/2))
        #print(f"Angle 3: {angle_to_point_3}")
        x3, y3 = self.find_coords_from_point(angle_to_point_3, distance, center_x, center_y)

        angle_to_point_4 = angle_of_orientation_rads + math.pi - math.atan((rectangle_width/2)/(rectangle_height/2))
        #print(f"Angle 4 : {angle_to_point_4}")
        x4, y4 = self.find_coords_from_point(angle_to_point_4, distance, center_x, center_y)

        points = [(x1,y1),(x2,y2),(x3,y3),(x4,y4)]
        #print(f"Points: {points}")

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
            pygame.gfxdraw.aapolygon(self.display_surface, points, self.hour_colour)
            pygame.gfxdraw.filled_polygon(self.display_surface, points, self.hour_colour)

    def draw_labels(self):
        """Draw the clock text labels"""
        for i in range(0,13):
            label_text = str(i)

            #Calculate the current angle the indicator will be drawn at from display center
            current_angle = -90 + (i*self.hours_angle)

            # create a text surface object and a rectangular object for the text surface object
            label = self.font.render(label_text, True, self.label_colour, self.face_colour)
            label_rect = label.get_rect()
            
            #Get the text height
            text_height = label_rect.bottom - label_rect.top
            text_width = label_rect.right - label_rect.left
            #print(F"Label Width:{text_width}, Label height:{text_height}")

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
        x, y =self.find_coords_from_center(90, self.hours_center_distance-(self.hours_height*4))

        pygame.gfxdraw.aacircle(self.display_surface, int(x), int(y), self.alarm_indicator_radius, self.alarm_indicator_current_colour)
        pygame.gfxdraw.filled_circle(self.display_surface, int(x), int(y), self.alarm_indicator_radius, self.alarm_indicator_current_colour)

    def draw_center_cover(self):
        """Draw the centre hands cover"""
        #Draw the circle
        pygame.gfxdraw.aacircle(self.display_surface, int(self.horizontal_center), int(self.vertical_center), self.hands_width, self.center_cover_colour)
        pygame.gfxdraw.filled_circle(self.display_surface, int(self.horizontal_center), int(self.vertical_center), self.hands_width, self.center_cover_colour)

    def draw_face(self):
        """Draws the clock face circle background"""
        #Calculate the radius of the circle with padding
        radius = int(self.face_radius)

        #Draw the circle
        pygame.gfxdraw.aacircle(self.display_surface, int(self.horizontal_center), int(self.vertical_center), radius, self.face_colour)
        pygame.gfxdraw.filled_circle(self.display_surface, int(self.horizontal_center), int(self.vertical_center), radius, self.face_colour)

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
        pygame.gfxdraw.aapolygon(self.display_surface, points, self.hour_colour)
        pygame.gfxdraw.filled_polygon(self.display_surface, points, self.hour_colour)

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
        pygame.gfxdraw.aapolygon(self.display_surface, points, self.minutes_colour)
        pygame.gfxdraw.filled_polygon(self.display_surface, points, self.minutes_colour)

    #Draw the Seconds indicators
    def draw_seconds_hand(self, seconds):

        #Calculate the current angle the circle will be drawn at from display center
        current_angle = -90 + (seconds*self.seconds_angle)
        
        #Find the height of the seconds hand
        height = self.seconds_center_distance
        width =  self.hands_width

        #Find the coordinates of the rectangle's verticies
        points = self.find_rectangle_points(current_angle, height, width, height/2)

        #Draw the hand
        pygame.gfxdraw.aapolygon(self.display_surface, points, self.seconds_colour)
        pygame.gfxdraw.filled_polygon(self.display_surface, points, self.seconds_colour)

    def update_analogue_time(self):
        """Get the current time and update the clock graphics"""
        current_time = datetime.now()
        #Get the current time in hours
        time_hours = current_time.hour
        #Get the current time in minutes
        time_minutes = current_time.minute
        #Get the current time in seconds
        time_seconds = current_time.second
        #Get the current time in milliseconds
        time_milliseconds = current_time.microsecond / 1000

        self.draw_seconds_hand(time_seconds)
        self.draw_minutes_hand(time_minutes, time_seconds)
        self.draw_hours_hand(time_hours, time_minutes)

    def __flash(self):
        """Flashes the alarm indicator"""
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

    def alarm_indicator_indicator_flash_disable(self):
        """Turns Alarm indicator Flash off"""
        self.alarm_indicator_flashing_state = False
        self.alarm_indicator_current_colour = self.alarm_indicator_off_colour

class Studio_Clock:
    def __init__(self, parent_surface):

        #Store reference to the surface
        self.display_surface = parent_surface

        #Display Colours
        self.bg_colour = (0,0,0) #Black
        self.seconds_colour = (255, 0, 0) #Red
        self.hour_on_colour = (255, 0, 0) #Red
        self.hour_off_colour = (129, 129, 129) #Grey
        self.indicator_ok_colour = "green"
        self.indicator_error_colour = "orange"
        self.alarm_indicator_off_colour = (129, 129, 129) #Grey
        self.alarm_indicator_on_colour = (255, 0, 0) #Red
        self.alarm_indicator_current_colour = (129, 129, 129)

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
        print(f"Studio Clock Display Area:{self.display_width},{self.display_height}")

        #Work out which is the smallest dimension
        if self.display_width <= self.display_height:
            smallest_dimension = self.display_width
        else:
            smallest_dimension = self.display_height
            
        #Scale Variables
        self.seconds_radius = int(smallest_dimension*0.02)
        self.hours_radius = int(smallest_dimension*0.025)
        self.alarm_indicator_radius = int(self.seconds_radius/2)
        self.indicator_text_size = int(smallest_dimension*0.07)
        self.digital_clock_text_size = int(smallest_dimension/6)

        #Radius of circle
        self.seconds_distance = (smallest_dimension / 2.05) - (self.seconds_radius/2)
        self.hours_distance = (smallest_dimension / 2.3) - (self.hours_radius/2)
        self.indicator_distance = (smallest_dimension / 2.5) - (self.hours_radius/2)

        #Find the centre of the display
        self.horizontal_center = self.display_width / 2
        self.vertical_center = self.display_height / 2

        self.font = pygame.font.SysFont('arial', self.digital_clock_text_size)

        #Alarm Indicator Flash Frequency
        self.flash_period = 400 #Time between flashes in ms
        self.alarm_indicator_flashing_state = False #Controls whetehr indicator is flashing
        self.change_time = 0 #Time for next flash in ms
    
    #Update the Display
    def render(self):
        #Fill the screen with a color to wipe away anything from last frame
        self.display_surface.fill(self.bg_colour)

        #Draw the clock
        self.draw_hours()
        self.draw_alarm_indicator()
        self.update_analogue_time()
        self.update_digital_time()
        self.__flash()
 
#----------------------------------Module Specific Code---------------------------------

    #Calculates coords give an angle and distance from the centre of the window
    def find_coords_from_center(self, angle, distance):
        #Convert Angle to Radians
        rad_angle = math.radians(angle)
        #Calculate the coordinates
        x_coord = distance * math.cos(rad_angle) + self.horizontal_center
        y_coord = distance * math.sin(rad_angle) + self.vertical_center

        return x_coord, y_coord

    #Draw the Hour indicators
    def draw_hours(self):
        for i in range(0,13):
            #Calculate the current angle the circle will be drawn at from display center
            current_angle = i*self.hours_angle

            #Find the coordinates to place the circle
            x, y = self.find_coords_from_center(current_angle, self.hours_distance)

            #Draw the circle
            pygame.gfxdraw.aacircle(self.display_surface, int(x), int(y), self.hours_radius, self.seconds_colour)
            pygame.gfxdraw.filled_circle(self.display_surface, int(x), int(y), self.hours_radius, self.seconds_colour)

    #Draw the seconds indicators
    def draw_seconds(self, i):
        for seconds in range(0,60):
            if seconds <= i:
                #Active Indicator Colour
                colour = self.hour_on_colour
            else:
                #Inactive indicator Colour
                colour = self.hour_off_colour

            #Calculate the current angle the circle will be drawn at from display center
            current_angle = ((seconds*self.seconds_angle)-90)

            #Find the coordinates to place the circle
            x, y = self.find_coords_from_center(current_angle, self.seconds_distance)

            #Draw the circle
            pygame.gfxdraw.aacircle(self.display_surface, int(x), int(y), self.seconds_radius, colour)
            pygame.gfxdraw.filled_circle(self.display_surface, int(x), int(y), self.seconds_radius, colour)

    def draw_alarm_indicator(self):
        x, y =self.find_coords_from_center(90, self.seconds_distance-(self.seconds_radius*8))

        pygame.gfxdraw.aacircle(self.display_surface, int(x), int(y), self.alarm_indicator_radius, self.alarm_indicator_current_colour)
        pygame.gfxdraw.filled_circle(self.display_surface, int(x), int(y), self.alarm_indicator_radius, self.alarm_indicator_current_colour)

    def update_analogue_time(self):
        #Get the current time in seconds
        time_seconds = strftime('%S')
        #Draw analogue clock seconds
        self.draw_seconds(int(time_seconds))

    def update_digital_time(self):
        #Get the current time
        time_seconds = strftime('%S')
        time_hr_min = strftime('%H:%M')

        # create a text surface object and a rectangular object for the text surface object
        text_hr_min = self.font.render(time_hr_min, True, "red", "black")
        text_rect_hr_min = text_hr_min.get_rect()

        text_sec = self.font.render(time_seconds, True, "red", "black")
        text_rect_sec = text_sec.get_rect()
        
        #Get the text height
        text_height = text_rect_hr_min.top - text_rect_hr_min.bottom

        #Set the center of the rectangular object.
        text_rect_hr_min.center = (self.horizontal_center, self.vertical_center+text_height/2)
        text_rect_sec.center = (self.horizontal_center, self.vertical_center-text_height/2)

        #Copy the text surface object to the display surface object at the center coordinate.
        self.display_surface.blit(text_hr_min, text_rect_hr_min)
        self.display_surface.blit(text_sec, text_rect_sec)

    def __flash(self):
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





