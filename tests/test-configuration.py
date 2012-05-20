from gui.common import *
from gui.configuration import *
import resources

class App(Application):
    
    class Main(ConfigurationWindow):
        def init(self):
            self.resize(800,600)
            self.show()
                
app = App(sys.argv)
app.exec_()


























