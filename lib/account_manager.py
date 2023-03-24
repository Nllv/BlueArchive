import os

import cv2
from control_emulator.image import WindowImage


class AccountManager(WindowImage):
    def __init__(self, window_name=None):
        super().__init__(window_name)

        self.pulled_chara_folder = 'image/ssr/pulled_chara'
        result_img_files = os.listdir(self.pulled_chara_folder)
        result_img_files = [chara.replace('.png', '') for chara in result_img_files]
        self.result_ssr = {
            chara: self.imread(f'{self.pulled_chara_folder}/{chara}.png') for chara in result_img_files
        }

    def get_gacha_character(self):
        coord = [304, 68, 448, 244]
        get_chara_img = self.capture(*coord)
        for ssr in self.result_ssr:
            if self.search(self.result_ssr[ssr], src=get_chara_img):
                return ssr
        else:
            cnt = 1
            unknown_chara_path = f'{self.pulled_chara_folder}/unknown_{cnt}.png'
            while os.path.isfile(unknown_chara_path):
                cnt += 1
                unknown_chara_path = f'{self.pulled_chara_folder}/unknown_{cnt}.png'
            cv2.imwrite(unknown_chara_path, get_chara_img)
            return f'unknown_{cnt}'
