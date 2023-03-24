import os

import cv2
import pyperclip

from config import config
# from data.filters import HSVFilters
from control_emulator.image import WindowImage


def get_image_pos(template, src=None, threshold=0.9, luminance=False, is_triming=False, hsvfilter=None):
    os.chdir(config.working_folder)
    # temp = 'image/porker/suit/CLUB.bmp'
    # temp = 'image/porker/button/no.bmp'
    # temp = 'image/porker/number/10.bmp'
    # temp = 'image/label/hard_map.bmp'
    # temp = 'image/map/8-3.bmp'
    # temp = 'image/button/shutsugeki.bmp'
    if type(template) == str:
        img = cv2.imread(template, 0)

    im = WindowImage()
    res = im.search(template, 0, 0, 0, 0, threshold, debug=True, src=src, hsvfilter=hsvfilter)
    # res = im.search(template, *Large.SKILL_BAR, threshold=threshold, debug=True, src=src)
    print("size w:{} h:{}".format(im.w, im.h))
    print("hit = {}".format(res))
    if not res:
        return
    print("score = {}".format(max(im.score)))
    if type(template) == str:
        if res == 1:
            send_str = "'{}', {}, {}, {}, {}, {}".format(template, im.img_x - 10, im.img_y - 10, im.img_x + im.w + 10,
                                                         im.img_y + im.h + 10, threshold)
            print(send_str)
            pyperclip.copy(send_str)
        else:
            for x, y in zip(im.all_img_x, im.all_img_y):
                send_str = "'{}', {}, {}, {}, {}, {}".format(template, x - 10, y - 10, x + im.w + 10,
                                                             y + im.h + 10, threshold)
                print(send_str)
                pyperclip.copy(send_str)
    print(list(zip(im.all_img_x, im.all_img_y, im.score)))
    if luminance:
        print(im.get_luminance(im.img_x, im.img_y))
    if not is_triming:
        img = cv2.imread("ss.png")
        cv2.imshow("image", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == '__main__':
    _temp = 'image/gacha/star.bmp'
    file = 'gacha_result_tokucho/3441.bmp'
    hsvfilter = HSVFilters.GACHA_RESULT_STAR
    # file = None
    get_image_pos(_temp, threshold=0.9, luminance=False, src=file, hsvfilter=hsvfilter)
