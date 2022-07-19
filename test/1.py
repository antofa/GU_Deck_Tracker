from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWebEngineWidgets import QWebEngineView

class WebWidget(QtWidgets.QWidget):

    def __init__(self):
        super(WebWidget, self).__init__()

        layout = QtWidgets.QHBoxLayout(self)

        title = QtWidgets.QLabel("FixedTitle:")
        # title.setText("A much larger fixed title")

        title.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, 
            QtWidgets.QSizePolicy.Fixed)

        layout.addWidget(title, 0, QtCore.Qt.AlignTop)

        v_layout = QtWidgets.QVBoxLayout()
        layout.addLayout(v_layout)

        expandingTitle = QtWidgets.QLabel("Expanding to Width Title")
        expandingTitle.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, 
            QtWidgets.QSizePolicy.Fixed)

        v_layout.addWidget(expandingTitle)

        text = QtWidgets.QTextEdit()

        view = QWebEngineView()
        view.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, 
            QtWidgets.QSizePolicy.Expanding)

        view.page().mainFrame().setScrollBarPolicy(
            QtCore.Qt.Vertical, 
            QtCore.Qt.ScrollBarAlwaysOff )

        view.page().mainFrame().setScrollBarPolicy(
            QtCore.Qt.Horizontal, 
            QtCore.Qt.ScrollBarAlwaysOff )

        v_layout.addWidget(view, 1)

        text.setPlainText("""
            this is a test which wraps to the next line\n\n\n
            bla bla bla\n\n\nthere are no vertical scroll bars here
            """)
        view.setHtml(text.toHtml())

        v_layout.addStretch()

        self.view = view
        view.page().mainFrame().contentsSizeChanged.connect(self.updateWebSize)

    def updateWebSize(self, size=None):
        if size is None:
            size = self.view.page().mainFrame().contentsSize()
        self.view.setFixedSize(size)

    def resizeEvent(self, event):
        super(WebWidget, self).resizeEvent(event)
        self.updateWebSize()


if __name__ == "__main__":

    app = QtWidgets.QApplication([])

    w = QtWidgets.QScrollArea()
    w.resize(800,600)

    web = WebWidget()
    w.setWidget(web)
    w.setWidgetResizable(True)

    w.show()

    app.exec_()