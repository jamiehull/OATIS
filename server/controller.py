import asyncio
import time
from pymata_express import pymata_express
import logging
import traceback


class Controller:
    """Class to handle Arduino Comms and setup, use one per board."""
    #Listens to GPI's from a controller and triggers GPO's
    def __init__ (self, input_handler, controller_id:int, controller_port:str, pin_config_list:list):

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #Function to handle input callbacks
        self.input_handler = input_handler

        #Sore a reference to the config
        self.controller_id = controller_id
        self.controller_port = controller_port
        self.pin_config_list = pin_config_list

        #Bool variable used to verify setup of arduino
        self.controller_status = False

        #Pin Mode Indexes
        self.CONTROLLER_ID_INDEX = 0
        self.PIN_ID_INDEX = 1
        self.PIN_MODE_INDEX = 2

        # Callback data list indices
        self.PIN_MODE = 0
        self.PIN_ID = 1
        self.PIN_STATE = 2
        self.STATE_CHANGE_TIME = 3

        #Create a new event loop for the thread
        self.loop = asyncio.new_event_loop()

        #Set the new loop as the current event loop for the thread
        asyncio.set_event_loop(self.loop)
        
    def setup_controller_connection(self) -> bool:
        """Creates the connection to the Arduino and pushes pin config."""
        #Instantiate pymata_express
        try:
            self.logger.debug("Starting Pymata Express...")
            self.board = pymata_express.PymataExpress(com_port=self.controller_port) 

            #If no exceptions in connection report controller status as true
            self.controller_status = True

            self.logger.info(f"Setting up controller with id: {self.controller_id} on port: {self.controller_port}")
            self.logger.debug(f"Pin Config List:{self.pin_config_list}")

            #Set controller input and output pins
            for pin_config in self.pin_config_list:

                #Calculate the arduino pin number
                pin_number = pin_config[self.PIN_ID_INDEX]

                #Get the mode of the selected pin
                pin_mode = pin_config[self.PIN_MODE_INDEX]

                if pin_mode == "input":
                    self.logger.debug(f"Pin:{pin_number} set to input.")
                    self.set_input_pin(pin_number)

                elif pin_mode == "output":
                    self.logger.debug(f"Pin:{pin_number} set to output.")
                    self.set_output_pin(pin_number)

                elif pin_mode == "disabled":
                    self.logger.debug(f"Pin:{pin_number} disabled.")
                
            

            return True

        except Exception as e:
            self.logger.debug(f"Controller not found, please check connnections.")
            self.logger.debug(f"{e}")

            self.controller_status = False
            return False

    def get_controller_status(self) -> bool:
        return self.controller_status

    def start_loop(self):
        """Starts the asyncio event loop"""
        #Run the event loop until stop() is called
        if self.controller_status == True:
            self.loop.run_forever()

    def stop_loop(self):
        """Stops the asyncio event loop"""
        if self.controller_status == True:
            self.loop.create_task(self.board.shutdown())

    #Used to set pins as outputs
    def set_output_pin(self, pin):
        """Sets an Arduino Pin as an Output."""
        #Submit register_output for excecution
        if self.controller_status == True:
            self.loop.create_task(self.register_output(pin))
        
    #Used to set pins as inputs
    def set_input_pin(self, pin):
        """Sets an Arduino Pin as an Input."""
        if self.controller_status == True:
            try:
                self.logger.debug(f"Setting arduino pin {pin} as an input")
                #Submit register_input_callbacks for execution 
                self.loop.create_task(self.register_input_callback(pin))

            except Exception as e:
                self.logger.debug(f"Error registering callbacks: {e}")
                self.loop.run_until_complete(self.board.shutdown())
                self.controller_status = False

    async def register_output(self, pin):
        """Registers Arduino Pin as an Output."""
        self.logger.debug(f"Setting arduino pin {pin} as an output")
        #Set the pin mode to output - no callback as we are not monitoring this pin
        await self.board.set_pin_mode_digital_output(pin)
       
    async def register_input_callback(self, pin):
        """Registers Arduino Pin as an input, setting the callback."""
        self.logger.debug(f"Registering Pin {pin} callback")
        # set the pin mode and assign a callback
        await self.board.set_pin_mode_digital_input_pullup(pin, callback=self.state_change_callback)

    async def state_change_callback(self, data):
        """Callback triggered on pin state change."""
        #data: [pin, current reported value, pin_mode, timestamp]

        #Extract the pin and state information from the data recieved from the controller
        pin = data[self.PIN_ID]
        state = data[self.PIN_STATE]

        date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[self.STATE_CHANGE_TIME]))
        self.logger.debug(f'Pin: {pin} Value: {state} Time Stamp: {date}')

        #Send the information to a handler function
        self.input_handler(self.controller_id, pin, state)


    def set_output_pin_state(self, pin_address:int, state:bool):
        """Sets an output pin high or low"""
        self.loop.create_task(self.board.digital_write(pin_address, state))
        self.logger.info(f"Pin: {pin_address} set to :{state}")

    

    



    