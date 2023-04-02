import numpy as np

from lib.hsvfilter import HsvFilter
from control_emulator.image import WindowImage
import cv2


def init_gui():
    def nothing(pos):
        pass

    cv2.namedWindow('tool', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('tool', 350, 700)

    cv2.createTrackbar('HMin', 'tool', 0, 179, nothing)
    cv2.createTrackbar('SMin', 'tool', 0, 255, nothing)
    cv2.createTrackbar('VMin', 'tool', 0, 255, nothing)
    cv2.createTrackbar('HMax', 'tool', 0, 179, nothing)
    cv2.createTrackbar('SMax', 'tool', 0, 255, nothing)
    cv2.createTrackbar('VMax', 'tool', 0, 255, nothing)

    cv2.setTrackbarPos('HMax', 'tool', 179)
    cv2.setTrackbarPos('SMax', 'tool', 255)
    cv2.setTrackbarPos('VMax', 'tool', 255)

    cv2.createTrackbar('SAdd', 'tool', 0, 255, nothing)
    cv2.createTrackbar('SSub', 'tool', 0, 255, nothing)
    cv2.createTrackbar('VAdd', 'tool', 0, 255, nothing)
    cv2.createTrackbar('VSub', 'tool', 0, 255, nothing)

    # trackbars for edge creation
    cv2.createTrackbar('KernelSize', 'tool', 1, 30, nothing)
    cv2.createTrackbar('ErodeIter', 'tool', 1, 5, nothing)
    cv2.createTrackbar('DilateIter', 'tool', 1, 5, nothing)
    cv2.createTrackbar('Canny1', 'tool', 0, 200, nothing)
    cv2.createTrackbar('Canny2', 'tool', 0, 500, nothing)
    # Set default value for Canny trackbars
    cv2.setTrackbarPos('KernelSize', 'tool', 5)
    cv2.setTrackbarPos('Canny1', 'tool', 100)
    cv2.setTrackbarPos('Canny2', 'tool', 200)

    cv2.createTrackbar('Resize', 'tool', 1, 300, nothing)
    cv2.setTrackbarPos('Resize', 'tool', 100)

    cv2.createTrackbar('X1', 'tool', 0, 1920, nothing)
    cv2.createTrackbar('Y1', 'tool', 0, 1080, nothing)
    cv2.createTrackbar('X2', 'tool', 0, 1920, nothing)
    cv2.createTrackbar('Y2', 'tool', 0, 1080, nothing)
    cv2.setTrackbarPos('X1', 'tool', 0)
    cv2.setTrackbarPos('Y1', 'tool', 0)
    cv2.setTrackbarPos('X2', 'tool', 1920)
    cv2.setTrackbarPos('Y2', 'tool', 1080)


def get_hsv_filter():
    hsv_filter = HsvFilter()
    hsv_filter.hMin = cv2.getTrackbarPos('HMin', 'tool')
    hsv_filter.sMin = cv2.getTrackbarPos('SMin', 'tool')
    hsv_filter.vMin = cv2.getTrackbarPos('VMin', 'tool')
    hsv_filter.hMax = cv2.getTrackbarPos('HMax', 'tool')
    hsv_filter.sMax = cv2.getTrackbarPos('SMax', 'tool')
    hsv_filter.vMax = cv2.getTrackbarPos('VMax', 'tool')
    hsv_filter.sAdd = cv2.getTrackbarPos('SAdd', 'tool')
    hsv_filter.sSub = cv2.getTrackbarPos('SSub', 'tool')
    hsv_filter.vAdd = cv2.getTrackbarPos('VAdd', 'tool')
    hsv_filter.vSub = cv2.getTrackbarPos('VSub', 'tool')
    return hsv_filter


def get_edge_filter_from_controls():
    # Get current positions of all trackbars
    edge_filter = EdgeFilter()
    edge_filter.kernelSize = cv2.getTrackbarPos('KernelSize', 'tool')
    edge_filter.erodeIter = cv2.getTrackbarPos('ErodeIter', 'tool')
    edge_filter.dilateIter = cv2.getTrackbarPos('DilateIter', 'tool')
    edge_filter.canny1 = cv2.getTrackbarPos('Canny1', 'tool')
    edge_filter.canny2 = cv2.getTrackbarPos('Canny2', 'tool')
    return edge_filter


def get_resize_per():
    per = cv2.getTrackbarPos('Resize', 'tool')
    return per / 100


def get_crop_range():
    x1, y1, x2, y2 = cv2.getTrackbarPos('X1', 'tool'), cv2.getTrackbarPos('Y1', 'tool'), \
                     cv2.getTrackbarPos('X2', 'tool'), cv2.getTrackbarPos('Y2', 'tool')
    if x2 <= x1:
        x2 = x1 + 1
    elif y2 <= y1:
        y2 = y1 + 1
    return x1, y1, x2, y2


def detect_contours(image):
    def find_tip(points, convex_hull):
        length = len(points)
        indices = np.setdiff1d(range(length), convex_hull)

        for i in range(2):
            j = indices[i] + 2
            if j > length - 1:
                j = length - j
            if np.all(points[j] == points[indices[i - 1] - 2]):
                return tuple(points[j])

    before_image = image.copy()
    bgr = cv2.cvtColor(before_image, cv2.COLOR_HSV2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    contours, hierarchy = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        peri = cv2.arcLength(cnt, True)
        i = 0.001
        approx = cv2.approxPolyDP(cnt, 0.025 * peri, True)
        hull = cv2.convexHull(approx, returnPoints=False)
        sides = len(hull)

        # if 6 > sides > 3:
        # if 6 > sides > 3 and sides + 1 == len(approx):
        #     arrow_tip = find_tip(approx[:, 0, :], hull.squeeze())
        #     if arrow_tip:
        #         cv2.drawContours(before_image, [cnt], 0, (0, 255, 0), 3)
    cv2.drawContours(before_image, [approx], 0, (0, 255, 0), 0)
    return before_image


def shift_channel(c, amount):
    if amount > 0:
        lim = 255 - amount
        c[c >= lim] = 255
        c[c < lim] += amount
    elif amount < 0:
        amount = -amount
        lim = amount
        c[c <= lim] = 0
        c[c > lim] -= amount
    return c


def _apply_hsv_filter(original_image, hsv_filter=None):
    hsv = cv2.cvtColor(original_image, cv2.COLOR_BGR2HSV)

    h, s, v = cv2.split(hsv)
    if not hsv_filter:
        hsv_filter = get_hsv_filter()
    s = shift_channel(s, hsv_filter.sAdd)
    s = shift_channel(s, -hsv_filter.sSub)
    v = shift_channel(v, hsv_filter.vAdd)
    v = shift_channel(v, -hsv_filter.vSub)
    hsv = cv2.merge([h, s, v])

    lower = np.array([hsv_filter.hMin, hsv_filter.sMin, hsv_filter.vMin])
    upper = np.array([hsv_filter.hMax, hsv_filter.sMax, hsv_filter.vMax])
    mask = cv2.inRange(hsv, lower, upper)
    result = cv2.bitwise_and(hsv, hsv, mask=mask)
    bgr_img = cv2.cvtColor(result, cv2.COLOR_HSV2BGR)
    return bgr_img


if __name__ == '__main__':
    self = WindowImage()
    self.hwnd = self.get_hwnd('LDPlayer-7')

    init_gui()
    # img = cv2.imread('juren.bmp')
    while True:
        img = self.capture()
        # output_image = _apply_hsv_filter(img, HsvFilter(0, 0, 255, 0, 0, 255, 0, 0, 0, 0))
        output_image = _apply_hsv_filter(img)
        resize_per = get_resize_per()
        # output_image2 = _apply_hsv_filter(img2)
        x1, y1, x2, y2 = get_crop_range()
        output_image = output_image[y1:y2, x1:x2]
        output_image = cv2.resize(output_image, None, fx=resize_per, fy=resize_per)

        # edge_image = apply_edge_filter(output_image, edge_filter)
        # edge_image = edge_image[y1:y2, x1:x2]
        # edge_image = cv2.resize(edge_image, None, fx=resize_per, fy=resize_per)

        # detected_image = detect_contours(edge_image)
        cv2.imshow('hsv', output_image)
        # cv2.imshow('hsv2', output_image2)
        # cv2.imshow('canny', edge_image)
        # cv2.imshow('detect', detected_image)
        # print('fps: {}'.format(1 / (time() - start)))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # cv2.imwrite('{}.png'.format(time_stamp.csv()), output_image)
            break
    print('{}, {}, {}, {}, {}, {}, {}, {}, {}, {}'.format(cv2.getTrackbarPos('HMin', 'tool'),
                                                          cv2.getTrackbarPos('SMin', 'tool'),
                                                          cv2.getTrackbarPos('VMin', 'tool'),
                                                          cv2.getTrackbarPos('HMax', 'tool'),
                                                          cv2.getTrackbarPos('SMax', 'tool'),
                                                          cv2.getTrackbarPos('VMax', 'tool'),
                                                          cv2.getTrackbarPos('SAdd', 'tool'),
                                                          cv2.getTrackbarPos('SSub', 'tool'),
                                                          cv2.getTrackbarPos('VAdd', 'tool'),
                                                          cv2.getTrackbarPos('VSub', 'tool')))
