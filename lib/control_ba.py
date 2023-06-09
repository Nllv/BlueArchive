import os
from datetime import timedelta
from time import sleep, time

from control_emulator.util import f_time, img_crop, read_csv, time_print

import config.config
from control_emulator.control import Control, ControlEmulatorError

from data.coord import Login, Tutorial as TutorialCoord, Gacha, Home
from data.filters import HSVFilters
from lib.account_manager import AccountManager
from lib.sqlitedb import SQLiteDB


class ControlBlueArchive(Control):
    def __init__(self, window_name, serial):
        super().__init__(window_name, serial)
        self.config_init(working_folder=self.get_root_folder(),
                         window_name=window_name,
                         package_name='com.YostarJP.BlueArchive')
        self.account_manager = AccountManager(window_name)
        self.sqlite = SQLiteDB('blue_archive.db')
        self.save = -1

    def record_login(self, save_number, is_transaction=True):
        if is_transaction:
            # トランザクションの開始
            self.sqlite.exclusive_transaction()

        # SQL文
        now = self.sqlite.get_now_dt()
        self.sqlite.execute('INSERT OR REPLACE INTO logins (save_id, updated_at) VALUES (?, ?)', (save_number, now))
        self.sqlite.execute('INSERT OR REPLACE INTO logins2 (save_id) VALUES (?)', (save_number,))

        # トランザクションの終了
        self.sqlite.conn.commit()

    def remove_record_login(self, save_number, is_transaction=True):
        if is_transaction:
            # トランザクションの開始
            self.sqlite.exclusive_transaction()
        # SQL文
        now = self.sqlite.get_now_dt() - timedelta(days=1)
        self.sqlite.execute('INSERT OR REPLACE INTO logins (save_id, updated_at) VALUES (?, ?)', (save_number, now))
        self.sqlite.execute(f'DELETE FROM logins2 where save_id = {save_number}')
        self.sqlite.commit()

    def add_soldout(self, save_number):
        # トランザクションの開始
        self.sqlite.exclusive_transaction()
        self.sqlite.execute('INSERT OR REPLACE INTO soldout (save_id) VALUES (?)', (save_number,))
        self.sqlite.commit()

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

    def reboot_emulator(self):
        self.is_vpn_connected = False
        self.device_class.ld_command(['reboot', '--name', self.window_name])
        sleep(30)
        self.device_init()

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

    def process_gacha_result(self, single_pull=False, is_tutorial=False):
        pulled_chara = []
        while True:
            img = self.capture()
            if single_pull and not self.search(*Gacha.THREE_STAR):
                while self.search('image/gacha/star.bmp', 10, 391, 83, 492, 0.9):
                    self.area_tap(27, 25, 102, 101)
                    sleep(0.2)
            if self.search(*Gacha.SKIP, src=img) and not self.search(*Gacha.THREE_STAR, src=img):
                self.gacha_skip()
                self.wait_images([['image/gacha/star.bmp', 10, 391, 83, 492, 0.9], Gacha.RESULT_OK])
                sleep(0.5)
            elif self.search(*Gacha.THREE_STAR, src=img):
                pulled_chara.append(self.account_manager.get_gacha_character())
                # if self.search(*Gacha.SKIP):
                #     self.gacha_skip()
                # else:
                while self.search(*Gacha.THREE_STAR):
                    self.area_tap(27, 25, 102, 101)
                    sleep(0.2)
            elif self.search(*Gacha.RESULT_OK, src=img):
                self.image_tap(*Gacha.RESULT_OK)
                if is_tutorial:
                    break
            elif self.search(*Gacha.RESULT_OK2, src=img):
                self.image_tap(*Gacha.RESULT_OK2, interval=2)
                break
            sleep(0.1)
            self.check_network_errors()
        return pulled_chara

    def get_mail(self):
        if 240 <= self.get_color(884, 12, 1):
            while not self.search('image/home/all_receive.bmp', 801, 481, 900, 525, 0.9):
                self.area_tap(839, 19, 876, 38)
                sleep(1)
                self.check_network_errors()
            while not self.search(*Home.INVENTORY) and not self.search(*Home.NO_MAIL):
                self.area_tap(786, 484, 917, 519)
                sleep(1)

    def go_to_home(self):
        while not self.search(*Home.MOMO_TALK) and not self.search(*Home.BUY_STONE):
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
        def go_to_student():
            self.image_tap(*Home.STUDENT, interval=3)

        def skip_first_arona_talk():
            self.wait_image(*Home.STUDENT_LIST)
            while self.search(*Home.STUDENT_LIST):
                self.area_tap(55, 166, 171, 274)
        def tutorial():
            if self.search(*TutorialCoord.STUDENT_MESSAGE1):
                home_pos = 915, 5, 936, 27
                # レベル
                skip_first_arona_talk()
                while not self.search(*Home.BUY_STONE):
                    self.area_tap(638, 89, 765, 117)
                    self.area_tap(*home_pos)
                go_to_student()

                # 装備
                skip_first_arona_talk()
                while not self.search(*Home.BUY_STONE):
                    self.area_tap(*home_pos)
                go_to_student()

                # スキル
                skip_first_arona_talk()
                while not self.search(*Home.BUY_STONE):
                    self.area_tap(519, 238, 582, 316)
                    self.area_tap(845, 245, 878, 309)
                    self.area_tap(*home_pos)
                go_to_student()

        self.go_to_home()
        go_to_student()
        self.wait_image(*Home.STUDENT_LIST)
        sleep(2)
        tutorial()

        if not self.search(self.img_path_builder('three_star', 'home'), hsvfilter=HSVFilters.STAR_FOOTBAR):
            sort_ok = 'image/home/ok.bmp', 549, 410, 603, 449, 0.9
            while not self.search(*sort_ok):
                self.area_tap(715, 74, 785, 95)
            sleep(2)
            for _ in range(3):
                self.area_tap(270, 117, 349, 137)
            self.image_tap(*sort_ok, interval=2)

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

        self.register_character_info(self.save, charas)
        # mutex = self.lock(5)
        # chara_csv = read_csv('csv/chara.csv')
        # chara_csv = [line for line in chara_csv if self.save not in line]
        # chara_csv.append([self.save, len(charas)] + charas)
        # chara_csv.sort(key=lambda x: x[0])
        # with open('csv/chara.csv', mode='w', encoding='UTF-8') as f:
        #     for line in chara_csv:
        #         write_str = f'{line[0]}, {line[1]}, {", ".join(line[2:])}\n'
        #         f.write(write_str)
        #     # chara_str = ', '.join(charas)
        #     # f.write(f'{self.save}, {len(charas)}, {chara_str}\n')
        # self.unlock(mutex)

    def gacha(self, gacha_type:str, gacha_tar=None):
        """
        ガチャを引く
        :param gacha_type: Coord形式
        :param gacha_tar: キャラ名
        :return:
        """
        if gacha_tar:
            all_account_info = self.account_manager.get_all_account_info()
            if self.save in all_account_info and gacha_tar in all_account_info[self.save]:
                return
        pulled_chara = []
        self.go_to_home()
        self.image_tap(*Home.GACHA, interval=5)
        while not self.search(*gacha_type):
            self.area_tap(6, 274, 25, 299)
            sleep(0.5)

        for pos in [[706, 360, 901, 416]]:
        # for pos in [[706, 360, 901, 416], [487, 362, 665, 417]]:
            while True:
                self.wait_image(*gacha_type)
                while not self.search(*Gacha.PULL_OK):
                    self.area_tap(*pos)
                    self.im_sleep(*Gacha.PULL_OK, sleep_time=2)
                sleep(2)
                if self.search(*Gacha.STONE_LESS):
                    while self.search(*Gacha.STONE_LESS):
                        self.area_tap(26, 83, 109, 148)
                    break
                self.image_tap(*Gacha.PULL_OK)
                now_pulled = self.process_gacha_result(single_pull=pos==[487, 362, 665, 417])
                pulled_chara += now_pulled
                if gacha_tar in pulled_chara:
                    time_print(pulled_chara)
                    return
        time_print(pulled_chara)

    def get_cooperation_code(self):
        self.go_to_home()
        while not self.search(*Home.MENU):
            self.area_tap(890, 16, 936, 38)
            sleep(0.5)
        while self.search(*Home.MENU):
            self.area_tap(490, 207, 644, 245)
            sleep(0.5)
        while not self.search('image/home/device_code.bmp', threshold=0.8):
            self.swipe(468, 412, 468, 162)
            sleep(0.5)
        self.wait_image('image/home/device_code.bmp', threshold=0.8)
        pos = self.img_coord()
        while not self.search(*Home.CODE):
            self.area_tap(pos[0] + 384, pos[1] - 5, pos[0] + 459, pos[1] + 25)

        # ID取得
        self.device.clipboard = None
        while not self.device.clipboard:
            self.area_tap(637, 209, 686, 229)
        _id = self.device.clipboard

        # コード生成
        for _ in range(3):
            self.area_tap(542, 288, 609, 308)
        sleep(1)

        # コード取得
        self.device.clipboard = None
        while not self.device.clipboard:
            self.area_tap(638, 289, 683, 309)
            sleep(2)
        _code = self.device.clipboard

        self.sqlite.exclusive_transaction()
        self.sqlite.execute(
            'INSERT OR REPLACE INTO accounts (save_id, cooperation_id, cooperation_code) VALUES (?, ?, ?)',
            (self.save, _id, _code)
        )
        self.sqlite.commit()
        # with open('csv/code.csv', encoding='UTF-8', mode='a') as f:
        #     f.write(f'{self.save}, {_id}, {_code}\n')

    def register_character_info(self, save_id: int, characters: list):
        self.sqlite.exclusive_transaction()
        for chara in characters:
            if chara in self.account_manager.limited_chara:
                is_limited = 1
            else:
                is_limited = 0
            self.sqlite.execute(
                'INSERT OR REPLACE INTO characters (save_id, character_name, is_limited) VALUES (?, ?, ?)',
                (save_id, chara, is_limited)
            )
        self.sqlite.commit()


if __name__ == '__main__':
    from config.config import emulator_connection
    emulator_number = 3
    self = ControlBlueArchive(emulator_connection[emulator_number]['window_name'],
                              emulator_connection[emulator_number]['port'])
    # self.del_save_folder()
    # self.push_save_folder(3005)
    # self.pull_save_folder()
    chara_csv = read_csv('csv/chara.csv')
    accounts_number = [account[0] for account in chara_csv]
    chara_csv = [account[2:] for account in chara_csv]
    for save_id, characters in zip(accounts_number, chara_csv):
        self.register_character_info(save_id, characters)

    self.save = 3757
    self.login(self.save)
    self.check_student()
    # self.get_cooperation_code()