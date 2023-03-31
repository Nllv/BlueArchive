import os
from time import sleep, time

from control_emulator.util import f_time, img_crop

import config.config
from control_emulator.control import Control, ControlEmulatorError

from data.coord import Login, Tutorial as TutorialCoord, Gacha, Home
from data.filters import HSVFilters
from lib.account_manager import AccountManager


class ControlBlueArchive(Control):
    def __init__(self, window_name, serial):
        super().__init__(window_name, serial)
        self.config_init(working_folder=self.get_root_folder(),
                         window_name=window_name,
                         package_name='com.YostarJP.BlueArchive')
        self.account_manager = AccountManager(window_name)
        self.save = -1

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

        timeout = f_time(180)
        while True:
            img = self.capture()
            for _error in [Home.NETWORK_ERROR, Home.NETWORK_ERROR2]:
                if self.search(*_error, src=img):
                    raise ControlEmulatorError()
            if timeout < time():
                raise ControlEmulatorError()

            if self.search(*Login.MENU, src=img):
                break
            sleep(0.5)
        while self.search(*Login.MENU):
            self.area_tap(348, 172, 682, 354)
            sleep(1)

        timeout = f_time(180)
        while True:
            if timeout < time():
                raise ControlEmulatorError()
            self.check_network_errors()
            for args in [Login.KIYAKU_OK, Login.NEWS, TutorialCoord.GUEST, Login.LOGIN_BONUS_BG]:
                if self.search(*args):
                    if args == Login.KIYAKU_OK:
                        self.accept_agreement()
                    if args == Login.NEWS:
                        self.close_news()
                        return
                    if args == TutorialCoord.GUEST:
                        return
                    if args == Login.LOGIN_BONUS_BG:
                        self.login_bonus()
                sleep(0.1)

    def close_news(self):
        while self.search(*Login.NEWS):
            self.area_tap(845, 64, 870, 85)

    def login_bonus(self):
        self.wait_image(*Login.LOGIN_BONUS_BG)
        while self.search(*Login.LOGIN_BONUS_BG):
            self.area_tap(854, 85, 904, 113)
            sleep(0.1)

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
                # if self.search(*Gacha.SKIP):
                #     self.gacha_skip()
                # else:
                while self.search(*Gacha.THREE_STAR):
                    self.area_tap(27, 25, 102, 101)
                    sleep(0.2)
            if self.search(*Gacha.RESULT_OK):
                self.image_tap(*Gacha.RESULT_OK)
                break

    def get_mail(self):
        if 240 <= self.get_color(884, 12, 1):
            self.image_tap(*Home.MAIL)
            while not self.search(*Home.INVENTORY) and not self.search(*Home.NO_MAIL):
                self.area_tap(786, 484, 917, 519)
                sleep(1)

    def go_to_home(self):
        while not self.search(*Home.MOMO_TALK):
            if self.search(*Login.MENU):
                self.login(-2)
            self.back()
            sleep(1)

    def receive_mission(self):
        self.image_tap(*Home.MISSION, interval=2)
        self.wait_image(*Home.ALL_RECEIVE)
        for _ in range(5):
            self.area_tap(*self.img_coord())
        self.go_to_home()

    def check_network_errors(self):
        img = self.capture()
        for _error in [Home.NETWORK_ERROR, Home.NETWORK_ERROR2, Login.MENU]:
            if self.search(*_error, src=img):
                raise ControlEmulatorError()
        if self.current_app() != self.package_name:
            raise ControlEmulatorError()

    def check_student(self):
        self.wait_image(*Home.STUDENT_LIST)
        charas = self.account_manager.find_chara()
        self.screen_shot(f'gacha_result/{self.save}.png')
        if 12 <= self.search(self.img_path_builder('three_star', 'home'), hsvfilter=HSVFilters.STAR_FOOTBAR):
            cnt = 1
            while True:
                self.swipe(484, 387, 484, 182, 0.5)
                sleep(1)
                add_charas = self.account_manager.find_chara()
                diff = [chara for chara in add_charas if chara not in charas]
                if len(diff):
                    charas += add_charas
                    self.screen_shot(f'gacha_result/{self.save}_{cnt}.png')
                    cnt += 1
                else:
                    break


if __name__ == '__main__':
    from config.config import emulator_connection
    emulator_number = 7
    self = ControlBlueArchive(emulator_connection[emulator_number]['window_name'],
                              emulator_connection[emulator_number]['port'])
    # self.del_save_folder()
    # self.push_save_folder(3005)
    # self.pull_save_folder()
    self.save = 3005
    # self.login(3005)
    self.check_student()
