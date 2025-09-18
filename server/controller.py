import asyncio
import time
from pymata_express import pymata_express
import logging


class Controller:
    #Listens to GPI's from a controller and triggers GPO's
    def __init__ (self, config:list, input_handler):

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #Function to handle input callbacks
        self.input_handler = input_handler

        #Controller Table Index constants to pick out correct data from the config
        self.gpio_pin_start_index = 6
        self.gpio_pin_end_index = 23
        self.serial_port_index = 4
        self.controller_id_index = 0

        #ID of this controller and serial port used for comms
        self.controller_id = config[self.controller_id_index]
        self.controller_port = config[self.serial_port_index]

        #Bool variable used to verify setup of arduino
        self.controller_status = False

        #Store a reference to the controller config
        self.config = config

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
        #Instantiate pymata_express
        try:
            self.logger.debug("Starting Pymata Express...")
            self.board = pymata_express.PymataExpress(com_port=self.controller_port)
            #If no exceptions in connection report controller status as true
            self.controller_status = True

            self.logger.debug(f"Setting up controller with id: {self.controller_id} on port: {self.controller_port}")

            #Set controller input and output pins
            for pin_index in range (self.gpio_pin_start_index, self.gpio_pin_end_index+1):
                #Calculate the arduino pin number
                pin_number = pin_index-4    #Pin starts at 2 for uno
                #Get the mode of the selected pin
                pin_mode = self.config[pin_index]

                if pin_mode == "in":
                    self.set_input_pin(pin_number)

                if pin_mode == "out":
                    self.set_output_pin(pin_number)

                if pin_mode == "disabled":
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
        #Run the event loop until stop() is called
        if self.controller_status == True:
            self.loop.run_forever()

    def stop_loop(self):
        if self.controller_status == True:
            self.loop.stop()

    #Used to set pins as outputs
    def set_output_pin(self, pin):
        #Submit register_output for excecution
        if self.controller_status == True:
            self.loop.create_task(self.register_output(pin))
        
    #Used to set pins as inputs
    def set_input_pin(self, pin):
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
        self.logger.debug(f"Setting arduino pin {pin} as an output")
        #Set the pin mode to output - no callback as we are not monitoring this pin
        await self.board.set_pin_mode_digital_output(pin)
       
    async def register_input_callback(self, pin):
        self.logger.debug("Registering Pin Callbacks")
        # set the pin mode and assign a callback
        await self.board.set_pin_mode_digital_input_pullup(pin, callback=self.pin_state_change_callback)


    async def pin_state_change_callback(self, data):
        #data: [pin, current reported value, pin_mode, timestamp]

        #extract the pin and state information from the data recieved from the controller
        pin = data[self.PIN_ID]
        state = data[self.PIN_STATE]

        date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[self.STATE_CHANGE_TIME]))
        self.logger.debug(f'Pin: {pin} Value: {state} Time Stamp: {date}')

        #Send the information to a handler function
        self.input_handler(self.controller_id, pin, state)

    

    



    