import json
import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QDesktopWidget, QLineEdit, \
                            QSystemTrayIcon, QMenu, QAction, QTabWidget, QVBoxLayout, \
                            QPushButton, QTableWidget, QHeaderView, QMessageBox, \
                            QGridLayout, QPushButton, QTableWidgetItem, \
                            QAbstractItemView, QHBoxLayout, QLayout
from PyQt5.QtGui import QIcon, QPixmap, QDropEvent
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtCore

from pyqtkeybind import keybinder 

from task import Tasks, TaskLine
from tab1 import TAB1
from tab2 import TAB2 
from tab3 import TAB3
from menu import MENU



class WinEventFilter(QtCore.QAbstractNativeEventFilter):
    def __init__(self, keybinder):
        self.keybinder = keybinder
        super().__init__()

    def nativeEventFilter(self, eventType, message):
        ret = self.keybinder.handler(eventType, message)
        return ret, 0



class CONFIG(object):
    def __init__(self):
        self.config_file = os.path.join(os.path.expanduser('~'), '.cuc', 'config.json')
        self.default_config = {'todotxt':'todo.txt',
            'donetxt':'done.txt',
            "style":{'priority':{
                '(A)' : '#FFD700',
                '(B)' : '#FF7F50',
                '(C)' : '#3CB371',
                '(D)' : '#1E90FF'
                },
                'completion_date':'#B22222',
                'creation_date':'green',
                'content':'black',
                'project':'#e74c3c',
                'context':'#3498db',
                'keyvalue':{
                    'k':'#800080',
                    'v':'#800080'
                },
                "fontsize": 15
            },
            "layout":{'window_fixed':True,
                'window_pos': [886,403],
                'window_opacity':0.95},
            "hotkey":{
                "pin":"Shift+Ctrl+P",
                'display':'Shift+Ctrl+A'
            }
        }
        
        self.checkConfigFile()
        self.readConfigFile()
    
    def checkConfigFile(self):
        if os.path.isfile(self.config_file):
            print('config file exists')
        else:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            self.saveConfigFile(self.default_config)
            print('create default config.')
    

    def readConfigFile(self):
        with open(self.config_file, encoding='utf-8') as handle:
            self.config = json.load(handle)


    def saveConfigFile(self, config):
        with open(self.config_file, 'w', encoding='utf-8') as handle:
                json.dump(config, handle, indent=True)
        print('config saved')


    def restoreConfig(self):
        self.config = self.default_config
        self.saveConfigFile(self.config)




