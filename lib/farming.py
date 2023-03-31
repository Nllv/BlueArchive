import random
from time import sleep

from control_emulator.util import wait_by_timezone, get_save_list, read_csv

from config.config import emulator_connection
from control_emulator.control import ControlEmulatorError
from lib.control_ba import ControlBlueArchive
from data.coord import Tutorial as TutorialCoord, Login, Home, Gacha
from lib.account_manager import AccountManager


class Farming(ControlBlueArchive):
    def __init__(self, window_name, serial):
        super().__init__(window_name, serial)
        self.config_init(working_folder=self.get_root_folder(),
                         window_name=window_name,
                         package_name='com.YostarJP.BlueArchive')
        self.account_manager = AccountManager(window_name)
        self.is_log_refresh = True

    def get_save_number(self, save_list):
        mutex = self.lock(5)
        logined = read_csv('csv/login.csv')
        for save in save_list:
            if save not in logined:
                self.log_write(save, 'login.csv', self.is_log_refresh)
                self.unlock(mutex)
                return save

    def run(self):
        save_list = get_save_list()
        self.save = self.get_save_number(save_list)
        self.login(self.save)
        self.get_mail()
        self.go_to_home()
        self.receive_mission()


if __name__ == '__main__':
    emulator_number = 7
    self = Farming(emulator_connection[emulator_number]['window_name'], emulator_connection[emulator_number]['port'])
    self.run()