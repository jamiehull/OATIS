import sqlite3
import tkinter as tk
import subprocess
import logging

class DB:
    def __init__(self):

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #Create a connection to the database
        self.connection = sqlite3.connect("database/rds_db")
        #Check the connection to the database was established
        self.logger.info(self.connection.total_changes)
        #Create a cursor object to manipulate the database
        self.cursor = self.connection.cursor()
        #Used for verification, the total number of tables in a valid database that has been correctly initialised
        self.total_number_tables = 8

    def connect(self):
        #Create a connection to the database
        self.logger.info("Connecting to database")
        self.connection = sqlite3.connect("database/rds_db")
        #Create a cursor object to manipulate the database
        self.cursor = self.connection.cursor()
        self.logger.info("Connection established")

    def close_connection(self):
        #Create a connection to the database
        self.logger.info("Closing connection to database")
        self.connection.close()

    def verify_database_setup(self):
        self.logger.info("Verifying the database is valid")
        table_names = ["devices", "locations", "trigger_mappings", "controllers", "trigger_groups", "display_templates", "messaging_groups", "images"]
        table_count = 0
        for table_name in table_names:
            #Count the number of tables with the specified table name present in sqlite_master
            self.cursor.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            #Returns 0 if table not exist, 1 if table exists
            table_exist = self.cursor.fetchone()
            #Add the result to the count variable, total should equal number of required tables
            table_count += table_exist[0]

        self.logger.info(f"Found {table_count} valid tables in the database, required {self.total_number_tables}")
        
        if table_count == self.total_number_tables:
            self.logger.info("All required tables present")
            return True
        
        else:
            self.logger.info("Database corrupt or not initialised.")
            return False
            
    def initialise_database(self):
        self.logger.info("Initialising the Database...")
        #Drop All Tables in the Database
        self.logger.debug("Dropping all tables")
        self.cursor.execute("DROP TABLE IF EXISTS devices")
        self.cursor.execute("DROP TABLE IF EXISTS locations")
        self.cursor.execute("DROP TABLE IF EXISTS trigger_mappings")
        self.cursor.execute("DROP TABLE IF EXISTS controllers")
        self.cursor.execute("DROP TABLE IF EXISTS trigger_groups")
        self.cursor.execute("DROP TABLE IF EXISTS images")
        self.cursor.execute("DROP TABLE IF EXISTS display_templates")
        self.cursor.execute("DROP TABLE IF EXISTS messaging_groups")
        self.cursor.execute("DROP TABLE IF EXISTS active_messages")
        self.cursor.execute("DROP TABLE IF EXISTS messages")
        
        self.logger.debug("Dropped all tables if they existed.")
        #Re-create all tables
        self.logger.debug("Creating all required tables.")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS devices 
                            (device_id INTEGER PRIMARY KEY AUTOINCREMENT,
                             device_name TEXT, 
                             device_ip TEXT, 
                            location TEXT, 
                            messaging_group_id INTEGER, 
                            trigger_group_id INTEGER, 
                            display_template_id INTEGER, 
                            FOREIGN KEY(messaging_group_id) REFERENCES messaging_groups(messaging_group_id),
                            FOREIGN KEY(trigger_group_id) REFERENCES trigger_groups(trigger_group_id),
                            FOREIGN KEY(display_template_id) REFERENCES display_templates(display_template_id))""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS locations 
                            (location_id INTEGER PRIMARY KEY, 
                             location TEXT)""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS trigger_mappings 
                            (trigger_group_id INTEGER,
	                        trigger	TEXT,
	                        controller_id INTEGER,
	                        gpi INTEGER,
	                        FOREIGN KEY(controller_id) REFERENCES controllers (controller_id),
	                        FOREIGN KEY(trigger_group_id) REFERENCES trigger_groups (trigger_group_id))""")

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS controllers 
                            (controller_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            controller_name TEXT, 
                            controller_location TEXT, 
                            controller_ip TEXT, 
                            controller_port TEXT, 
                            controller_type TEXT, 
                            pin2 TEXT, 
                            pin3 TEXT, 
                            pin4 TEXT, 
                            pin5 TEXT, 
                            pin6 TEXT, 
                            pin7 TEXT, 
                            pin8 TEXT, 
                            pin9 TEXT, 
                            pin10 TEXT, 
                            pin11 TEXT, 
                            pin12 TEXT,
                            pin13 TEXT,
                            pin14 TEXT,
                            pin15 TEXT,
                            pin16 TEXT,
                            pin17 TEXT,
                            pin18 TEXT, 
                            pin19 TEXT)""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS trigger_groups 
                            (trigger_group_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            trigger_group_name TEXT 
                            )""")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS display_templates 
                            (display_template_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            display_template_name TEXT, 
                            layout TEXT, 
                            logo_image_id INTEGER, 
                            clock_type TEXT, 
                            indicators_displayed INTEGER, 
                            indicator_1_label TEXT, 
                            indicator_1_flash TEXT, 
                            indicator_1_colour TEXT, 
                            indicator_2_label TEXT, 
                            indicator_2_flash TEXT, 
                            indicator_2_colour TEXT,
                            indicator_3_label TEXT, 
                            indicator_3_flash TEXT, 
                            indicator_3_colour TEXT,
                            indicator_4_label TEXT, 
                            indicator_4_flash TEXT, 
                            indicator_4_colour TEXT,
                            indicator_5_label TEXT, 
                            indicator_5_flash TEXT, 
                            indicator_5_colour TEXT,
                            indicator_6_label TEXT, 
                            indicator_6_flash TEXT, 
                            indicator_6_colour TEXT, 
                            last_changed TEXT, 
                            FOREIGN KEY(logo_image_id) REFERENCES images (image_id))""")
        
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS messaging_groups 
                            (messaging_group_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            messaging_group_name TEXT,
                            osc_address TEXT)""")
        
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
                            FOREIGN KEY(message_group_id) REFERENCES messaging_groups (messaging_group_id))""")
    

        self.logger.debug("Commiting Changes")
        self.connection.commit()

        self.logger.info("Database Initialised")
        self.logger.info(self.connection.total_changes)

    #Add a device entry into the database
    def add_device(self, device_name, device_ip, location, msg_group_id, trig_grp_id, display_tmplt_id):
        #Insert a row into the device table
        self.cursor.execute(f"INSERT INTO devices (device_name, device_ip, location, messaging_group_id, trigger_group_id, display_template_id) VALUES (?,?,?,?,?,?)", (device_name, device_ip, location, msg_group_id, trig_grp_id, display_tmplt_id))
        self.connection.commit()

    #Add a trigger_group entry into the database
    def add_trigger_group(self, trigger_group_name):
        #Insert a row into the trigger_groups table
        self.cursor.execute(f"INSERT INTO trigger_groups (trigger_group_name) VALUES (?)", (trigger_group_name,))
        self.connection.commit()

    #Add a mapping entry into the database
    def add_trigger_mapping(self, trigger_group_id, trigger, controller_id, gpi):
        #Insert a row into the trigger_mappings table
        self.cursor.execute(f"INSERT INTO trigger_mappings (trigger_group_id, trigger, controller_id, gpi) VALUES (?,?,?,?)", (trigger_group_id, trigger, controller_id, gpi))
        self.connection.commit()

    #Add a controller entry into the database
    def add_controller(self, controller_name, controller_location, controller_ip, controller_port, controller_type, pin2, pin3, pin4, pin5, pin6, pin7, pin8, pin9, pin10, pin11, pin12, pin13, pin14, pin15, pin16, pin17, pin18, pin19):
        #Insert a row into the controllers table
        self.cursor.execute(f"INSERT INTO controllers (controller_name, controller_location, controller_ip, controller_port, controller_type, pin2, pin3, pin4, pin5, pin6, pin7, pin8, pin9, pin10, pin11, pin12, pin13, pin14, pin15, pin16, pin17, pin18, pin19) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (controller_name, controller_location, controller_ip, controller_port, controller_type, pin2, pin3, pin4, pin5, pin6, pin7, pin8, pin9, pin10, pin11, pin12, pin13, pin14, pin15, pin16, pin17, pin18, pin19))
        self.connection.commit()

    #Add a display template entry to the database
    def add_display_template(self, 
                            display_template_name, 
                            layout, 
                            logo_image_id, 
                            clock_type, 
                            indicators_displayed, 
                            indicator_1_label, 
                            indicator_1_flash, 
                            indicator_1_colour, 
                            indicator_2_label, 
                            indicator_2_flash, 
                            indicator_2_colour,
                            indicator_3_label, 
                            indicator_3_flash, 
                            indicator_3_colour,
                            indicator_4_label, 
                            indicator_4_flash, 
                            indicator_4_colour,
                            indicator_5_label, 
                            indicator_5_flash, 
                            indicator_5_colour,
                            indicator_6_label, 
                            indicator_6_flash, 
                            indicator_6_colour, 
                            last_changed):
        #Insert a row into the diusplay template table
        self.cursor.execute(f"""INSERT INTO display_templates (display_template_name, 
                            layout, 
                            logo_image_id, 
                            clock_type, 
                            indicators_displayed, 
                            indicator_1_label, 
                            indicator_1_flash, 
                            indicator_1_colour, 
                            indicator_2_label, 
                            indicator_2_flash, 
                            indicator_2_colour,
                            indicator_3_label, 
                            indicator_3_flash, 
                            indicator_3_colour,
                            indicator_4_label, 
                            indicator_4_flash, 
                            indicator_4_colour, 
                            indicator_5_label, 
                            indicator_5_flash, 
                            indicator_5_colour,
                            indicator_6_label, 
                            indicator_6_flash, 
                            indicator_6_colour, 
                            last_changed) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
                            (display_template_name, 
                            layout, 
                            logo_image_id, 
                            clock_type, 
                            indicators_displayed, 
                            indicator_1_label, 
                            indicator_1_flash, 
                            indicator_1_colour, 
                            indicator_2_label, 
                            indicator_2_flash, 
                            indicator_2_colour,
                            indicator_3_label, 
                            indicator_3_flash, 
                            indicator_3_colour,
                            indicator_4_label, 
                            indicator_4_flash, 
                            indicator_4_colour,
                            indicator_5_label, 
                            indicator_5_flash, 
                            indicator_5_colour,
                            indicator_6_label, 
                            indicator_6_flash, 
                            indicator_6_colour, 
                            last_changed))
        self.connection.commit()

    #Add a messaging group entry to the database
    def add_messaging_group(self, message_group_name, osc_address):
        #Insert a new value into the database table
        self.cursor.execute(f"INSERT INTO messaging_groups (messaging_group_name, osc_address) VALUES (?,?)",(message_group_name, osc_address))
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





    #Generic function to delete a row from any table given an id
    def delete_row(self, table_name, condition, id):
        
        #Turn on Foreigh Key Support
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.cursor.execute("PRAGMA foreign_keys")
        foreign_key_status = self.cursor.fetchall()
        self.logger.debug(f"Foreign Key Status:{foreign_key_status}")
        #Remove a value from the table
        try:
            self.cursor.execute(f"DELETE FROM {table_name} WHERE {condition} = ?",(id,))
            self.connection.commit()
            return True
        except Exception as e:
            return e

        #Refresh the treeviewer GUI when menu button clicked
    
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

    #Backs-up the entire database to file
    def backup_db(self):
        self.logger.info("Attempting to backup the Database")
        #Open a cmd shell and use the .backup command to copy the database to file
        subprocess.call(["sqlite3", "database/rds_db", ".backup 'database/backup_rds_db'"])
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
    