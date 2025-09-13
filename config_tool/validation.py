import ipaddress

#A class to validate data inputs
class Validation:

    #Function to check for a valid ip address in the correct format
    def validate_ip(ip_string):
        try:
            ip_object = ipaddress.ip_address(ip_string) #Throws ValueError exception if not valid
            valid = True

        except ValueError:
            valid = False

        return valid