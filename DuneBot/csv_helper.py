import csv

def set_subreddit(channel, subreddit):
    print(channel, subreddit)

    # Open the csv file for reading and writing
    with open("subreddits.csv", "r+") as csv_file:
        # Read all the rows into a list
        rows = csv_file.readlines()

        # Iterate through each row
        for i, row in enumerate(rows):
            # Split the row into a list
            row_data = row.strip().split(",")

            # Check if the row contains either of the strings
            if channel in row_data or subreddit in row_data:
                # Overwrite the row with new data
                rows[i] = channel + "," + subreddit + "\n"
        
        # Clear the file
        csv_file.seek(0)
        csv_file.truncate()
        
        # Write the rows back to the file
        csv_file.writelines(rows)


