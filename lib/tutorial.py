import random
from time import sleep

from config.config import emulator_connection
from control_emulator.control import ControlEmulatorError
from lib.control_ba import ControlBlueArchive
from data.coord import Tutorial as TutorialCoord, Login, Home, Gacha
from lib.account_manager import AccountManager


class Tutorial(ControlBlueArchive):
    def __init__(self, window_name, serial):
        super().__init__(window_name, serial)
        self.config_init(working_folder=self.get_root_folder(),
                         window_name=window_name,
                         package_name='com.YostarJP.BlueArchive')
        self.account_manager = AccountManager(window_name)

    def run(self):
        while True:
            try:
                self.login(-1)
                self.create_guest_account()
                self.tutorial_1()
                self.tutorial_2()
                self.tutorial_3()
                self.tutorial_4()
                self.tutorial_5()
                self.stop_app()
                self.pull_save_folder()
            except ControlEmulatorError:
                self.stop_app()
                self.is_vpn_connected = False
            except self.device_errors:
                self.device_init()

    def create_guest_account(self):
        self.image_tap(*TutorialCoord.GUEST)
        self.accept_agreement()
        self.image_tap(*TutorialCoord.CREATE_ACCOUNT_OK)
        self.wait_image(*TutorialCoord.NAME_OK)
        self.input_random_name()
        self.image_tap(*TutorialCoord.NAME_OK)
        self.image_tap(*TutorialCoord.CALLED_NAME_OK)
        self.image_tap(*TutorialCoord.NOTIFICATION_OK)

    def input_random_name(self):
        while not self.device(text='OK').exists:
            self.area_tap(430, 265, 504, 284)
            sleep(1)
        name = random.choice(
            ['ユウキ', 'カエデ', 'ハルカ', 'ナオキ', 'ショウタ', 'アイカ', 'サトシ', 'ミカエ', 'ハルミ', 'キョウコ']
        )
        self.input_key(name)
        self.device(text='OK').click()

    def skip_talk(self):
        self.wait_images([TutorialCoord.MENU, TutorialCoord.MENU2])
        # while self.search(*TutorialCoord.MENU) or self.search(*TutorialCoord.SKIP):
        while True:
            if self.search(*TutorialCoord.OK_BUTTON):
                self.image_tap(*TutorialCoord.OK_BUTTON, interval=2)
                break
            elif self.search(*TutorialCoord.SKIP):
                self.area_tap(*self.img_coord())
            elif self.search(*TutorialCoord.MENU):
                self.image_tap(*TutorialCoord.MENU, interval=0.1)
            sleep(0.1)

    def tutorial_1(self):
        self.wait_image(*TutorialCoord.STR_END, deadline=120)
        while self.search(*TutorialCoord.STR_END):
            self.area_tap(369, 139, 607, 322)
            sleep(1)
        self.wait_image(*TutorialCoord.STR_END)
        while True:
            self.check_network_errors()
            if self.search(*TutorialCoord.MENU) or self.search(*TutorialCoord.MENU2):
                self.skip_talk()
            elif self.search(*TutorialCoord.RIN):
                self.rin_talk_skip()
                break
            sleep(0.5)
        self.wait_rin()
        self.use_skill1()
        self.wait_rin()
        self.use_skill2()
        self.process_battle_result()

    def tutorial_2(self):
        while True:
            self.check_network_errors()
            if self.search(*TutorialCoord.MENU) or self.search(*TutorialCoord.MENU2):
                self.skip_talk()
            elif self.search(*TutorialCoord.RIN):
                self.rin_talk_skip()
                break
            sleep(0.5)
        while True:
            self.check_network_errors()
            if self.search(*TutorialCoord.MENU) or self.search(*TutorialCoord.MENU2):
                self.skip_talk()
            elif self.search(*TutorialCoord.RIN):
                self.use_skill3()
                break
            sleep(0.5)
        self.process_battle_result()

    def tutorial_3(self):
        while True:
            self.check_network_errors()
            if self.search(*TutorialCoord.MENU):
                self.skip_talk()
            self.area_tap(335, 179, 635, 314)
            if self.search(*TutorialCoord.MOVIE_SKIP_OK):
                self.image_tap(*TutorialCoord.MOVIE_SKIP_OK)
                break
            sleep(0.1)
        self.wait_image(*Home.MOMO_TALK, deadline=300)
        sleep(3)
        while self.search(*Home.MOMO_TALK):
            self.area_tap(653, 458, 709, 521)
            sleep(0.2)
        self.wait_image(*TutorialCoord.FREE)
        while not self.search(*Gacha.PULL_OK):
            self.area_tap(722, 364, 892, 414)
        self.image_tap(*Gacha.PULL_OK)
        self.process_gacha_result()

    def wait_rin(self):
        self.wait_image(*TutorialCoord.RIN)

    def rin_talk_skip(self):
        img = self.capture(805, 14, 855, 37)
        while self.search(img, 805, 14, 855, 37, threshold=0.95):
            self.area_tap(16, 453, 78, 516)

    def use_skill1(self):
        while not self.search(*TutorialCoord.SKILL1):
            self.area_tap(716, 434, 765, 492)
            sleep(0.5)
        while self.search(*TutorialCoord.SKILL1):
            self.area_tap(713, 130, 730, 150)

    def use_skill2(self):
        img = self.capture(805, 14, 855, 37)
        while self.search(img, 805, 14, 855, 37, 0.95):
            self.area_tap(640, 440, 688, 490)

    def use_skill3(self):
        while not self.search(*TutorialCoord.SKILL3):
            self.area_tap(638, 439, 687, 491)
            sleep(0.5)
        while self.search(*TutorialCoord.SKILL3):
            self.area_tap(692, 115, 747, 162)

    def process_battle_result(self):
        self.wait_image(*TutorialCoord.BATTLE_RESULT_OK)
        self.image_tap(*TutorialCoord.BATTLE_RESULT_OK)

    def tutorial_4(self):
        self.wait_image(*TutorialCoord.ENTER)
        while not self.search(*TutorialCoord.MISSION_START):
            self.area_tap(805, 159, 867, 197)
        self.image_tap(*TutorialCoord.MISSION_START)
        self.wait_image(*TutorialCoord.MISSION_START2)
        while self.search(*TutorialCoord.MISSION_START2):
            self.area_tap(359, 332, 419, 375)
        self.wait_image(*TutorialCoord.BATTLE_START)
        while not self.search(*TutorialCoord.TEAM_EDIT_OK):
            self.area_tap(887, 116, 917, 148)
        self.image_tap(*TutorialCoord.TEAM_EDIT_OK)
        self.image_tap(*TutorialCoord.BATTLE_START)
        self.image_tap(*TutorialCoord.MISSION_START2)
        while self.search(*TutorialCoord.PHASE_END):
            self.area_tap(466, 318, 540, 360)
        self.process_battle_result()
        self.image_tap(*TutorialCoord.BATTLE_RESULT_OK2)
        self.wait_image(*TutorialCoord.PHASE_END)
        while self.search(*TutorialCoord.PHASE_END):
            self.area_tap(824, 482, 929, 514)
            self.area_tap(543, 277, 588, 304)
            sleep(2)
        self.process_battle_result()
        self.image_tap(*TutorialCoord.BATTLE_RESULT_OK3)
        self.wait_image(*TutorialCoord.BATTLE_RESULT_OK4)
        while self.search(*TutorialCoord.BATTLE_RESULT_OK4):
            self.area_tap(311, 476, 454, 514)
        self.login_bonus()

    def tutorial_5(self):
        self.wait_image(*Home.MOMO_TALK)
        sleep(3)
        while not self.search(*TutorialCoord.MOMO_TALK_CLOSE):
            self.area_tap(116, 93, 129, 125)
            sleep(0.2)
        while not self.search(*TutorialCoord.YUUKA_ICON):
            self.area_tap(102, 181, 150, 230)
            sleep(0.2)
        while not self.search(*Home.MOMO_TALK):
            self.back()
            sleep(0.5)
        self.daily_mission()
        self.link_account()
        self.get_mail()

    def daily_mission(self):
        self.image_tap(*Home.MISSION)
        self.wait_image(*TutorialCoord.MISSION_MESSAGE)
        self.skip_talk()
        self.wait_image(*Home.ALL_RECEIVE)
        for _ in range(5):
            self.area_tap(*self.img_coord())
        while not self.search(*Home.MOMO_TALK):
            self.back()
            sleep(0.5)

    def link_account(self):
        while not self.search(*Home.MENU):
            self.area_tap(890, 16, 936, 38)
            sleep(0.5)
        while self.search(*Home.MENU):
            self.area_tap(490, 207, 644, 245)
            sleep(0.5)
        self.wait_image(*Home.ACCOUNT_SETTING)
        while self.search(*Home.ACCOUNT_SETTING) or self.search(*Home.MENU):
            self.area_tap(756, 175, 793, 250)
            sleep(0.5)


if __name__ == '__main__':
    self = Tutorial(emulator_connection[3]['window_name'], emulator_connection[3]['port'])
    self.run()