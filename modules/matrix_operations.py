def find_display_sections(layout_matrix):
        """Finds the display secions in the layout matrix and their top_left_coordinate, returning a dict.
        Keys are display section id's, values are the top_left_coordinate as a tuple."""
        print("#######---Finding Display Section ID's in Layout Matrix and their Top Left Coordinates---#######")

        #Working Dict storing section id's and their top left coordinate
        display_section_id_dict = {}

        #Origin to start scanning from
        x=0
        y=0

        #Loop to find each area id and its origin
        for row in layout_matrix:
            for column in row:
                if column not in display_section_id_dict:
                    display_section_id_dict[column] = (x, y)
                x += 1 #Advance to next column
            y += 1 #Advance to next row
            x = 0 #Reset column position to 0 as we are in a new row

        print(f"Display Section Top Left Coordinates: {display_section_id_dict}")

        return display_section_id_dict

def find_display_section_dimensions(layout_matrix:list, display_section_id:int, top_left_coord:tuple, total_columns:int, total_rows:int):
        """Finds the dimension of a display section in terms of display blocks."""
        print(f"#######---Finding Dimensions of Display Section: {display_section_id}---#######")
        print(f"Input Layout Matrix: {layout_matrix}")
        width=0
        height=0

        #Origin to start scanning from
        x=top_left_coord[0]
        y=top_left_coord[1]

        #Finding width
        for i in range(total_columns - top_left_coord[0]):
            if layout_matrix[y][x] == display_section_id:
                #print(f"Position:{x},{y}")
                width += 1
                x += 1
            else:
                 break

        #Origin to start scanning from
        x=top_left_coord[0]
        y=top_left_coord[1]

        #Finding height
        for i in range(total_rows - top_left_coord[1]):
            if layout_matrix[y][x] == display_section_id:
                #print(f"Position:{x},{y}")
                height += 1
                y += 1
            else:
                 break
            
        print(f"Display Section {display_section_id} width:{width}, height:{height}")

        return width, height

def verify_surface_is_rect(layout_matrix:list, display_section_id:int, top_left_coord:tuple) -> bool:
    """Checks if a display surface is a rectangle and not repeated."""
    print(f"#######---Verifying diplay section ID: {display_section_id} is not duplicated in another block.---#######")
    print(f"Input Layout Matrix: {layout_matrix}")

    #Our test result we will return
    valid = True

    total_columns = len(layout_matrix[0])
    total_rows = len(layout_matrix)

    #Origin to start scanning from
    top_left_coord_x = top_left_coord[0]
    top_left_coord_y = top_left_coord[1]

    #Only start if we are given a valid start coord with the specified display_section_id
    if layout_matrix[top_left_coord_y][top_left_coord_x] == display_section_id:

        #First find the dimensions of the display section
        width, height = find_display_section_dimensions(layout_matrix, display_section_id, top_left_coord, total_columns, total_rows)

        #Display Section id coords
        display_section_id_coords_list = []

        #Check all expected coords are assigned the display id
        if valid == True:
            for row in range(top_left_coord_y, top_left_coord_y+height):
                if valid == True:
                    for column in range(top_left_coord_x, top_left_coord_x+width):
                        print(f"Expecting Diplay Section ID:{display_section_id} at {top_left_coord_y},{column}, found {layout_matrix[row][column]}")
                        if layout_matrix[row][column] != display_section_id:
                            print("Unexpected Display ID Found!")
                            valid *= False
                            break
                        else:
                            display_section_id_coords_list.append((row,column))
                else:
                    print(f"Display Section: {display_section_id}, not a rectangle!")
                    break

        #Check other coords do not have the same display id
        if valid == True:
            for row in range(0, total_rows):
                if valid == True:
                    for column in range(0, total_columns):
                        coordinates = (row,column)
                        if coordinates not in display_section_id_coords_list:
                            if layout_matrix[row][column] == display_section_id:
                                valid *= False
                                print(f"Display Section ID:{display_section_id} occurs at unexpected coordinate {coordinates}.")
                                break

    else:
        print(f"Invalid start coordinate specified! Coord:{top_left_coord}")
        valid *= False

    return valid

    


        

     