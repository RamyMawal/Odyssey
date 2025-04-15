import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout


class ButtonUpdater(QLabel):

    def __init__(self):
        self.count = 0
        self.label = "Not Clicked Yet!"
        super().__init__(self.label)
        self.setText(self.label)


    def updateLabel(self):
        self.count += 1
        self.label = "I was clicked {} times!".format(self.count)
        self.setText(self.label)
        


if __name__ == "__main__":


    app = QApplication(sys.argv);

    window = QWidget();
    window.setWindowTitle("Simple Test App")

    layout = QHBoxLayout()
    button = QPushButton("Click me!")
    label = ButtonUpdater()

    button.clicked.connect(lambda: label.updateLabel()) 

    layout.addWidget(label)
    layout.addWidget(button)
    window.setLayout(layout)

    window.show();

    sys.exit(app.exec())
