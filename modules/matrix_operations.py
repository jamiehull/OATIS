def find_display_sections(layout_matrix):
        """Finds the display secions in the layout matrix and their top_left_coordinate, returning a dict.
        Keys are display section id's, values are the top_left_coordinate as a tuple."""
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

        return display_section_id_dict

def find_display_section_dimensions(layoput_matrix:list, display_section_id:int, top_left_coord:tuple, total_columns:int, total_rows:int):
        """Finds the dimension of a display section"""
        width=0
        height=0

        #Origin to start scanning from
        x=top_left_coord[0]
        y=top_left_coord[1]

        #Finding width
        for i in range(total_columns - top_left_coord[0]):
            if layoput_matrix[y][x] == display_section_id:
                #print(f"Position:{x},{y}")
                width += 1
                x += 1

        #Origin to start scanning from
        x=top_left_coord[0]
        y=top_left_coord[1]

        #Finding height
        for i in range(total_rows - top_left_coord[1]):
            if layoput_matrix[y][x] == display_section_id:
                #print(f"Position:{x},{y}")
                height += 1
                y += 1

        return width, height