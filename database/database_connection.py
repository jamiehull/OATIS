import sqlite3
import tkinter as tk
import subprocess
import logging

class DB:
    def __init__(self):

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #Create a connection to the database
        self.connection = sqlite3.connect("database/oatis_db")
        #Check the connection to the database was established
        self.logger.info(self.connection.total_changes)
        #Create a cursor object to manipulate the database
        self.cursor = self.connection.cursor()

        #Database tables:
        self.database_tables = [
            "devices",
            "locations",
            "controllers",
            "controller_types",
            "pin_modes",
            "images",
            "display_templates",
            "display_surfaces",
            "message_groups",
            "active_messages",
            "messages",
            "input_triggers",
            "input_logics",
            "input_logic_mapping",
            "output_logics",
            "output_triggers",
            "output_logic_mapping",
            "top_banner",
            "studio_clock",
            "analogue_clock",
            "digital_clock",
            "static_text",
            "static_image",
            "stacked_image",
            "indicator",
            "display_instances"
        ]

        #Used for verification, the total number of tables in a valid database that has been correctly initialised
        self.total_number_tables = len(self.database_tables)

    def connect(self):
        #Create a connection to the database
        self.logger.info("Connecting to database")
        self.connection = sqlite3.connect("database/oatis_db")
        #Create a cursor object to manipulate the database
        self.cursor = self.connection.cursor()
        self.logger.info("Connection established")

    def close_connection(self):
        #Create a connection to the database
        self.logger.info("Closing connection to database")
        self.connection.close()

    def verify_database_setup(self):
        self.logger.info("Verifying the database is valid")
        table_count = 0
        for table_name in self.database_tables:
            #Count the number of tables with the specified table name present in sqlite_master
            self.cursor.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{table_name}'")

            #Returns 0 if table not exist, 1 if table exists
            table_exist = self.cursor.fetchone()
            if table_exist[0] == 1:
                self.logger.debug(f"Table: {table_name} exists")
            else:
                self.logger.debug(f"Table: {table_name} is missing")

            #Add the result to the count variable, total should equal number of required tables
            table_count += table_exist[0]

        self.logger.info(f"Found {table_count} valid tables in the database, required {self.total_number_tables}")
        
        if table_count == self.total_number_tables:
            self.logger.info("All required tables present")
            return True
        
        else:
            self.logger.info("Database corrupt or not initialised.")
            return False
    
    #Creates all tables and adds in default data into tables.
    def initialise_database(self):
        self.logger.info("Initialising the Database...")
        #Drop All Tables in the Database
        for table in self.database_tables:
            self.logger.debug(f"Dropping table: {table}")
            self.cursor.execute(f"DROP TABLE IF EXISTS {table}")
        self.logger.debug("Dropped all tables if they existed.")

        #Re-create all tables
        self.logger.debug("Creating all required tables.")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS devices 
                            (device_id INTEGER PRIMARY KEY AUTOINCREMENT,
                             device_name TEXT, 
                             device_ip TEXT, 
                            location TEXT, 
                            message_group_id INTEGER, 
                            display_instance_id INTEGER, 
                            FOREIGN KEY(message_group_id) REFERENCES message_groups(message_group_id),
                            FOREIGN KEY(display_instance_id) REFERENCES display_instances(display_instance_id))""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS locations 
                            (location_id INTEGER PRIMARY KEY, 
                             location TEXT)""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS controller_types 
                            (manufacturer TEXT, 
                            model TEXT PRIMARY KEY, 
                            total_gpio_pins INTEGER,
                            start_pin_index INTEGER,
                            end_pin_index INTEGER,
                            start_input_only_pin_index INTEGER,
                            end_input_only_pin_index INTEGER
                            )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS controllers 
                            (controller_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            controller_name TEXT, 
                            controller_location TEXT, 
                            controller_ip TEXT, 
                            controller_port TEXT, 
                            controller_type TEXT,
                            FOREIGN KEY (controller_type) REFERENCES controller_types (model)
                            )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS pin_modes 
                            (controller_id INTEGER, 
                            pin_id INTEGER, 
                            pin_mode TEXT,
                            FOREIGN KEY(controller_id) REFERENCES controllers (controller_id),
                            PRIMARY KEY (controller_id, pin_id)
                            )""")

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS display_templates 
                            (display_template_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            display_template_name TEXT, 
                            total_columns INTEGER, 
                            total_rows INTEGER, 
                            layout_matrix BLOB, 
                            last_changed TEXT
                            )""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS display_surfaces 
                            (display_template_id INTEGER NOT NULL, 
                            display_surface_id INTEGER NOT NULL, 
                            widget_string TEXT, 
                            top_left_coord_column INTEGER, 
                            top_left_coord_row INTEGER, 
                            block_width INTEGER, 
                            block_height INTEGER,
                            FOREIGN KEY(display_template_id) REFERENCES display_templates (display_template_id),
                            PRIMARY KEY (display_template_id, display_surface_id) 
                            )""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS display_instances
                            (display_instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            display_instance_name TEXT,
                            display_template_id INTEGER NOT NULL,
                            last_changed TEXT,
                            FOREIGN KEY(display_template_id) REFERENCES display_templates (display_template_id))""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS message_groups 
                            (message_group_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            message_group_name TEXT)""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS images 
                            (image_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            image_name TEXT, 
                            image_file BLOB)""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS messages 
                            (message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            message_text TEXT NOT NULL,
                            message_timestamp TEXT NOT NULL)""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS active_messages 
                            (message_id INTEGER NOT NULL,
                            message_group_id INTEGER NOT NULL,
                            FOREIGN KEY(message_id) REFERENCES messages (message_id),
                            FOREIGN KEY(message_group_id) REFERENCES message_groups (message_group_id))""")

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS input_triggers 
                            (input_trigger_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            input_trigger_name TEXT NOT NULL,
                            controller_id INTEGER NOT NULL,
                            address TEXT NOT NULL,
                            current_state BOOL NOT NULL,
                            FOREIGN KEY(controller_id) REFERENCES controllers (controller_id))""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS input_logics 
                            (input_logic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            input_logic_name TEXT NOT NULL,
                            high_condition TEXT NOT NULL
                            )""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS input_logic_mapping 
                            (input_logic_id INTEGER NOT NULL,
                            input_trigger_id INTEGER NOT NULL,
                            FOREIGN KEY(input_logic_id) REFERENCES input_logics (input_logic_id),
                            FOREIGN KEY(input_trigger_id) REFERENCES input_triggers (input_trigger_id)
                            )""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS output_logics 
                            (output_logic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            output_logic_name TEXT NOT NULL,
                            input_logic_id INTEGER NOT NULL,
                            current_state BOOL NOT NULL,
                            FOREIGN KEY(input_logic_id) REFERENCES input_logics (input_logic_id)
                            )""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS output_triggers 
                            (output_trigger_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            output_trigger_name TEXT NOT NULL,
                            output_type TEXT NOT NULL,
                            controller_id INTEGER NOT NULL,
                            address TEXT,
                            ip_address TEXT,
                            port INTEGER,
                            protocol TEXT,
                            command_high TEXT,
                            arguments_high TEXT,
                            command_low TEXT,
                            arguments_low TEXT,
                            FOREIGN KEY(controller_id) REFERENCES controllers (controller_id)
                            )""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS output_logic_mapping 
                            (output_logic_id INTEGER NOT NULL,
                            output_trigger_id INTEGER NOT NULL,
                            FOREIGN KEY(output_logic_id) REFERENCES output_logics (output_logic_id),
                            FOREIGN KEY(output_trigger_id) REFERENCES output_triggers (output_trigger_id)
                            )""")

        #----------------------------------------------Display Widget Config----------------------------------------------
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS indicator 
                            (display_instance_id INTEGER NOT NULL,
                            display_surface_id INTEGER NOT NULL,
                            indicator_label TEXT NOT NULL,
                            on_colour TEXT NOT NULL,
                            flash_enable TEXT NOT NULL,
                            input_logic_id INTEGER NOT NULL,
                            FOREIGN KEY(display_instance_id) REFERENCES display_instances (display_instance_id)
                            FOREIGN KEY(input_logic_id) REFERENCES input_logics (input_logic_id)
                            )""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS studio_clock 
                            (display_instance_id INTEGER NOT NULL,
                            display_surface_id INTEGER NOT NULL,
                            timezone TEXT NOT NULL,
                            timezone_label_enable TEXT NOT NULL,
                            legend_colour TEXT NOT NULL,
                            FOREIGN KEY(display_instance_id) REFERENCES display_instances (display_instance_id)
                            )""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS analogue_clock 
                            (display_instance_id INTEGER NOT NULL,
                            display_surface_id INTEGER NOT NULL,
                            timezone TEXT NOT NULL,
                            timezone_label_enable TEXT NOT NULL,
                            clock_face_colour TEXT NOT NULL,
                            legend_colour TEXT NOT NULL,
                            hours_hand_colour TEXT NOT NULL,
                            minutes_hand_colour TEXT NOT NULL,
                            seconds_hand_colour TEXT NOT NULL,
                            smooth_tick TEXT NOT NULL,
                            FOREIGN KEY(display_instance_id) REFERENCES display_instances (display_instance_id)
                            )""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS digital_clock 
                            (display_instance_id INTEGER NOT NULL,
                            display_surface_id INTEGER NOT NULL,
                            timezone TEXT NOT NULL,
                            timezone_label_enable TEXT NOT NULL,
                            time_format TEXT NOT NULL,
                            text_colour TEXT NOT NULL,
                            FOREIGN KEY(display_instance_id) REFERENCES display_instances (display_instance_id)
                            )""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS static_text 
                            (display_instance_id INTEGER NOT NULL,
                            display_surface_id INTEGER NOT NULL,
                            label_text TEXT NOT NULL,
                            text_colour TEXT NOT NULL,
                            FOREIGN KEY(display_instance_id) REFERENCES display_instances (display_instance_id)
                            )""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS static_image 
                            (display_instance_id INTEGER NOT NULL,
                            display_surface_id INTEGER NOT NULL,
                            image_id INTEGER NOT NULL,
                            FOREIGN KEY(display_instance_id) REFERENCES display_instances (display_instance_id)
                            )""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS stacked_image 
                            (display_instance_id INTEGER NOT NULL,
                            display_surface_id INTEGER NOT NULL,
                            image_stack_id INTEGER NOT NULL,
                            FOREIGN KEY(display_instance_id) REFERENCES display_instances (display_instance_id)
                            )""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS top_banner 
                            (display_instance_id INTEGER NOT NULL,
                            display_surface_id INTEGER NOT NULL,
                            image_id INTEGER NOT NULL,
                            FOREIGN KEY(display_instance_id) REFERENCES display_instances (display_instance_id)
                            FOREIGN KEY(image_id) REFERENCES images (image_id)
                            )""")
        
        
        
        #Default database entries for the system to work
        self.add_controller_type("Network", "Network", 0, 0, 0, 0, 0)
        self.add_controller_type("Arduino", "UNO", 18, 2, 20, 14, 20)
        self.add_controller_type("Arduino", "MEGA", 52, 2, 54, 0, 0)

        self.__add_network_controller(0, "Network", "Network", "N/A", "N/A", "Network", "N/A", "N/A")

        self.logger.debug(f"Commiting Changes")
        self.connection.commit()
        self.logger.info("Database Initialised")


    #Add a device entry into the database
    def add_device(self, device_name, device_ip, location, msg_group_id, display_instance_id):
        #Insert a row into the device table
        self.cursor.execute(f"INSERT INTO devices (device_name, device_ip, location, message_group_id, display_instance_id) VALUES (?,?,?,?,?)", (device_name, device_ip, location, msg_group_id, display_instance_id))
        self.connection.commit()

    def add_controller_type(self, manufacturer, model, total_gpio_pins, start_pin_index, end_pin_index, start_input_only_pin_index, end_input_only_pin_index):
        self.cursor.execute(f"INSERT INTO controller_types (manufacturer, model, total_gpio_pins, start_pin_index, end_pin_index, start_input_only_pin_index, end_input_only_pin_index) VALUES (?,?,?,?,?,?,?)", (manufacturer, model, total_gpio_pins, start_pin_index, end_pin_index, start_input_only_pin_index, end_input_only_pin_index))
        self.connection.commit()

    #Add a controller entry into the database
    def add_controller(self, controller_name, controller_location, controller_ip, controller_port, controller_type):
        #Insert a row into the controllers table
        self.cursor.execute(f"INSERT INTO controllers (controller_name, controller_location, controller_ip, controller_port, controller_type) VALUES (?,?,?,?,?)", (controller_name, controller_location, controller_ip, controller_port, controller_type))
        self.connection.commit()

        #Adds the default network controller to the database
    def __add_network_controller(self, controller_id, controller_name, controller_location, controller_ip, controller_port, controller_type, start_pin_index, end_pin_index):
        #Insert a row into the controllers table
        self.cursor.execute(f"INSERT INTO controllers (controller_id, controller_name, controller_location, controller_ip, controller_port, controller_type) VALUES (?,?,?,?,?,?)", (controller_id, controller_name, controller_location, controller_ip, controller_port, controller_type))
        self.connection.commit()

    def add_pin_mode(self, controller_id, pin_id, pin_mode):
        self.cursor.execute(f"INSERT INTO pin_modes (controller_id, pin_id, pin_mode) VALUES (?,?,?)", (controller_id, pin_id, pin_mode))
        self.connection.commit()

    #Add a display template entry to the database
    def add_display_template(self, display_template_name, total_columns, total_rows, layout_matrix, last_changed):
        #Insert a row into the display template table
        self.cursor.execute(f"""INSERT INTO display_templates (display_template_name, 
                            total_columns,
                            total_rows,
                            layout_matrix, 
                            last_changed) VALUES (?,?,?,?,?)""", 
                            (display_template_name, 
                            total_columns,
                            total_rows,
                            layout_matrix, 
                            last_changed))
        self.connection.commit()

    def add_display_surface(self, display_template_id, display_surface_id, widget_string, top_left_coord_column, top_left_coord_row, block_width, block_height):
        #Insert a row into the display surfaces table
        self.cursor.execute(f"""INSERT INTO display_surfaces (display_template_id, 
                            display_surface_id, 
                            widget_string, 
                            top_left_coord_column, 
                            top_left_coord_row, 
                            block_width, 
                            block_height) VALUES (?,?,?,?,?,?,?)""", 
                            (display_template_id, 
                             display_surface_id, 
                             widget_string, 
                             top_left_coord_column, 
                             top_left_coord_row, 
                             block_width, 
                             block_height))
        self.connection.commit()

    def add_display_instance(self, display_instance_name:str, display_template_id:str, last_changed):
        #Insert a row into the display instances table
        self.cursor.execute(f"""INSERT INTO display_instances (display_instance_name, display_template_id, last_changed) VALUES (?,?,?)""", 
                            (display_instance_name,
                             display_template_id,
                             last_changed))
        self.connection.commit()

    #Add a message group entry to the database
    def add_message_group(self, message_group_name):
        #Insert a new value into the database table
        self.cursor.execute(f"INSERT INTO message_groups (message_group_name) VALUES (?)",(message_group_name,))
        self.connection.commit()

    #Add an image entry to the database
    def add_image(self, image_name, image_file):
        #Insert a new value into the database table
        self.cursor.execute(f"INSERT INTO images (image_name, image_file) VALUES (?,?)",(image_name, image_file))
        self.connection.commit()

    #Add an message entry to the database
    def add_message(self, message_text : str, message_timestamp : str):
        #Insert a new value into the database table
        self.cursor.execute(f"INSERT INTO messages (message_text, message_timestamp) VALUES (?,?)",(message_text, message_timestamp))
        self.connection.commit()    

    #Add an active_message entry to the database
    def add_active_message(self, message_id : int, message_group_id : int):
        #Insert a new value into the database table
        self.cursor.execute(f"INSERT INTO active_messages (message_id, message_group_id) VALUES (?,?)",(message_id, message_group_id))
        self.connection.commit()   

    #Add an input_trigger entry to the database
    """Current state should be set to False by default"""
    def add_input_trigger(self, input_trigger_name:str, controller_id:str, address:str, current_state:bool):
        self.logger.debug(f"Querying database with data: Input Trigger Name:{input_trigger_name}, Controller ID:{controller_id}, Address:{address}")
        #Insert a new value into the database table
        self.cursor.execute(f"INSERT INTO input_triggers (input_trigger_name, controller_id, address, current_state) VALUES (?,?,?,?)",(input_trigger_name, controller_id, address, current_state))
        self.connection.commit()   

    #Add an input_logic entry to the database
    def add_input_logic(self, input_logic_name, high_condition:str):
        #Insert a new value into the database table
        self.cursor.execute(f"INSERT INTO input_logics (input_logic_name, high_condition) VALUES (?,?)",(input_logic_name, high_condition))
        self.connection.commit()   

    #Add an input_logic_mapping entry to the database
    def add_input_logic_mapping(self, input_logic_id:str, input_trigger_id:str):
        #Insert a new value into the database table
        self.cursor.execute(f"INSERT INTO input_logic_mapping (input_logic_id, input_trigger_id) VALUES (?,?)",(input_logic_id, input_trigger_id))
        self.connection.commit()   

    #Add an output_logic_mapping entry to the database
    def add_output_logic(self, output_logic_name:str, input_logic_id:str, current_state:bool):
        #Insert a new value into the database table
        self.cursor.execute(f"INSERT INTO output_logics (output_logic_name, input_logic_id, current_state) VALUES (?,?,?)",(output_logic_name, input_logic_id, current_state))
        self.connection.commit()   

    #Add an output_trigger entry to the database
    def add_output_trigger(self, output_trigger_name:str, output_type:str, controller_id:str, address:str, ip_address:str, port:int, protocol:str, command_high:str, arguments_high:str, command_low:str, arguments_low:str):
        #Insert a new value into the database table
        self.cursor.execute(f"INSERT INTO output_triggers (output_trigger_name, output_type, controller_id, address, ip_address, port, protocol, command_high, arguments_high, command_low, arguments_low) VALUES (?,?,?,?,?,?,?,?,?,?,?)",(output_trigger_name, output_type, controller_id, address, ip_address, port, protocol, command_high, arguments_high, command_low, arguments_low))
        self.connection.commit()  

    #Add an output_logic_mapping entry to the database
    def add_output_logic_mapping(self, output_logic_id:str, output_trigger_id:str):
        #Insert a new value into the database table
        self.cursor.execute(f"INSERT INTO output_logic_mapping (output_logic_id, output_trigger_id) VALUES (?,?)",(output_logic_id, output_trigger_id))
        self.connection.commit()   

    def add_top_banner(self, display_instance_id, display_surface_id, config_list:list):
            self.cursor.execute(f"INSERT INTO top_banner (display_instance_id, display_surface_id, image_id) VALUES (?,?,?)", (display_instance_id, display_surface_id, config_list[0]))
            self.connection.commit()

    def add_studio_clock(self, display_instance_id, display_surface_id, config_list:list):
        self.cursor.execute(f"INSERT INTO studio_clock (display_instance_id, display_surface_id, timezone, timezone_label_enable, legend_colour) VALUES (?,?,?,?,?)", (display_instance_id, display_surface_id, config_list[0], config_list[1], config_list[2]))
        self.connection.commit()

    def add_analogue_clock(self, display_instance_id, display_surface_id, config_list:list):
        self.cursor.execute(f"""INSERT INTO analogue_clock (display_instance_id, 
                            display_surface_id, 
                            timezone, 
                            timezone_label_enable, 
                            clock_face_colour, 
                            legend_colour, 
                            hours_hand_colour, 
                            minutes_hand_colour, 
                            seconds_hand_colour, 
                            smooth_tick) VALUES (?,?,?,?,?,?,?,?,?,?)""", (display_instance_id, display_surface_id, config_list[0], config_list[1], config_list[2], config_list[3], config_list[4], config_list[5], config_list[6], config_list[7]))
        self.connection.commit()

    def add_digital_clock(self, display_instance_id, display_surface_id, config_list:list):
        self.cursor.execute(f"""INSERT INTO digital_clock (display_instance_id, 
                            display_surface_id, 
                            timezone, 
                            timezone_label_enable, 
                            time_format,
                            text_colour) VALUES (?,?,?,?,?,?)""", (display_instance_id, display_surface_id, config_list[0], config_list[1], config_list[2], config_list[3]))
        self.connection.commit()

    def add_static_text(self, display_instance_id, display_surface_id, config_list:list):
        self.cursor.execute(f"""INSERT INTO static_text (display_instance_id, 
                            display_surface_id, 
                            label_text, 
                            text_colour) VALUES (?,?,?,?)""", (display_instance_id, display_surface_id, config_list[0], config_list[1]))
        self.connection.commit()

    def add_static_image(self, display_instance_id, display_surface_id, config_list:list):
        self.cursor.execute(f"""INSERT INTO static_image (display_instance_id, 
                            display_surface_id, 
                            image_id) VALUES (?,?,?)""", (display_instance_id, display_surface_id, config_list[0]))
        self.connection.commit()

    def add_stacked_image(self, display_instance_id, display_surface_id, config_list:list):
        self.cursor.execute(f"""INSERT INTO stacked_image (display_instance_id, 
                            display_surface_id, 
                            image_stack_id) VALUES (?,?,?)""", (display_instance_id, display_surface_id, config_list[0]))
        self.connection.commit()

    def add_indicator(self, display_instance_id, display_surface_id, config_list:list):
            self.cursor.execute(f"""INSERT INTO indicator (display_instance_id, 
                                display_surface_id, 
                                indicator_label, 
                                on_colour, 
                                flash_enable, 
                                input_logic_id) VALUES (?,?,?,?,?,?)""", (display_instance_id, display_surface_id, config_list[0], config_list[1], config_list[2], config_list[3]))
            self.connection.commit()