class App(QWidget):
    def __init__(self):
        super().__init__()
        self.left = 10
        self.top = 10
        self.width = 460
        self.height = 360
        # read configure file
        self.config = CONFIG()
        self.initUI()
        # create tasks by reading files in configure file
        tasks = Tasks()
        tasks.readFromFile(self.config.config['todotxt'])
        tasks.taskSort()
        # create done tasks list from done.txt, add status saved.
        self.doneTask = Tasks()
        self.doneTask.readFromFile(self.config.config['donetxt'], 'saved')
        # create tray icon 
        self.initTrayIcon(tasks.tasklines)
        # create tab1,  parent is APP
        self.initTab1(tasks)    
        self.initTab2()  
        self.initTab3()
        self.menu = MENU(self)
        self.initTab()
        QtGui.QFontDatabase.addApplicationFont('font/NotoColorEmoji.ttf')
        # focus on new task edit line
        self.tab1.textboxAdd.setFocus()

        # # Keep window state
        # self.settings = QtCore.QSettings("My Soft", "Cuc")
        # if not self.settings.value("geometry") == None:
        #     self.restoreGeometry(self.settings.value("geometry"))
        # if not self.settings.value("windowState") == None:
        #     self.restoreState(self.settings.value("windowState"))

        
    def initUI(self):
        # 设置窗口固定大小
        self.setFixedSize(self.width, self.height)
        # 设置窗体无边框
        if self.config.config['layout']['window_fixed']:
            self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint | QtCore.Qt.CustomizeWindowHint)
        else:
            self.setWindowTitle('Cuc')
            self.setWindowIcon(QtGui.QIcon('icons/icon1.png'))
            self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Window)
        # 设置透明背景
        self.setWindowOpacity(self.config.config['layout']['window_opacity'])
        #self.setAttribute(QtCore.Qt.WA_TranslucentBackground) # 设置窗口背景透明

        ag = QDesktopWidget().availableGeometry()    # 显示器可用的长宽信息
        print("显示器：", ag.width(), ag.height())
        self.maxwidth = ag.width()
        self.maxheight = ag.height()
        # 固定窗口位置
        self.fixedGeometry = (self.config.config['layout']['window_pos'][0], 
                        self.config.config['layout']['window_pos'][1], 
                        self.width, 
                        self.height)
        self.setGeometry(*self.fixedGeometry)
        self.show()
        self.activateWindow()



    def initTrayIcon(self, init_tasklines):
        self.tray_icon = SystemTrayIcon(init_tasklines, self)
        self.tray_icon.show()


    def initTab(self):
        # init tab 
        self.layout = QVBoxLayout()
        self.tabs = QTabWidget()       
        self.tabs.resize(458, 358)
        self.tabs.addTab(self.tab1, "TODO")
        self.tabs.addTab(self.tab2, 'DONE')
        self.tabs.addTab(self.tab3, "Summary")
        self.bottom = QHBoxLayout()
        self.pinButton = QtWidgets.QPushButton()
        self.pinButton.setToolTip('Keep window on top.')
        self.menuButton = QtWidgets.QPushButton()
        self.menuButton.setToolTip('Show preference setting window.')
        self.pinButton.setMaximumSize(30, 30)
        self.pinButton.setCheckable(True)
        self.pinButton.setChecked(True)
        self.pinButton.setIcon(QtGui.QIcon("icons/pinterest2.png"))
        self.pinButton.clicked.connect(self.winPinTop)
        self.menuButton = QtWidgets.QPushButton()
        self.menuButton.setMaximumSize(30, 30)
        self.menuButton.setChecked(True)
        self.menuButton.setIcon(QtGui.QIcon("icons/cog.png"))
        self.menuButton.clicked.connect(self.showMenu)
        self.bottom.addWidget(self.pinButton,alignment=QtCore.Qt.AlignRight)
        self.bottom.addWidget(self.menuButton)
        self.bottom.setContentsMargins(1, 1, 1, 1)

        # add tabs to widget
        self.layout.addWidget(self.tabs)
        self.layout.addLayout(self.bottom)
        self.layout.setContentsMargins(0, 1, 0, 2)
        self.setLayout(self.layout)


    # tab1 
    def initTab1(self, tasks):
        self.tab1 = TAB1(tasks, self)


    # tab2 
    def initTab2(self):
        self.tab2 = TAB2(self)
        self.tab2.doneTask = self.doneTask
        print('done tasks', len(self.tab2.doneTask.tasklines))

    
    # tab3 
    def initTab3(self):
        self.tab3 = TAB3(self)

    # hide to system tray instead of close
    def closeEvent(self, event):
        # self.settings.setValue("geometry", self.saveGeometry())
        # self.settings.setValue("windowState", self.saveState())
        print(self.settings)
        event.ignore()
        self.hide()

    # display window in the right bottom
    def rightBottomShow(self):
        if self.config.config['layout']['window_fixed']:
            self.setGeometry(*self.fixedGeometry)
        self.show()
        self.activateWindow()
        # print(self.pos())
        # focus on new task edit line
        self.tab1.textboxAdd.setFocus()

    
    # update tab1 table 
    def updateTab1Table(self, taskline=None):
        if taskline:
            self.tab1.tasks.tasklines.append(taskline)
            self.tab1.tasks.taskSort()
        self.tab1.tab1TaskTable.clear()
        self.tab1.tab1TaskTable.setRowCount(len(self.tab1.tasks.tasklines))
        self.tab1.tasks.taskSort()
        for i, t in enumerate(self.tab1.tasks.tasklines):
            cellwidget = self.tab1.createCellQlabel(i)
            self.tab1.tab1TaskTable.setCellWidget(i, 0, cellwidget)
            editButton = self.tab1.createButton('checkmark')
            deleteButton = self.tab1.createButton('delete')            
            self.tab1.tab1TaskTable.setCellWidget(i,1, editButton)
            self.tab1.tab1TaskTable.setCellWidget(i,2, deleteButton)


    # update tab2 table
    def updateTab2Table(self, insert_taskline=None):
        if insert_taskline:
            self.tab2.doneTask.tasklines.insert(0, insert_taskline)
            self.tab2.tab2TaskTable.insertRow(0)
            self.tab2.createTaskRow(insert_taskline, 0, self.tab2.tab2TaskTable)
        else:
            self.tab2.tab2TaskTable.clear()
            unsavedDoneTasks = [t for t in self.tab2.doneTask.tasklines if getattr(t, 'status', None)  != 'saved']
            self.tab2.tab2TaskTable.setRowCount(len(unsavedDoneTasks))
            for i, t in enumerate(unsavedDoneTasks):
                self.tab2.createTaskRow(t, i, self.tab2.tab2TaskTable)
    

    @QtCore.pyqtSlot()
    def winPinTop(self):
        button = self.sender()
        if button.isChecked():
            print('on top')
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            self.rightBottomShow()
        else:
            print('no top')
            self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
            self.rightBottomShow()

    
    def showMenu(self):
        if self.menu.isHidden():
            self.menu.show()
        else:
            self.menu.close()

    
    def reloadTable(self):
        #print(self.config.config)
        print('update tab1')
        self.updateTab1Table()
        print('update tab2')
        self.updateTab2Table()


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, init_tasklines, parent=None):
        '''
        init_tasklines, tasklines parsed from todo.txt, set icon
        according taskline number.
        parent is class App
        '''
        super(SystemTrayIcon, self).__init__(parent)
        # init icon by taskline number
        idx = len(init_tasklines) // 5 + 1
        if idx > 4:
            idx = 4
        icon_png = "icons/icon%s.png" % idx
        icon = QIcon(icon_png)
        QSystemTrayIcon.__init__(self, icon, parent)
        
        menu = QMenu(parent)
        showAction = menu.addAction('&Show')
        showAction.triggered.connect(self.parent().rightBottomShow)
        menu.addSeparator()
        exitAction = menu.addAction('&Exit')
        exitAction.triggered.connect(self.exit)      
        self.setContextMenu(menu)
        self.activated.connect(self.onTrayIconActivated)


    def updateIcon(self):
        idx = len(self.parent().tab1.tasks.tasklines) // 5 + 1
        if idx > 4:
            idx = 4 

        if self.parent().isHidden():
            self.setIcon(QIcon(QPixmap('icons/icon0.png')))
        elif self.parent().isVisible():
            icon_png = "icons/icon%s.png" % idx
            self.setIcon(QIcon(QPixmap(icon_png)))


    def exit(self):
        self.parent().tab1.tasks.saveToFile(self.parent().config.config['todotxt'])
        self.parent().tab2.saveDoneTask(self.parent().config.config['donetxt'])
        QtCore.QCoreApplication.exit()        


    def onTrayIconActivated(self, reason):
        #print(reason, '--reason--')
        if reason == QSystemTrayIcon.Trigger:
            #print(self.parent.frameGeometry(), self.parent.normalGeometry(), ag, sg)
            if self.parent().isHidden():
                self.parent().rightBottomShow()
                self.updateIcon()
            else:
                self.parent().hide()
                self.updateIcon()


    def shortcut(self):
        print('press shortcut')
        if self.parent().isHidden():
            self.parent().rightBottomShow()
            self.updateIcon()
        else:
            self.parent().hide()
            self.updateIcon()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    if sys.platform.startswith('win'):
        default_font = QtGui.QFont('Microsoft YaHei')
    else:
        default_font = QtGui.QFont('Arial')
    default_font.setPointSize(10)
    app.setFont(default_font)
    ex = App()
    

    # keybinder from here
    keybinder.init()
    win_event_filter = WinEventFilter(keybinder)
    event_dispatcher = QtCore.QAbstractEventDispatcher.instance()
    event_dispatcher.installNativeEventFilter(win_event_filter)
    keybinder.register_hotkey(ex.winId(), "Shift+Ctrl+A", ex.tray_icon.shortcut)
    # keybinder.register_hotkey(tab1.winId(), "Shift+Ctrl+B", tab1.testbutton)

    sys.exit(app.exec_())
    # keybinder.unregister_hotkey(ex.winId(), "Shift+Ctrl+A")


