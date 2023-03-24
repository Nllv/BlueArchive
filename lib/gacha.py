from control_emulator.control import Control
from data.coord import Gacha as GachaCoord
from lib.account_manager import AccountManager


class Gacha(Control):
    def __init__(self, window_name, serial):
        super().__init__(serial)
        self.config_init(working_folder=self.get_root_folder(),
                         window_name=window_name,
                         package_name='com.YostarJP.BlueArchive')

    def skip(self):
        self.image_tap(*GachaCoord.SKIP)

    def process_gacha_result(self):
        while True:
            if self.search(*GachaCoord.THREE_STAR):
                # pass