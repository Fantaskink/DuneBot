import csv

def set_subreddit(channel, subreddit):
    print(channel, subreddit)

    index = 0

    with open('subreddits.csv', 'r') as csvfile:
        csv_reader = csv.reader(csvfile)

        for row in csv_reader:
            if channel in row or subreddit in row:
                index = row.index


