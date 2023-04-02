from config import config
from lib.tutorial import Tutorial
from lib.farming import Farming


def runner(window_name, serial):
    if config.do_task == 'farming':
        self = Farming(window_name, serial)
        self.run()
    elif config.do_task == 'tutorial':
        self = Tutorial(window_name, serial)
        self.run()