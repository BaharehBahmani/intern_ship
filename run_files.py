#from dataset_builder import main
#import typer
#from typer import Option
import os

if __name__ == '__main__':
    # python subreddit_downloader.py Ovariancancer --reddit-id QIUAai3QO4eAFTbZJVpPpA --reddit-secret 15txVuRiWx3qPG2A1l1ZoyXgBxAmzA 
    # --reddit-username Hojjat_HB --batch-size 100 --laps 4 --debug
    os.system('python subreddit_downloader.py ' + 'Ovariancancer' + ' --run-id 2' + ' --reddit-id QIUAai3QO4eAFTbZJVpPpA' + ' --reddit-secret 15txVuRiWx3qPG2A1l1ZoyXgBxAmzA' +
              ' --reddit-username Hojjat_HB' + ' --batch-size 10' + ' --laps 1' + ' --utc-after ' + str(1556660300) + ' --comments-cap 100' + ' --debug')
    os.system('python dataset_builder.py --subreddit-dir ' + 'Ovariancancer' + ' --run-id 2')