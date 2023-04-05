import tkinter
import tkinter.filedialog

import numpy as np
import pyperclip
import win32gui
from PIL import Image, ImageTk
import cv2

import config.config
from control_emulator.image import WindowImage
from dev.image_pos import get_image_pos


class Model(WindowImage):
    # 画像処理前か画像処理後かを指定
    BEFORE = 1
    AFTER = 2
    
    def __init__(self):
        # config.config.window_name = 'Arknights'
        config.config.window_name = 'EleSto1'
        # config.config.window_name = 'LDPlayer-3'
        self.hwnd = self.get_hwnd('LDPlayer-3')

        # PIL画像オブジェクトを参照
        super().__init__()
        self.before_image = None
        self.after_image = None
        
        # Tkinter画像オブジェクトを参照
        self.before_image_tk = None
        self.after_image_tk = None
        
        self.file_path = None
    
    def get_image(self, type):
        """Tkinter画像オブジェクトを取得する"""
        
        if type == Model.BEFORE:
            if self.before_image is not None:
                # Tkinter画像オブジェクトに変換
                self.before_image_tk = ImageTk.PhotoImage(self.before_image)
            return self.before_image_tk
        
        elif type == Model.AFTER:
            if self.after_image is not None:
                # Tkinter画像オブジェクトに変換
                self.after_image_tk = ImageTk.PhotoImage(self.after_image)
            return self.after_image_tk
        
        else:
            return None
    
    def read(self):
        """画像の読み込みを行う"""
        
        # pathの画像を読み込んでPIL画像オブジェクト生成
        img = self.capture(debug=True)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.before_image_np = img
        self.before_image = Image.fromarray(img)
    
    def round(self, value, min, max):
        """valueをminからmaxの範囲に丸める"""
        
        ret = value
        if value < min:
            ret = min
        if value > max:
            ret = max
        
        return ret
    
    def crop(self, param, resize_per: int):
        """画像をクロップ"""
        
        if len(param) != 4:
            return
        if self.before_image is None:
            return
        if param[0] == param[2] or param[1] == param[3]:
            return
        # print(param)
        # 画像上の選択範囲を取得（x1,y1）-（x2,y2）
        x1, y1, x2, y2 = param
        
        # 画像外の選択範囲を画像内に切り詰める
        # x1 = self.round(x1, 0, self.before_image.width)
        # x2 = self.round(x2, 0, self.before_image.width)
        # y1 = self.round(y1, 0, self.before_image.height)
        # y2 = self.round(y2, 0, self.before_image.height)
        
        # x1 <= x2 になるように座標を調節
        if x1 <= x2:
            crop_x1 = x1
            crop_x2 = x2
        else:
            crop_x1 = x2
            crop_x2 = x1
        
        # y1 <= y2 になるように座標を調節
        if y1 <= y2:
            crop_y1 = y1
            crop_y2 = y2
        else:
            crop_y1 = y2
            crop_y2 = y1
        
        # PIL Imageのcropを実行
        self.after_image = self.before_image.crop(
            (
                crop_x1,
                crop_y1,
                crop_x2,
                crop_y2
            )
        )
        self.crop_pos = crop_x1, crop_y1, crop_x2, crop_y2
        img = np.asarray(self.after_image)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.after_image_np = img
        
        # リサイズ
        w, h = self.after_image_np.shape[:2]
        size = (h * resize_per, w * resize_per)
        self.after_image = cv2.resize(self.after_image_np, size)
        self.after_image = cv2.cvtColor(self.after_image, cv2.COLOR_BGR2RGB)
        self.after_image = Image.fromarray(self.after_image)
        
        self.file_path = None


