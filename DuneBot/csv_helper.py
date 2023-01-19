import csv
import os

# Create "subreddits.csv" if it does not exist
if os.path.exists("subreddits.csv"):
    pass
else:
    with open('subreddits.csv', 'w') as creating_new_csv_file: 
        pass

def set_subreddit(channel, subreddit):
    channel = str(channel)
    subreddit = str(subreddit)
    found = False
    lines = []
    with open('subreddits.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if channel in row:
                found = True
                row = [channel, subreddit,"False"]
            lines.append(row)
    if not found:
        lines.append([channel, subreddit,"False"])
    with open('subreddits.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(lines)


def get_rows():
    # open the CSV file
    with open('subreddits.csv', 'r') as file:
        # read the contents of the file using the csv.reader object
        csv_reader = csv.reader(file)
        
        # create an empty list to store the rows
        data = []
        
        # iterate over the rows in the file
        for row in csv_reader:
            # append each row as a separate list to the data list
            data.append(row)

    return(data)

def update_csv_row(id_to_find, new_value):
    # Open the CSV file
    with open('subreddits.csv', 'r') as csvfile:
        # Create a CSV reader
        reader = csv.reader(csvfile)
        # Create a new list to store the updated rows
        rows = []
        # Iterate through the rows in the CSV
        for row in reader:
            # Check if the first column matches the ID we're looking for
            if row[0] == id_to_find:
                # Update the third column with the new value
                row[2] = new_value
            # Add the row to the list of updated rows
            rows.append(row)
    # Open the CSV file again, this time in write mode
    with open('subreddits.csv', 'w', newline='') as csvfile:
        # Create a CSV writer
        writer = csv.writer(csvfile)
        # Write the updated rows to the file
        writer.writerows(rows)
                

def set_all_false():
    with open('subreddits.csv', 'r') as f:
        reader = csv.reader(f)
        lines = [line for line in reader]

    with open('subreddits.csv', 'w') as f:
        writer = csv.writer(f)
        
        if len(lines):
            for line in lines:
                line[2] = "False"

        writer.writerows(lines)

def delete_row( row_index):
    # Open the CSV file for reading
    with open('subreddits.csv', 'r') as file:
        # Create a CSV reader object
        reader = csv.reader(file)
        # Convert the CSV reader object to a list
        data = list(reader)

    # Delete the specified row
    del data[row_index]

    # Open the CSV file for writing
    with open('subreddits.csv', 'w') as file:
        # Create a CSV writer object
        writer = csv.writer(file)
        # Write the updated data to the CSV file
        writer.writerows(data)

