import random
from datetime import datetime, timedelta, time as dt_time
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
        self.is_log_refresh = False

    def get_save_number(self, is_refresh=True):
        def is_before_4am(date_strings):
            four_am = datetime.combine(datetime.today(), dt_time(hour=4))
            now = datetime.now()
            if now < four_am:
                four_am = four_am - timedelta(days=1)
            result = []

            for date_string in date_strings:
                # 文字列をdatetimeオブジェクトに変換
                date_time = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
                result.append(date_time < four_am)

            return result

        self.sqlite.exclusive_transaction()
        logins_record = self.sqlite.execute_all('SELECT * FROM logins')
        soldout = self.sqlite.execute_all('SELECT * FROM soldout')
        if is_refresh:
            _date_strings = [account_info[1] for account_info in logins_record]
            before_4am = is_before_4am(_date_strings)
            logins_record = [account_info[0] for account_info, _bool in zip(logins_record, before_4am) if _bool]
        else:
            logins_record = [account_info[0] for account_info in logins_record]
            logins2_record = self.sqlite.execute_all('SELECT * FROM logins')
            logins_record = [save_id for save_id in logins_record if save_id not in logins2_record]
        logins_record = [save_id for save_id in logins_record if save_id not in soldout]
        self.record_login(logins_record[0], is_transaction=False)
        self.sqlite.commit()
        return logins_record[0]

        # mutex = self.lock(5)
        # logined = read_csv('csv/login.csv')
        # for save in save_list:
        #     if save not in logined:
        #         self.log_write(save, 'login.csv', self.is_log_refresh)
        #         self.unlock(mutex)
        #         return save

    def run(self):
        def del_login():
            mutex = self.lock(5)
            login_list = read_csv('csv/login.csv')
            with open('csv/login.csv', mode='w', encoding='UTF-8') as f:
                for save_number in login_list:
                    if save_number != self.save:
                        f.write(f'{save_number}\n')
            self.unlock(mutex)

        login_cnt = 1
        while True:
            wait_by_timezone([3, 50, 0], [4, 0, 0])
            # save_list = get_save_list()
            soldout = read_csv('csv/soldout.csv')
            # save_list = [save for save in save_list if save not in soldout]
            # save_list.reverse()
            # self.save = self.get_save_number(save_list)
            self.save = self.get_save_number()
            time_print(f'LOGIN : {self.save}')
            try:
                self.login(self.save)
                self.get_mail()
                self.go_to_home()
                self.receive_mission()
                # self.gacha(Gacha.LIMITED_PICK_UP_2, 'ムツキ(正月)')
                # self.gacha(Gacha.LIMITED_PICK_UP_1, 'アル(正月)')
                self.check_student()
                self.get_cooperation_code()
            except ControlEmulatorError:
                self.stop_app()
                self.is_vpn_connected = False
                del_login()
            except self.device_errors:
                self.device_init()
                del_login()
            login_cnt += 1
            if 20 <= login_cnt:
                self.reboot_emulator()
                login_cnt = 1

if __name__ == '__main__':
    emulator_number = 7
    self = Farming(emulator_connection[emulator_number]['window_name'], emulator_connection[emulator_number]['port'])
    self.run()