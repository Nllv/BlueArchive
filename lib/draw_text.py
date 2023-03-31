import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont


def cv2_putText(img, text, org, fontFace, fontScale, color, stroke_width, stroke_color, mat_pos, mat_alpha,mode=0):
    """
    画像に文字を書き加える関数(日本語化)
    :param img: 文字を書き込むイメージ
    :param text: 書き込む文字
    :param org: 座標
    :param fontFace: フォントファイルへのパス
    :param fontScale: フォントサイズ
    :param color: BGR
    :param stroke_width: 縁取りのサイズ
    :param stroke_color: 縁取りの色 RGB
    :param mat_pos: 文字乗せ用マットの座標 (x1, y1, x2, y2)
    :param mat_alpha: マットの透明度
    :param mode: 座標の基準 0:左下 1:左上 2:中央
    :return: 文字が書かれたイメージ
    """

    # 文字をのせるためのマットを作成する
    overlay = img.copy()
    mat_color = (200, 100, 100)
    fill = -1  # -1にすると塗りつぶし
    cv2.rectangle(overlay, mat_pos[0:2], mat_pos[2:4], mat_color, fill)
    img = cv2.addWeighted(overlay, mat_alpha, img, 1 - mat_alpha, 0)

    # テキスト描写域を取得
    fontPIL = ImageFont.truetype(font=fontFace, size=fontScale)
    dummy_draw = ImageDraw.Draw(Image.new("RGB", (0,0)))
    text_w, text_h = dummy_draw.textsize(text, font=fontPIL)
    text_b = int(0.1 * text_h) # バグにより下にはみ出る分の対策

    # テキスト描写域の左上座標を取得（元画像の左上を原点とする）
    x, y = org
    offset_x = [0, 0, text_w//2]
    offset_y = [text_h, 0, (text_h+text_b)//2]
    x0 = x - offset_x[mode]
    y0 = y - offset_y[mode]
    img_h, img_w = img.shape[:2]

    # 画面外なら何もしない
    if not ((-text_w < x0 < img_w) and (-text_b-text_h < y0 < img_h)) :
        print ("out of bounds")
        return img

    # テキスト描写域の中で元画像がある領域の左上と右下（元画像の左上を原点とする）
    x1, y1 = max(x0, 0), max(y0, 0)
    x2, y2 = min(x0+text_w, img_w), min(y0+text_h+text_b, img_h)

    # テキスト描写域と同サイズの黒画像を作り、それの全部もしくは一部に元画像を貼る
    text_area = np.full((text_h+text_b,text_w,3), (0,0,0), dtype=np.uint8)
    text_area[y1-y0:y2-y0, x1-x0:x2-x0] = img[y1:y2, x1:x2]

    # それをPIL化し、フォントを指定してテキストを描写する（色変換なし）
    imgPIL = Image.fromarray(text_area)
    draw = ImageDraw.Draw(imgPIL)
    draw.text(xy=(0, 0), text=text, fill=color, font=fontPIL, stroke_width=stroke_width, stroke_fill=stroke_color)

    # PIL画像をOpenCV画像に戻す（色変換なし）
    text_area = np.array(imgPIL, dtype = np.uint8)

    # 元画像の該当エリアを、文字が描写されたものに更新する
    img[y1:y2, x1:x2] = text_area[y1-y0:y2-y0, x1-x0:x2-x0]

    return img


def draw_texts(img, texts, font_scale=0.7, thickness=2, color=(0, 0, 0)):
    h, w, c = img.shape
    offset_x = 5  # 左下の座標
    initial_y = 0
    dy = int(h / 36)
    # color = (0, 0, 0)  # black

    texts = [texts] if type(texts) == str else texts

    for i, text in enumerate(texts):
        offset_y = initial_y + (i + 1) * dy
        cv2.putText(img, text, (offset_x, offset_y), cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale, color, thickness, cv2.LINE_AA)


def draw_result_on_img(img, texts, w_ratio=0.35, h_ratio=0.2, alpha=0.4, font_scale=0.8, color=(0, 0, 0)):
    # 文字をのせるためのマットを作成する
    overlay = img.copy()
    pt1 = (0, 0)
    pt2 = (int(img.shape[1] * w_ratio), int(img.shape[0] * h_ratio))

    mat_color = (200, 200, 200)
    fill = -1  # -1にすると塗りつぶし
    cv2.rectangle(overlay, pt1, pt2, mat_color, fill)

    mat_img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

    draw_texts(mat_img, texts, font_scale=font_scale, thickness=2, color=color)

    return mat_img
