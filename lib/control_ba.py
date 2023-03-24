import os
from time import sleep

import config.config
from control_emulator.control import Control

from data.coord import Login, Tutorial as TutorialCoord, Gacha
from lib.account_manager import AccountManager
from lib.tutorial import Tutorial


class ControlBlueArchive(Control):
    def __init__(self, window_name, serial):
        super().__init__(serial)
        self.config_init(working_folder=self.get_root_folder(),
                         window_name=window_name,
                         package_name='com.YostarJP.BlueArchive')
        self.account_manager = AccountManager(window_name)

    def login(self, save_number=-1):
        self.vpn_init()
        self.stop_app()
        self.cache_clear()
        self.login_preprocessing()
        if -1 <= save_number:
            self.del_save_folder()
        if 0 < save_number:
            self.push_save_folder(save_number)
        self.start_app()

        self.wait_image(*Login.MENU)
        while self.search(*Login.MENU):
            self.area_tap(348, 172, 682, 354)
            sleep(1)

        for args in [Login.KIYAKU_OK, Login.NEWS, TutorialCoord.GUEST]:
            if self.search(*args):
                if args == Login.KIYAKU_OK:
                    self.accept_agreement()
                if args == Login.NEWS:
                    self.close_news()
                    return
                if args == TutorialCoord.GUEST:
                    tutorial = Tutorial(self.window_name, self.serial)
                    tutorial.run()

    def close_news(self):
        while self.search(*Login.NEWS):
            self.area_tap(845, 64, 870, 85)

    def accept_agreement(self):
        while self.search('image/login/check_mark.bmp') < 2:
            while not self.search(*Login.FIRST_CHECK_MARK):
                self.area_tap(122, 378, 141, 397)
                sleep(1)
            while not self.search(*Login.SECOND_CHECK_MARK):
                self.area_tap(579, 378, 601, 399)
                sleep(1)
        self.image_tap(*Login.KIYAKU_OK)

    def login_preprocessing(self):
        del_tar_file = ['.save', 'AgreementStatusSaveData']
        folder = '/storage/emulated/0/Android/data/com.YostarJP.BlueArchive/files'
        result = self.device_class.adb_command(
            ['shell', 'ls', folder],
            self.device_class.serial
        )
        file_list = result.decode('utf-8').replace('\n', '').split('\r')
        for f in file_list:
            if f != '' and any([tar in f for tar in del_tar_file]):
                self.device_class.adb_command(['shell', 'rm', '-rf', f'{folder}/{f}'], self.device_class.serial)

    def gacha_skip(self):
        self.image_tap(*Gacha.SKIP)

    def process_gacha_result(self):
        pulled_chara = []
        while True:
            if self.search(*Gacha.SKIP) and not self.search(*Gacha.THREE_STAR):
                self.gacha_skip()
            if self.search(*Gacha.THREE_STAR):
                pulled_chara.append(self.account_manager.get_gacha_character())
                if self.search(*Gacha.SKIP):
                    self.gacha_skip()
                else:
                    while not self.search(*Gacha.RESULT_OK):
                        self.area_tap(27, 25, 102, 101)
                        sleep(0.2)
                    self.image_tap(*Gacha.RESULT_OK)


if __name__ == '__main__':
    from config.config import emulator_connection
    emulator_number = 5
    self = ControlBlueArchive(emulator_connection[emulator_number]['window_name'],
                              emulator_connection[emulator_number]['port'])
    # self.del_save_folder()
    # self.push_save_folder(1)
    # self.pull_save_folder()
    self.login(-1)
