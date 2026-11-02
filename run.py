"""Launch FileSift.   python run.py            -> open the app
                     python run.py --reminders -> show due warranty reminders and exit (used by Task Scheduler)
"""
import sys

from filesift.app import main

if __name__ == "__main__":
    sys.exit(main())
