from PyQt6.QtWidgets import QWidget, QRubberBand, QApplication
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QPalette, QScreen

class RegionSelector(QWidget):
    # 信号：选区结束，发送 (x, y, w, h)
    selection_finished = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        # 无边框 + 顶层显示 + 工具窗口(避免任务栏图标)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.Tool)
        
        # 设置半透明黑色背景
        self.setStyleSheet("background-color: black;")
        self.setWindowOpacity(0.3) 
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        # === 核心修改：计算所有屏幕的组合区域 ===
        total_rect = QRect()
        for screen in QApplication.screens():
            total_rect = total_rect.united(screen.geometry())
        
        # 将窗口移动到组合区域的左上角，并设置大小
        self.setGeometry(total_rect)
        # ======================================

        self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.origin = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            rect = self.rubberBand.geometry()
            # 转换为屏幕绝对坐标
            global_pos = self.mapToGlobal(rect.topLeft())
            x, y, w, h = global_pos.x(), global_pos.y(), rect.width(), rect.height()
            
            # 发送坐标前做一下防抖，防止误触宽高为0
            if w > 5 and h > 5:
                self.selection_finished.emit((x, y, w, h))
            
            self.close()
            
    def keyPressEvent(self, event):
        # 允许按 ESC 取消
        if event.key() == Qt.Key.Key_Escape:
            self.close()
