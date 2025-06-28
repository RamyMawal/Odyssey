from stores.controller_context import ControllerContext

from PyQt6.QtCore import QThread


class GlobalSupervisor(QThread):
    def __init__(self, context: ControllerContext):
        super().__init__()
        self.context = context
        self._isrunning = True        
        pass

    def run(self):
        #Prepare some things
        while(self._isrunning):
            #Do the formation calculations
            pass

        

    def stop(self):
        self._isrunning = False
