from lib.tutorial import Tutorial
from config.config import emulator_connection


if __name__ == '__main__':
    emulator_number = 7
    self = Tutorial(emulator_connection[emulator_number]['window_name'], emulator_connection[emulator_number]['port'])
    self.run()