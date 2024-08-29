import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui

class WaterfallWidget(pg.PlotWidget):
    def __init__(self, sampleSize=50000, buffer_width=10000, dtype=np.float32, cmap_name='CET-L8'):
        super().__init__()
        self.sampleSize = sampleSize
        self.buffer_width = buffer_width
        self.buffer_size = buffer_width * 2
        self.dtype = dtype
        self.buffers = self._create_buffers()
        self.current_col = 0
        self.current_buffer = 1
        self.update_count = 0
        self.showGrid(x=True, y=True)
        self.cmap = pg.colormap.get(cmap_name)
        self.image_item = pg.ImageItem()
        self.addItem(self.image_item)
        self.invertY(False)
        self.color_bar = self.addColorBar(self.image_item, colorMap=self.cmap, values=(-1, 1), orientation='h', limits=(-10, 10), rounding=0.1)
        self.sigRangeChanged.connect(self.update_current_buffer)
        self.autoRange()
    def _create_buffers(self):
        return {
            1: np.zeros((self.sampleSize, self.buffer_size // 1), dtype=self.dtype),
            2: np.zeros((self.sampleSize, self.buffer_size // 2), dtype=self.dtype),
            4: np.zeros((self.sampleSize, self.buffer_size // 4), dtype=self.dtype),
            8: np.zeros((self.sampleSize, self.buffer_size // 8), dtype=self.dtype),
            16: np.zeros((self.sampleSize, self.buffer_size // 16), dtype=self.dtype),
            32: np.zeros((self.sampleSize, self.buffer_size // 32), dtype=self.dtype),
            64: np.zeros((self.sampleSize, self.buffer_size // 64), dtype=self.dtype),
            128: np.zeros((self.sampleSize, self.buffer_size // 128), dtype=self.dtype),
        }
    def update_buffer(self, level, new_data):
        buffer = self.buffers[level]
        sampleSize = buffer.shape[1]
        buffer[:, self.current_col // level] = new_data                                   # memory leaking at these lines
        buffer[:, (self.current_col // level + sampleSize // 2) % sampleSize] = new_data  # memory leaking at these lines
    def update_waterfall(self, new_data, clear_prev = False):
        if (new_data.shape[0] != self.sampleSize) or (clear_prev == True):
            self.sampleSize = new_data.shape[0]
            self.clear_waterfall()
        self.update_count += 1
        for level in self.buffers.keys():
            if self.update_count % level == 0:
                self.update_buffer(level, new_data)
        self.current_col = (self.current_col + 1) % (self.buffer_size // 2)
        self.update_visible_image()
    def clear_waterfall(self):
        self.buffers = self._create_buffers()
        self.current_col = 0
        self.current_buffer = 1
        self.update_count = 0
        self.image_item.clear()
    def update_visible_image(self):
        current_col_offset = self.current_col // self.current_buffer
        x_range, y_range = self.viewRange()
        x_min, x_max = x_range
        x_max += 1
        y_min, y_max = y_range
        y_max += 1
        x_start = max(0, int(x_min))
        x_end = min(self.buffers[self.current_buffer].shape[0], int(x_max))
        buffer_width = self.buffers[self.current_buffer].shape[1] // 2
        y_start = max(current_col_offset, int(current_col_offset + (y_min / self.current_buffer)))
        y_end = min(current_col_offset + buffer_width, int(current_col_offset + (y_max / self.current_buffer)))
        try:
            visible_data = self.buffers[self.current_buffer][x_start:x_end, y_start:y_end]
            transform = QtGui.QTransform()
            transform.translate(x_start, max(0, int(y_min)))
            transform.scale(1, self.current_buffer)
            self.image_item.setTransform(transform)
            self.image_item.setImage(visible_data, levels=(self.color_bar.levels()[0], self.color_bar.levels()[1]), autoLevels=False)
        except IndexError:
            self.image_item.clear()
    def update_current_buffer(self):
        y_range = self.viewRange()[1][1] - self.viewRange()[1][0]
        widget_height_in_pixels = self.size().height()
        pixels_per_row = widget_height_in_pixels / y_range
        
        if pixels_per_row > 2:
            self.current_buffer = 1
        elif pixels_per_row > 1:
            self.current_buffer = 2
        elif pixels_per_row > 0.5:
            self.current_buffer = 4
        elif pixels_per_row > 0.25:
            self.current_buffer = 8
        elif pixels_per_row > 0.125:
            self.current_buffer = 16
        elif pixels_per_row > 0.0625:
            self.current_buffer = 32
        elif pixels_per_row > 0.03125:
            self.current_buffer = 64
        else:
            self.current_buffer = 128
        self.update_visible_image()

# Example of use
if __name__ == "__main__":
    app = pg.mkQApp()
    waterfall_widget = WaterfallWidget()
    waterfall_widget.setGeometry(100, 100, 800, 600)
    waterfall_widget.show()

    def newSpectro():
        global data, ptr
        new_data = data[ptr % 100]
        waterfall_widget.update_waterfall(new_data)
        ptr += 1

    data = np.random.normal(size=(100, 50000))
    ptr = 0

    upd_timer = QtCore.QTimer()
    upd_timer.setInterval(50)
    upd_timer.timeout.connect(newSpectro)
    upd_timer.start()

    app.exec()
