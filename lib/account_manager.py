import os
import shutil

import cv2
import numpy as np
from control_emulator.image import WindowImage
from control_emulator.util import img_crop, get_save_list, time_print, fill_rect_with_black

from data.filters import HSVFilters
from lib.draw_text import cv2_putText


class AccountManager(WindowImage):
    def __init__(self, window_name=None):
        super().__init__(window_name)

        self.pulled_chara_folder = 'image/ssr/pulled_chara'
        result_img_files = os.listdir(self.pulled_chara_folder)
        result_img_files = [chara.replace('.png', '') for chara in result_img_files]
        self.result_ssr = {
            chara: self.imread(f'{self.pulled_chara_folder}/{chara}.png', is_jpn=True) for chara in result_img_files
        }

        self.have_chara_folder = 'image/ssr/have_chara'
        have_img_files = os.listdir(self.have_chara_folder)
        have_img_files = [chara.replace('.png', '') for chara in have_img_files]
        self.have_ssr = {
            chara: self.imread(f'{self.have_chara_folder}/{chara}.png', is_jpn=True) for chara in have_img_files
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

    def find_chara(self, save_number=-1, src=None):
        """
        :param save_number: -1 -> キャプチャ, 1以上の時は'gacha_result'からファイルを読み込む
        :param src: Noneでない時、このイメージを使う
        :return:
        """
        find_chara = []
        crop_range= [31, 118, 927, 532]

        if src is not None:
            img = img_crop(src, *crop_range)
        elif 0 < save_number:
            img = self.imread(f'gacha_result/{save_number}.png')
            img = img_crop(img, *crop_range)
            cnt = 1
            add_file_path = f'gacha_result/{save_number}_{cnt}.png'
            while os.path.isfile(add_file_path):
                add_img = img_crop(self.imread(add_file_path), *crop_range)
                img = cv2.vconcat([img, add_img])
                cnt += 1
                add_file_path = f'gacha_result/{save_number}_{cnt}.png'
        else:
            img = self.capture()
            img = img_crop(img, 31, 118, 927, 532)
        for ssr in self.have_ssr:
            if self.search(self.have_ssr[ssr], src=img, threshold=0.75):
                find_chara.append(ssr)
        return find_chara

    def make_data_have_chara(self):
        save_list = get_save_list()
        chara_pos = [[45 + 148 * i, 148, 176 + 148 * i, 295] for i in range(3)]
        chara_pos += [[44 + 148 * i, 148, 175 + 148 * i, 295] for i in range(3, 6)]
        chara_pos += [[45 + 148 * i, 349, 176 + 148 * i, 496] for i in range(3)]
        chara_pos += [[44 + 148 * i, 349, 175 + 148 * i, 496] for i in range(3, 6)]
        for save_number in save_list:
            time_print(save_number)
            file_path = f'gacha_result/{save_number}.png'
            if not os.path.isfile(file_path):
                continue
            img = self.imread(file_path)
            ssr_value = self.search(self.img_path_builder('three_star', 'home'),
                                    src=img, hsvfilter=HSVFilters.STAR_FOOTBAR)
            find_chara = self.find_chara(src=img)
            if ssr_value == len(find_chara):
                continue

            for index, pos in enumerate(chara_pos):
                chara_img = img_crop(img, *pos)
                if not self.search(
                        self.img_path_builder('three_star', 'home'), src=chara_img, hsvfilter=HSVFilters.STAR_FOOTBAR
                ):
                    continue
                for ssr in self.have_ssr:
                    if self.search(self.have_ssr[ssr], src=chara_img, threshold=0.8):
                        if index <= 5 and not os.path.isfile(f'image/ssr/for_thumbnail/{ssr}.png'):
                            self.jp_imwrite(
                                f'image/ssr/for_thumbnail/{ssr}.png', img_crop(img, pos[0], pos[1], pos[2], pos[3] + 28)
                            )
                        break
                else:
                    cnt = 1
                    unknown_chara_path = f'{self.have_chara_folder}/unknown_{cnt}.png'
                    while os.path.isfile(unknown_chara_path):
                        cnt += 1
                        unknown_chara_path = f'{self.have_chara_folder}/unknown_{cnt}.png'
                    cv2.imwrite(unknown_chara_path, chara_img)
                    self.have_ssr[f'unknown_{cnt}'] = chara_img
                    if index <= 5:
                        self.jp_imwrite(
                            f'image/ssr/for_thumbnail/unknown_{cnt}.png', img_crop(img, pos[0], pos[1], pos[2], pos[3] + 28)
                        )

    def create_thumbnail(self, save_number: int, row: int):
        """
        ゲームトレードのサムネイル画像を作る関数
        :param save_number: サムネイル画像を作るセーブデータ番号
        :param row: 行方向の制限
        :param column: 列方向の制限
        """
        def add_limited_text_to_img(chara_name):
            return cv2_putText(self.imread(f'image/ssr/for_thumbnail/{chara_name}.png', is_jpn=True),
                               '限　定', (22, 115), 'meiryo.ttc', 30, (0, 0, 255), 2,
                               (255, 255, 255), (0, 120, 131, 151), 0.8, 1)
        def mask_stone_and_money(_img):
            money_mask_pos = [608, 9, 673, 26]
            stone_mask_pos = [752, 9, 783, 26]
            _img = fill_rect_with_black(_img, *money_mask_pos)
            _img = fill_rect_with_black(_img, *stone_mask_pos)
            return _img

        charas = self.find_chara(save_number)
        limited_chara = ['ホシノ(水着)', 'ミカ', 'ムツキ(正月)', 'アル(正月)', 'マリー(体操服)', 'ユウカ(体操服)']
        th_chara_list = [
            add_limited_text_to_img(chara) for chara in charas if chara in limited_chara
        ]
        th_chara_list += [
            self.imread(f'image/ssr/for_thumbnail/{chara}.png', is_jpn=True)
            for chara in charas if chara not in limited_chara
        ]
        splitted_th_chara_list = [th_chara_list[i:i + row] for i in range(0, len(th_chara_list), row)]
        v_img = None
        for v in splitted_th_chara_list:
            h_img = None
            while len(v) < row:
                bg = np.zeros((175, 131, 3), np.uint8)
                bg[:] = (100, 100, 100)
                v.append(bg)
            for h in v:
                if h_img is None:
                    h_img = h
                else:
                    h_img = cv2.hconcat([h_img, h])
            if v_img is None:
                v_img = h_img
            else:
                v_img = cv2.vconcat([v_img, h_img])

        self.image_view(v_img)


        os.makedirs(f'rmt/{save_number}', exist_ok=True)
        cv2.imwrite(f'rmt/{save_number}/thumbnail.png', v_img)
        gacha_result_img = self.imread(f'gacha_result/{save_number}.png')
        gacha_result_img = mask_stone_and_money(gacha_result_img)
        cv2.imwrite(f'rmt/{save_number}/0.png', gacha_result_img)

        cnt = 1
        add_file_path = f'gacha_result/{save_number}_{cnt}.png'
        while os.path.isfile(add_file_path):
            add_img = self.imread(add_file_path)
            add_img = mask_stone_and_money(add_img)
            cv2.imwrite(f'rmt/{save_number}/{cnt}.png', add_img)
            cnt += 1
            add_file_path = f'gacha_result/{save_number}_{cnt}.png'


if __name__ == '__main__':
    self = AccountManager('LDPlayer-7')
    # self.screen_shot('gacha_result/3005.png')
    # self.make_data_have_chara()
    self.create_thumbnail(3005, 5)