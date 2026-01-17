import ipaddress
import logging


def validate_inputs(inputs_list:list[tuple]):
    """
    Validates input data.
    Pass in a list of tuples containing (input_data, validation_condition)
    Function will return True if all data is valid, False if not
    """
    #Setup Logging
    logger = logging.getLogger(__name__)

    logger.info("Validating input data")

    valid = True

    for input_data in inputs_list:
        logger.debug(f"Input Data:{input_data}")

        test_data = input_data[0]
        test_condition = input_data[1]

        logger.debug(f"Test Data:{test_data}, Test Condition:{test_condition}")

        if test_condition == "not_null":
            valid = validate_not_null(test_data)

        elif test_condition == "not_null_ip_address":
            valid = validate_ip(test_data)

        elif test_condition == "not_null_ip_address_or_n/a":
            valid = validate_ip_na(test_data)

        elif test_condition == "not_null_not_in_db":
            valid = validate_not_null_not_in_db(test_data)

        elif test_condition == "not_null_display_builder":
            valid = validate_not_null_display_builder(test_data)

        elif test_condition == "not_null_display_instance_config":
            valid = validate_not_null_display_instance_config(test_data)

        elif test_condition == "null_or_osc_command":
            valid = validate_na_or_null_or_osc_command(test_data)

        elif test_condition == "not_null_osc_command_input_trigger":
            #The value of the previous data item determines what test we run
            controller = inputs_list[1][0]
            if controller[0] == "0": #OSC
                valid = validate_not_null_osc_command(test_data)
            else:                   #GPI
                valid = validate_not_null(test_data)

        elif test_condition == "null_or_osc_args":
            valid = validate_null_or_osc_args(test_data)

        elif test_condition == "n/a":
            #Don't invalidate the test if a condition is not specified
            pass

        else:
            logger.error(f"Invalid test condition {test_condition} specified.")
            valid = False
        #If any of the above conditions return false, break the loop
        if valid == False:
            logger.warning(f"Test Data:{test_data} failed test condition:{test_condition}")
            break

    logger.info(f"Input Data Valid:{valid}")

    return valid



def validate_not_null(test_data) -> bool:
    if test_data != ""  and test_data != [] and test_data != () and test_data != {}:
        return True
    else:
        return False

#Function to check for a valid ip address in the correct format
def validate_ip(ip_string) -> bool:
    try:
        ip_object = ipaddress.ip_address(ip_string) #Throws ValueError exception if not valid
        valid = True

    except ValueError:
        valid = False

    return valid

#Function to check for a valid ip address in the correct format or N/A
def validate_ip_na(ip_string) -> bool:
    if ip_string == "N/A":
        valid = True
    else:
        try:
            ip_object = ipaddress.ip_address(ip_string) #Throws ValueError exception if not valid
            valid = True

        except ValueError:
            valid = False

    return valid

def validate_not_null_not_in_db(test_data) -> bool:
    """Validates an image path is not null and is not 'Stored in Database'"""
    #Check not null
    not_null = validate_not_null(test_data)
    not_in_db = False

    #Check not stored in DB
    if test_data != "Stored in Database":
        not_in_db = True
    else:
        not_in_db = False

    #Return the outcome
    if not_null and not_in_db == True:
        return True
    else:
        return False
    
from modules.gui_templates import Display_Template
def validate_not_null_display_builder(test_data : Display_Template) -> bool:
    """Validates all data fields in the Display Builder Frame."""
    
    #Setup Logging
    logger = logging.getLogger(__name__)

    logger.debug(f"Display builder test data:{test_data}")

    valid = True

    valid *= validate_not_null(test_data.display_template_name)
    valid *= validate_not_null(test_data.number_of_columns)
    valid *= validate_not_null(test_data.number_of_rows)
    valid *= validate_not_null(test_data.layout_matrix)
    valid *= validate_not_null(test_data.display_area_dict)

    return valid

def validate_not_null_display_instance_config(test_data: tuple[str,str,list]) -> bool:
    """Validates all data fields in the Display Instance Config Frame."""

    #Setup Logging
    logger = logging.getLogger(__name__)

    logger.debug(f"Display Instance Test Data:{test_data}")

    valid = True
    #Instance Name
    valid *= validate_not_null(test_data[0])
    #Display Template ID
    valid *= validate_not_null(test_data[1])

    #Config Frames
    config_valid = test_data[3]
    logger.debug(f"Valid config: {config_valid}")
    
    if config_valid == True:
        valid *= True
    else:
        valid *= False

    return valid

def validate_not_null_osc_command(test_data:str) -> bool:
    """Validates and OSC Command."""
    try:
        valid = True

        #Check if data is not null
        valid *= validate_not_null(test_data)

        #Check the osc command is valid
        #Checking for / at start
        valid *= bool(test_data[0] == "/")
        #Checking no whitespace
        valid *= bool(test_data.count(" ") == 0)

    except IndexError:
        valid = False

    finally:
        return valid
    
def validate_na_or_null_or_osc_command(test_data:str) -> bool:
    """Validates and OSC Command."""
    try:
        valid = True

        #Check data is N/A
        na = validate_na(test_data)

        if na == False:
            #Check if null
            not_null = validate_not_null(test_data)

            if not_null == True:
                #Check the osc command is valid
                #Checking for / at start
                valid *= bool(test_data[0] == "/")
                #Checking no whitespace
                valid *= bool(test_data.count(" ") == 0)
        else:
            valid = True
    except IndexError:
        valid = False

    finally:
        return valid
    
def validate_null_or_osc_args(test_data:str) -> bool:
    """Validates OSC Arguments."""
    try:
        valid = True

        #Check data is not null
        not_null = validate_not_null(test_data)

        if not_null == True:
            #Valid OSC Args should be seperated by whitespace, we split these into a list
            args_list = test_data.split()
            if args_list == []:
                valid = False
        else:
            valid = True

    except IndexError:
        valid = False

    finally:
        return valid

def validate_na(test_data:str) -> bool:
    """Checks if the test data == N/A"""
    try:
        valid = True
        
        if test_data == "N/A":
            valid = True

        else: valid = False

    except Exception:
        valid = False

    finally:
        return valid
    


