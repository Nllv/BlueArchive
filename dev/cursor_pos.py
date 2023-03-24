from time import sleep
import pyperclip

import keyboard as keyboard
import win32api

if __name__ == '__main__':
    _list = []
    while True:
        if keyboard.read_key() == 'shift':
            x, y = win32api.GetCursorPos()
            if 4 <= len(_list):
                _list = []
            _list.append(x)
            _list.append(y)
            clip_text = ''.join([str(_) + ', ' for _ in _list])
            clip_text = clip_text.rstrip(', ')
            pyperclip.copy(clip_text)
            print(clip_text)
        if keyboard.read_key() == 'f12':
            exit()
        sleep(0.1)