from lib.tutorial import Tutorial
from config.config import emulator_connection
from runner import runner

if __name__ == '__main__':
    emulator_number = 4
    runner(emulator_connection[emulator_number]['window_name'], emulator_connection[emulator_number]['port'])

    self = Tutorial(emulator_connection[emulator_number]['window_name'], emulator_connection[emulator_number]['port'])
    self.run()