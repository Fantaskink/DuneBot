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
    with open('subreddits.csv', 'r') as f:
        reader = csv.reader(f)
        lines = [line for line in reader]
        for i, row in enumerate(lines):
            if channel in row or subreddit in row:
                lines[i] = [channel, subreddit,"False"]
                found = True
                break
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

def set_true(row_index):
    with open('subreddits.csv', 'r') as f:
        reader = csv.reader(f)
        lines = [line for line in reader]

        # Sets boolean value from csv file to true
        lines[row_index][2] = "True"
    
    with open('subreddits.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(lines)
                

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

def get_rows_with_false():
    # Open the CSV file for reading
    with open('subreddits.csv', 'r') as file:
        # Create a CSV reader object
        reader = csv.reader(file)
        # Initialize an empty list to store the rows with "False" in the third column
        false_rows = []
        # Iterate through each row in the CSV file
        for row in reader:
            # Check if the third column in the row is "False"
            if row[2] == "False":
                # If it is, add the row to the list
                false_rows.append(row)
        return false_rows

