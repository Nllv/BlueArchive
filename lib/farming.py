import random
from time import sleep

from control_emulator.util import wait_by_timezone, get_save_list, read_csv, time_print

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
        def del_login():
            mutex = self.lock(5)
            login_list = read_csv('csv/login.csv')
            with open('csv/login.csv', mode='w', encoding='UTF-8') as f:
                for save_number in login_list:
                    if save_number != self.save:
                        f.write(f'{save_number}\n')
            self.unlock(mutex)

        while True:
            save_list = get_save_list()
            soldout = read_csv('csv/soldout.csv')
            save_list = [save for save in save_list if save not in soldout]
            save_list.reverse()
            self.save = self.get_save_number(save_list)
            time_print(f'LOGIN : {self.save}')
            try:
                self.login(self.save)
                self.get_mail()
                self.go_to_home()
                self.receive_mission()
                self.gacha(Gacha.LIMITED_PICK_UP_2, 'ムツキ(正月)')
                self.check_student()
            except ControlEmulatorError:
                self.stop_app()
                self.is_vpn_connected = False
                del_login()
            except self.device_errors:
                self.device_init()
                del_login()

if __name__ == '__main__':
    emulator_number = 7
    self = Farming(emulator_connection[emulator_number]['window_name'], emulator_connection[emulator_number]['port'])
    self.run()