class View:
    # キャンバス指定用
    LEFT_CANVAS = 1
    RIGHT_CANVAS = 2
    
    def __init__(self, app, model):
        
        self.master = app
        self.model = model

        x1, y1, x2, y2 = win32gui.GetClientRect(WindowImage.get_hwnd())
        w = x2 - x1
        h = y2 - y1

        # キャンバスのサイズ
        # left_canvas_width = 1600
        left_canvas_width = w
        # left_canvas_height = 900
        left_canvas_height = h

        right_canvas_width = 400
        right_canvas_height = 400
        
        # キャンバスとボタンを配置するフレームの作成と配置
        self.main_frame = tkinter.Frame(self.master)
        self.main_frame.pack()
        
        # ラベルを配置するフレームの作成と配置
        self.sub_frame = tkinter.Frame(self.master)
        self.sub_frame.pack(fill='x')
        
        # キャンバスを配置するフレームの作成と配置
        self.canvas_frame = tkinter.Frame(self.main_frame)
        self.canvas_frame.grid(column=1, row=1)
        
        # ボタンを配置するフレームの作成と配置
        self.button_frame = tkinter.Frame(self.main_frame)
        self.button_frame.grid(column=2, row=1)
        
        # １つ目のキャンバスの作成と配置
        self.left_canvas = tkinter.Canvas(self.canvas_frame, width=left_canvas_width,
                                          height=left_canvas_height, bg="gray")
        self.left_canvas.grid(column=1, row=1)
        
        # ２つ目のキャンバスの作成と配置
        self.right_canvas = tkinter.Canvas(self.canvas_frame, width=right_canvas_width,
                                           height=right_canvas_height, bg="gray")
        self.right_canvas.grid(column=2, row=1)
        
        # 各種ボタン
        self.capture_button = tkinter.Button(self.button_frame, text="キャプチャ")
        self.capture_button.grid(row=0, column=0)
        
        self.load_button = tkinter.Button(self.button_frame, text="画像読込")
        self.load_button.grid(row=0, column=1)
        
        self.template_match_button = tkinter.Button(self.button_frame, text="画像認識")
        self.template_match_button.grid(row=1, column=0)
        
        self.save_button = tkinter.Button(self.button_frame, text="保存")
        self.save_button.grid(row=1, column=1)
        
        # 各種スライダ
        self.threshold = tkinter.Scale(self.button_frame, label='threshold', orient='h',
                                       from_=0.0, to=1.0, length=200, resolution=0.01)
        self.threshold.set(0.9)
        self.threshold.grid(row=2, column=0, columnspan=2)
        
        self.left_slider = tkinter.Scale(self.button_frame, label='left', orient='h',
                                         from_=0, to=left_canvas_width, length=100)
        self.left_slider.grid(row=3, column=0)
        
        self.right_slider = tkinter.Scale(self.button_frame, label='right', orient='h',
                                          from_=0, to=left_canvas_width, length=100, variable=left_canvas_width)
        self.right_slider.grid(row=3, column=1)
        
        self.top_slider = tkinter.Scale(self.button_frame, label='top', orient='v',
                                        from_=0, to=left_canvas_height, length=100)
        self.top_slider.grid(row=4, column=0)
        
        self.bottom_slider = tkinter.Scale(self.button_frame, label='bottom', orient='v',
                                           from_=0, to=left_canvas_height, length=100, variable=left_canvas_height)
        self.bottom_slider.grid(row=4, column=1)

        self.resize_slider = tkinter.Scale(self.button_frame, label='リサイズ', orient='h',
                                           from_=1, to=5, length=200)
        self.resize_slider.set(3)
        self.resize_slider.grid(row=5, column=0, columnspan=2)
        
        self.log_label = tkinter.Label(master=self.button_frame, relief="flat", text='', anchor="w")
        self.log_label.grid(row=6, column=0, columnspan=2, sticky='wens')
        
        # メッセージ表示ラベルの作成と配置
        # メッセージ更新用
        self.message = tkinter.StringVar()

        self.pos_label = tkinter.Label(self.sub_frame, relief="flat", text="ここにマウスカーソル座標")
        self.pos_label.pack(side="left")
        self.message_label = tkinter.Label(self.sub_frame, textvariable=self.message, relief="flat")
        self.message_label.pack()
    
    def draw_image(self, type):
        """画像をキャンバスに描画"""
        
        # typeに応じて描画先キャンバスを決定
        if type == View.LEFT_CANVAS:
            canvas = self.left_canvas
            image = self.model.get_image(Model.BEFORE)
        elif type == View.RIGHT_CANVAS:
            canvas = self.right_canvas
            image = self.model.get_image(Model.AFTER)
        else:
            return
        
        if image is not None:
            # キャンバス上の画像の左上座標を決定
            sx = (canvas.winfo_width() - image.width()) // 2
            sy = (canvas.winfo_height() - image.height()) // 2
            
            # キャンバスに描画済みの画像を削除
            objs = canvas.find_withtag("image")
            for obj in objs:
                canvas.delete(obj)
            
            # 画像をキャンバスの真ん中に描画
            canvas.create_image(
                sx, sy,
                image=image,
                anchor=tkinter.NW,
                tag="image"
            )
    
    def draw_selection(self, selection, type):
        """選択範囲を描画"""
        
        # typeに応じて描画先キャンバスを決定
        if type == View.LEFT_CANVAS:
            canvas = self.left_canvas
        elif type == View.RIGHT_CANVAS:
            canvas = self.right_canvas
        else:
            return
        
        # 一旦描画済みの選択範囲を削除
        self.delete_selection(type)
        
        if selection:
            # 選択範囲を長方形で描画
            canvas.create_rectangle(
                selection[0],
                selection[1],
                selection[2],
                selection[3],
                outline="red",
                width=3,
                tag="selection_rectangle"
            )
    
    def delete_selection(self, type):
        """選択範囲表示用オブジェクトを削除する"""
        
        # typeに応じて描画先キャンバスを決定
        if type == View.LEFT_CANVAS:
            canvas = self.left_canvas
        elif type == View.RIGHT_CANVAS:
            canvas = self.right_canvas
        else:
            return
        
        # キャンバスに描画済みの選択範囲を削除
        objs = canvas.find_withtag("selection_rectangle")
        for obj in objs:
            canvas.delete(obj)
    
    def draw_message(self, message):
        self.message.set(message)
    

