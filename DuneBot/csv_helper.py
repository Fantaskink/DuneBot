import csv

import os

if os.path.exists("subreddits.csv"):
    pass
else:
    with open('subreddits.csv', 'w') as creating_new_csv_file: 
        pass

def set_subreddit(channel, subreddit):

    

    channel = str(channel)
    subreddit = str(subreddit)

    print(channel, subreddit)

    found = False
    with open('subreddits.csv', 'r') as f:
        reader = csv.reader(f)
        lines = [line for line in reader]
        for i, row in enumerate(lines):
            if channel in row or subreddit in row:
                lines[i] = [channel, subreddit]
                found = True
                break
    if not found:
        lines.append([channel, subreddit])

    with open('subreddits.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(lines)


def get_channels_and_subs():
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