#-----------------------------------------------------------------------------------------------------------------------------

    #Generic function to delete a row from any table given an id
    def delete_row(self, table_name, condition, id):
        
        #Turn on Foreign Key Support
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.cursor.execute("PRAGMA foreign_keys")
        #foreign_key_status = self.cursor.fetchall()
        #self.logger.debug(f"Foreign Key Status:{foreign_key_status}")
        #Remove a value from the table
        try:
            self.cursor.execute(f"DELETE FROM {table_name} WHERE {condition} = ?",(id,))
            self.connection.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error in deleting item: {e}")
            return e
        
    #Generic function to delete a row from any table given an id
    def delete_row_dual_condition(self, table_name, condition1, value1, condition2, value2):
        
        #Turn on Foreigh Key Support
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.cursor.execute("PRAGMA foreign_keys")
        #foreign_key_status = self.cursor.fetchall()
        #self.logger.debug(f"Foreign Key Status:{foreign_key_status}")
        #Remove a value from the table
        try:
            self.cursor.execute(f"DELETE FROM {table_name} WHERE {condition1} = (?) AND {condition2} = (?)",(value1,value2,))
            self.connection.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error in deleting item: {e}")
            return e

    
    #Generic function to get all the data held in the database for a specified table
    def get_current_table_data(self, table_name):
        self.cursor.execute(f"SELECT * FROM {table_name}")
        updated_rows = self.cursor.fetchall()
        return updated_rows
    
    #Generic function to get all column data for a specified row in a specified table given the item id
    def get_current_row_data(self, table_name, condition, id):
        self.logger.debug("Querying the database")
        self.cursor.execute(f"SELECT * FROM {table_name} WHERE {condition} = ?",(id,))
        row = self.cursor.fetchall()
        #self.logger.debug(f"Returned data:{row}")
        return row
    
    #Generic function to return all rows that meet the specified contition, sorting ascending by the specifiec sort column.
    def get_rows_condition_sort_asc(self, table_name, condition, condition_value, sort_column):
        self.logger.debug("Querying the database")
        self.cursor.execute(f"SELECT * FROM {table_name} WHERE {condition} = ? ORDER BY {sort_column} ASC",(condition_value,))
        row = self.cursor.fetchall()
        #self.logger.debug(f"Returned data:{row}")
        return row
    
    #Generic function to return all columns for the row matching both conditions
    def get_current_row_data_dual_condition(self, table_name, condition1, value1, condition2, value2):
        self.logger.debug("Querying the database")
        self.cursor.execute(f"SELECT * FROM {table_name} WHERE {condition1} = (?) AND {condition2} = (?)",(value1,value2,))
        row = self.cursor.fetchall()
        self.logger.debug(f"Returned data:{row}")
        return row
    
    def update_trigger_mapping(self, table_name, condition1, value1, condition2, value2, controller_id, gpi):
        self.cursor.execute(f"UPDATE {table_name} SET controller_id = (?), gpi = (?) WHERE {condition1} = (?) AND {condition2} = (?)",(controller_id, gpi, value1, value2,))
        self.connection.commit()

    #Generic function to update a single columns value in a specified table given the item id
    def update_row(self, table_name, column, id_column_name, updated_value, id):
        self.cursor.execute(f"UPDATE {table_name} SET {column} = (?) WHERE {id_column_name} = (?)",(updated_value, id))
        self.connection.commit()

    #Updates a row given 2 conditions
    def update_row_dual_condition(self, table_name, update_column, updated_value, condition1, condition_value1, condition2, condition_value2):
        self.cursor.execute(f"UPDATE {table_name} SET {update_column} = (?) WHERE {condition1} = (?) AND {condition2} = (?)",(updated_value, condition_value1, condition_value2,))
        self.connection.commit()

    #Backs-up the entire database to file
    def backup_db(self):
        self.logger.info("Attempting to backup the Database")
        #Open a cmd shell and use the .backup command to copy the database to file
        subprocess.call(["sqlite3", "database/oatis_db", ".backup 'database/backup_oatis_db'"])
        self.logger.info("Database Backup Successful")

    #Generic function to get all data for 1 selected column in a selected table given an id and condition - Always returns a list
    def get_1column_data(self, column1, table_name, condition, id) -> list:
        self.cursor.execute(f"SELECT {column1} FROM {table_name} WHERE {condition} = ?",(id,))
        #Fetch the returned row and extract the string from the list
        data = self.cursor.fetchall()

        #If no results are returned - A blank list is returned from the database
        if len(data) == 0 :
            #Return the blank list
            returned_data : list = data
            self.logger.debug("Database Query Returned No Results")
        
        #If one or more result is returned
        if len(data) >= 1:
            #Blank list to hold the data to be returned
            return_list :list = []

            for column in data:
                #Extract the data from each tuple and place in a list
                return_list.append(column[0])

            #Return the populated list
            returned_data : list = return_list
            self.logger.debug("Database Query Returned 1 or More Results")
        
        self.logger.debug(f"Database Returned: {returned_data}")
        return returned_data

    #Generic function to get all data for 2 selected columns in a selected table
    def get_2column_data(self, column1, column2, table_name):
        self.cursor.execute(f"SELECT {column1}, {column2} FROM {table_name}")
        column = self.cursor.fetchall()
        return column
    
    #Generic function to return 1 column from all rows given 2 conditions from a specified table
    def get_1column_data_dual_condition(self, column, condition1, value1, condition2, value2, table_name):
        self.cursor.execute(f"SELECT {column} FROM {table_name} WHERE {condition1} = (?) AND {condition2} = (?)",(value1,value2,))
        rows_list_of_tuples = self.cursor.fetchall()
        #Extract the data items nested in the list of tuples and reformat into a single list
        rows_list = []
        for tuple in rows_list_of_tuples:
            data_item = tuple[0]
            rows_list.append(data_item)

        return rows_list
    
    #Generic function to return 2 columns from all rows given 2 conditions from a specified table
    def get_2column_data_dual_condition(self, column1, column2, condition1, value1, condition2, value2, table_name):
        self.cursor.execute(f"SELECT {column1}, {column2} FROM {table_name} WHERE {condition1} = (?) AND {condition2} = (?)",(value1,value2,))
        rows = self.cursor.fetchall()
        return rows

    def get_last_insert_row_id(self):
        """Returns the row id for the last inserted item"""

        self.cursor.execute(f"SELECT last_insert_rowid()")
        row_id = self.cursor.fetchall()[0][0]

        return row_id


    