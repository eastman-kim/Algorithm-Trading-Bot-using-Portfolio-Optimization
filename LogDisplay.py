from abc import *


class AbstractDisplay(metaclass=ABCMeta):
    def __init__(self, parent):
        self.parent = parent

    @abstractmethod
    def __call__(self):
        pass

    def check_account_filled(self):
        if self.parent.accountComboBox.currentText():
            return True


class LogDisplay(AbstractDisplay):
    def __call__(self):
        if self.parent.kiwoom.msg:
            self.parent.logTextEdit.append(self.parent.kiwoom.msg)
            self.parent.kiwoom.msg = ""