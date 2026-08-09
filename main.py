# -*- coding: utf-8 -*-
"""
Block Blast Anlık Takip Eden ve Blok Yenileyen Şeffaf Izgara Göstergesi
"""

import random
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

Window.borderless = True
Window.clearcolor = (0, 0, 0, 0)  # Arka plan tamamen şeffaf

class TransparentGridCell(Widget):
    """Görünmez, hamle olunca renklenen tekil şeffaf hücre."""
    def __init__(self, r, c, **kwargs):
        super(TransparentGridCell, self).__init__(**kwargs)
        self.row = r
        self.col = c
        
        with self.canvas:
            self.color_inst = Color(0, 0, 0, 0)
            self.rect = Rectangle(size=self.size, pos=self.pos)
            
        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def update_graphics(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def set_state(self, active, rgba=(0.1, 0.9, 0.3, 0.6)):
        self.canvas.clear()
        with self.canvas:
            if active:
                Color(*rgba)  # Yarı şeffaf yeşil vurgu
            else:
                Color(0, 0, 0, 0)  # Tamamen şeffaf / görünmez
            self.rect = Rectangle(size=self.size, pos=self.pos)


class TransparentBoardOverlay(GridLayout):
    """8x8 Tamamen Şeffaf Izgara Katmanı"""
    def __init__(self, **kwargs):
        super(TransparentBoardOverlay, self).__init__(**kwargs)
        self.cols = 8
        self.rows = 8
        self.size_hint = (None, None)
        
        screen_w, screen_h = Window.size
        board_size = min(screen_w, screen_h) * 0.85
        self.size = (board_size, board_size)
        self.pos = ((screen_w - board_size) / 2, (screen_h - board_size) / 2)
        
        self.cells = {}
        for r in range(8):
            for c in range(8):
                cell = TransparentGridCell(r, c)
                self.add_widget(cell)
                self.cells[(r, c)] = cell

    def clear_board(self):
        for cell in self.cells.values():
            cell.set_state(False)

    def show_move(self, block, start_r, start_c):
        self.clear_board()
        if not block:
            return
        b_rows = len(block)
        b_cols = len(block[0])
        
        for br in range(b_rows):
            for bc in range(b_cols):
                if block[br][bc] == 1:
                    tr = start_r + br
                    tc = start_c + bc
                    if (tr, tc) in self.cells:
                        self.cells[(tr, tc)].set_state(True)


class LiveGameSyncEngine:
    """Tahta değişimlerini ve yenilenen blokları dinamik olarak takip eden motor."""
    def __init__(self):
        self.size = 8
        # Oyun tahtası matrisi
        self.board = [[0 for _ in range(8)] for _ in range(8)]
        
        # Olası blok havuzu (Yenilenen blokları simüle etmek için)
        self.pool_blocks = [
            [[1, 1, 1]],                        # Yatay 3'lü
            [[0, 0, 1], [0, 1, 0], [1, 0, 0]],  # Çapraz
            [[1, 1], [1, 0]],                   # Sarı L
            [[1, 1], [1, 1]],                   # 2x2 Kare
            [[1], [1], [1]]                     # Dikey 3'lü
        ]
        
        # Alttaki aktif 3 slot
        self.current_tray = [random.choice(self.pool_blocks), random.choice(self.pool_blocks), random.choice(self.pool_blocks)]

    def poll_game_state(self):
        """Tahtayı ve alt slotların yenilenmesini anlık olarak kontrol eder/simüle eder."""
        # 1. Eğer alttaki 3 slot bittiyse (None olduysa) yeni bloklar yükle
        if all(slot is None for slot in self.current_tray):
            self.current_tray = [random.choice(self.pool_blocks), random.choice(self.pool_blocks), random.choice(self.pool_blocks)]
            # Slotlar yenilendiğinde tahtada da ufak bir temizlik/değişim simüle edilebilir
            
        # 2. Tahtada rastgele doluluk değişimi (oyun oynandıkça taşların konması)
        empty_cells = [(r, c) for r in range(self.size) for c in range(self.size) if self.board[r][c] == 0]
        if empty_cells and random.random() > 0.7:
            r, c = random.choice(empty_cells)
            self.board[r][c] = 1
            
        # Eğer tahta çok dolduysa simülasyon için sıfırla ki oyun kitlenmesin
        if len(empty_cells) < 10:
            self.board = [[0 for _ in range(8)] for _ in range(8)]

    def check_fit(self, block, r, c):
        b_rows = len(block)
        b_cols = len(block[0])
        if r + b_rows > self.size or c + b_cols > self.size:
            return False
        for br in range(b_rows):
            for bc in range(b_cols):
                if block[br][bc] == 1 and self.board[r + br][c + bc] == 1:
                    return False
        return True

    def get_best_move(self):
        """Mevcut tahta ve güncel slotlara göre en iyi hamleyi hesaplar."""
        self.poll_game_state()
        
        for idx, block in enumerate(self.current_tray):
            if block is None:
                continue
            b_rows = len(block)
            b_cols = len(block[0])
            for r in range(self.size - b_rows + 1):
                for c in range(self.size - b_cols + 1):
                    if self.check_fit(block, r, c):
                        # Hamle bulununca bu bloğu slotdan düşmüş gibi simüle edebiliriz
                        return block, r, c
                        
        # Hiçbiri uymuyorsa slotları yenile ve tekrar dene
        self.current_tray = [None, None, None]
        return None, 0, 0


class TransparentOverlayApp(App):
    def build(self):
        self.engine = LiveGameSyncEngine()
        self.root_layout = FloatLayout()
        
        self.grid_overlay = TransparentBoardOverlay()
        self.root_layout.add_widget(self.grid_overlay)
        
        # Sürekli arka planda tahtayı ve blokları tarayıp güncelleyen döngü (1 saniyede bir)
        Clock.schedule_interval(self.update_loop, 1.0)
        
        return self.root_layout

    def update_loop(self, dt):
        block, r, c = self.engine.get_best_move()
        if block:
            self.grid_overlay.show_move(block, r, c)
        else:
            self.grid_overlay.clear_board()


if __name__ == '__main__':
    TransparentOverlayApp().run()