class Controller:
    INTERVAL = 50
    
    def __init__(self, app, model, view):
        self.master = app
        self.model = model
        self.view = view
        
        # マウスボタン管理用
        self.pressing = False
        self.selection = None
        
        # ラベル表示メッセージ管理用
        self.message = ""
        
        self.get_pos_str = ''
        self.set_events()

    def set_events(self):
        """受け付けるイベントを設定する"""
        
        # キャンバス上のマウス押し下げ開始イベント受付
        self.view.left_canvas.bind(
            "<ButtonPress>",
            self.button_press
        )
        
        # キャンバス上のマウス動作イベント受付
        self.view.left_canvas.bind(
            "<Motion>",
            self.mouse_motion,
        )
        
        # キャンバス上のマウス押し下げ終了イベント受付
        self.view.left_canvas.bind(
            "<ButtonRelease>",
            self.button_release,
        )

        self.view.left_canvas.bind("<Button-3>", self.get_pos)

        # ボタン押し下げイベント受付
        self.view.capture_button['command'] = self.push_capture_button
        self.view.load_button['command'] = self.load_image
        self.view.save_button['command'] = self.save_file
        self.view.template_match_button['command'] = self.template_matching
        
        # スライダーイベント設定
        self.view.left_slider['command'] = self.on_slider_crop
        self.view.right_slider['command'] = self.on_slider_crop
        self.view.top_slider['command'] = self.on_slider_crop
        self.view.bottom_slider['command'] = self.on_slider_crop
        self.view.resize_slider['command'] = self.on_slider_crop
        
        # 画像の描画用のタイマーセット
        self.master.after(Controller.INTERVAL, self.timer)
    
    def timer(self):
        """一定間隔で画像等を描画"""
        
        # 画像処理前の画像を左側のキャンバスに描画
        self.view.draw_image(
            View.LEFT_CANVAS
        )
        
        # 画像処理後の画像を右側のキャンバスに描画
        self.view.draw_image(
            View.RIGHT_CANVAS
        )
        
        # トリミング選択範囲を左側のキャンバスに描画
        self.view.draw_selection(
            self.selection,
            View.LEFT_CANVAS
        )
        
        # ラベルにメッセージを描画
        self.view.draw_message(
            self.message
        )
        
        # 再度タイマー設定
        self.master.after(Controller.INTERVAL, self.timer)

    def get_pos(self, event):
        objs = self.view.left_canvas.find_withtag("image")
        if len(objs) != 0:
            draw_coord = self.view.left_canvas.coords(objs[0])
            if self.get_pos_str.count('\n') == 2:
                self.get_pos_str = "{}, {}\n".format(int(event.x - draw_coord[0]), int(event.y - draw_coord[1]))
            else:
                self.get_pos_str += "{}, {}\n".format(int(event.x - draw_coord[0]), int(event.y - draw_coord[1]))
            self.view.log_label['text'] = self.get_pos_str
            send_str = self.get_pos_str.replace('\n', ', ')
            send_str = send_str.rstrip(', ')
            pyperclip.copy(send_str)

    def push_capture_button(self):
        """ファイル選択ボタンが押された時の処理"""
        # 画像ファイルの読み込みと描画
        self.model.read()

        x1, y1, x2, y2 = win32gui.GetClientRect(WindowImage.get_hwnd())
        w = x2 - x1
        h = y2 - y1
        self.model.crop((0, 0, w, h), 1)

        self.selection = None
        
        # 選択範囲を表示するオブジェクトを削除
        self.view.delete_selection(view.LEFT_CANVAS)
        
        # メッセージを更新
        self.message = "トリミングする範囲を指定してください"
    
    def save_file(self):
        file_path = tkinter.filedialog.asksaveasfilename(defaultextension='bmp',
                                                         filetypes=[("Bitmap", ".bmp"), ("PNG", ".png")],
                                                         initialdir="./image")
        if file_path == "":
            return
        # img = np.asarray(self.model.after_image)
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # self.model.after_image_np = img
        self.model.save_image(self.model.after_image_np, file_path)
        send_str = "'{}', {}, {}, {}, {}, {}".format('image/' + file_path.split('image/')[1],
                                                     self.model.crop_pos[0] - 10, self.model.crop_pos[1] - 10,
                                                     self.model.crop_pos[2] + 10, self.model.crop_pos[3] + 10, 0.9)
        print(send_str)
        pyperclip.copy(send_str)
        self.model.file_path = None
    
    def template_matching(self):
        threshold = self.view.threshold.get()
        if self.model.file_path:
            get_image_pos(self.model.file_path, self.model.before_image_np, threshold, is_triming=False)
        else:
            get_image_pos(self.model.after_image_np, self.model.before_image_np, threshold, is_triming=False)
    
    def load_image(self):
        file_path = tkinter.filedialog.askopenfilename(initialdir="./image")
        if file_path == "":
            return
        self.model.after_image = Image.open(file_path)
        img = np.asarray(self.model.after_image)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.model.after_image_np = img
        self.model.after_image_tk = ImageTk.PhotoImage(self.model.after_image)
        self.model.file_path = 'image/' + file_path.split('image/')[1]

    def on_slider_crop(self, args):
        param = self.view.left_slider.get(), self.view.top_slider.get(), \
                self.view.right_slider.get(), self.view.bottom_slider.get()
        self.model.crop(param, self.view.resize_slider.get())
        self.message = "{}, {}, {}, {} w:{} h:{}".format(int(param[0]), int(param[1]), int(param[2]), int(param[3]),
                                                         int(param[2] - param[0]), int(param[3] - param[1]))

    def button_press(self, event):
        """マウスボタン押し下げ開始時の処理"""
        
        # マウスクリック中に設定
        self.pressing = True
        
        self.selection = None
        
        # 現在のマウスでの選択範囲を設定
        self.selection = [
            event.x,
            event.y,
            event.x,
            event.y
        ]
        
        # 選択範囲を表示するオブジェクトを削除
        self.view.delete_selection(View.LEFT_CANVAS)
    
    def mouse_motion(self, event):
        """マウスボタン移動時の処理"""
        
        if self.pressing:
            # マウスでの選択範囲を更新
            self.selection[2] = event.x
            self.selection[3] = event.y

        objs = self.view.left_canvas.find_withtag("image")
        if len(objs) != 0:
            draw_coord = self.view.left_canvas.coords(objs[0])
            self.view.pos_label['text'] = "{}, {}".format(int(event.x - draw_coord[0]), int(event.y - draw_coord[1]))
    
    def button_release(self, event):
        """マウスボタン押し下げ終了時の処理"""
        
        if self.pressing:
            
            # マウスボタン押し下げ終了
            self.pressing = False
            
            # マウスでの選択範囲を更新
            self.selection[2] = event.x
            self.selection[3] = event.y
            
            # 画像の描画位置を取得
            objs = self.view.left_canvas.find_withtag("image")
            if len(objs) != 0:
                draw_coord = self.view.left_canvas.coords(objs[0])
                
                # 選択範囲をキャンバス上の座標から画像上の座標に変換
                x1 = self.selection[0] - draw_coord[0]
                y1 = self.selection[1] - draw_coord[1]
                x2 = self.selection[2] - draw_coord[0]
                y2 = self.selection[3] - draw_coord[1]
                
                # 画像をcropでトリミング
                self.model.crop((int(x1), int(y1), int(x2), int(y2)), self.view.resize_slider.get())
                
                # スライダーを更新
                self.view.left_slider.set(x1)
                self.view.right_slider.set(x2)
                self.view.top_slider.set(y1)
                self.view.bottom_slider.set(y2)
                
                # メッセージを更新
                self.message = "{}, {}, {}, {} w:{} h:{}".format(int(x1), int(y1), int(x2), int(y2),
                                                                 int(x2 - x1), int(y2 - y1))


if __name__ == '__main__':
    app = tkinter.Tk()
    
    # アプリのウィンドウのサイズ設定
    # app.geometry("1616x740")
    # app.title("トリミングアプリ")
    
    model = Model()
    view = View(app, model)
    controller = Controller(app, model, view)
    
    app.mainloop()
