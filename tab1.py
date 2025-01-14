from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui 
from task import TaskLine



class HiddenLabel(QtWidgets.QLabel):
    '''
    QLable hide when mouse pressed
    '''
    def __init__(self, buddy, taskline, parent = None):
        super(HiddenLabel, self).__init__(parent)
        #self.setFixedHeight(50)
        parent3 = self.parent().parent().parent()
        if isinstance(parent3, QtWidgets.QStackedWidget):
            config = parent3.widget(0).config
        else:
            config = self.parent().parent().config
        self.buddy = buddy
        self.taskline = taskline
        self.setText(self.taskline.enrich_text(config['style']))
        style_temp  = "QLabel{padding-top:0;font-family:Arial,SimHei,NotoColorEmoji;font-size:%spx}"
        self.setStyleSheet(style_temp % config['style']['fontsize'])

    # left double clicked to edit
    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.hide()
            #print('double click', self.taskline.plain_text)
            self.buddy.setText(self.taskline.plain_text)
            self.buddy.show()
            # self.buddy.setFocus()



# class HiddenButton(QtWidgets.QPushButton):
#     def __init__(self):
#         super().__init__()
#         self.op = QtWidgets.QGraphicsOpacityEffect()
#         self.op.setOpacity(0)
#         self.setGraphicsEffect(self.op)
    
#     def enterEvent(self, QEvent):
#         print('Enter')
#         time.sleep(0.25)
#         self.op.setOpacity(1)
#         self.setGraphicsEffect(self.op)
    
#     def leaveEvent(self, QEvent):
#         print('leave')
#         time.sleep(0.25)
#         self.op.setOpacity(0)
#         self.setGraphicsEffect(self.op)
        



class EditableCell(QtWidgets.QWidget):
    '''
    QLineEdit show when HiddenLabel is hidden
    '''
    def __init__(self, idx, parent = None):
        super(EditableCell, self).__init__(parent)
        self.taskline = self.parent().tasks.tasklines[idx]
        self.tab1 = self.parent()
        # Create ui
        self.myEdit = QtWidgets.QLineEdit()
        self.myEdit.hide() # Hide line edit
        self.myEdit.returnPressed.connect(self.textEdited)
        # Create our custom label, and assign myEdit as its buddy
        self.myLabel = HiddenLabel(self.myEdit, self.taskline, self) 
        
        # Put them under a layout together
        hLayout = QtWidgets.QHBoxLayout()
        hLayout.addWidget(self.myLabel)
        hLayout.addWidget(self.myEdit)
        hLayout.setContentsMargins(5, 0, 0, 0)
        self.setLayout(hLayout)


    def textEdited(self):
        # If the input is left empty, revert back to the label showing
        row = self.tab1.tab1TaskTable.indexAt(self.pos()).row()
        print('edit finished', self.myEdit.text(), ' row:', row)
        self.taskline = TaskLine()
        self.taskline.parser(self.myEdit.text())
        self.tab1.tasks.tasklines[row] = self.taskline
        print('edited plain text', self.taskline.plain_text)
        # update text after saving
        self.myLabel.setText(self.taskline.enrich_text(self.tab1.config['style']))
        self.myLabel.taskline = self.taskline
        self.myEdit.hide()
        self.myLabel.show()
        # self.myLabel.setFocus()
        self.tab1.edit_trigger.emit()



class TAB1(QtWidgets.QWidget):
    trigger = QtCore.pyqtSignal()
    check_trigger = QtCore.pyqtSignal(TaskLine)
    add_trigger = QtCore.pyqtSignal(TaskLine)
    edit_trigger = QtCore.pyqtSignal()
    def __init__(self, tasks, parent=None):
        super(TAB1, self).__init__(parent)
        self.tasks = tasks
        self.layout = QtWidgets.QGridLayout()
        self.layout.setVerticalSpacing(2)
        self.config = self.parent().config.config
        # add text edit line for new task
        self.textboxAdd = QtWidgets.QLineEdit()
        self.textboxAdd.setPlaceholderText('Input something ...')
        self.textboxAdd.setFixedHeight(25)
        self.textboxAdd.setFixedWidth(448)
        self.layout.addWidget(self.textboxAdd, 0, 0, 1, 10)
        self.textboxAdd.returnPressed.connect(self.addLine)

        # add layout for added tasks
        self.tab1TaskTable = QtWidgets.QTableWidget()
        self.tab1TaskTable.setStyleSheet("selection-background-color: #f4f6f6")
        self.tab1TaskTable.verticalHeader().setVisible(False)
        self.tab1TaskTable.horizontalHeader().setVisible(False)
        self.tab1TaskTable.setShowGrid(False)
        self.tab1TaskTable.setColumnCount(3)
        self.tab1TaskTable.setRowCount(len(self.tasks.tasklines))
        self.tab1TaskTable.setColumnWidth(0, 380)
        self.tab1TaskTable.setColumnWidth(1, 25)
        self.tab1TaskTable.setColumnWidth(2, 25)
        self.tab1TaskTable.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        self.layout.addWidget(self.tab1TaskTable, 1, 0, 15, 13)

        # signal and slot
        # update tray icon by taskline number 
        self.trigger.connect(self.parent().tray_icon.updateIcon)
        self.check_trigger.connect(self.parent().updateTab2Table)
        self.add_trigger.connect(self.parent().updateTab1Table)
        self.edit_trigger.connect(self.parent().updateTab1Table)


        # display tasks
        for i, t in enumerate(self.tasks.tasklines):
            print('init row %s' % i)
            cellwidget = self.createCellQlabel(i)
            self.tab1TaskTable.setCellWidget(i, 0, cellwidget)
            editButton = self.createButton('checkmark')
            deleteButton = self.createButton('delete')            
            self.tab1TaskTable.setCellWidget(i,1, editButton)
            self.tab1TaskTable.setCellWidget(i,2, deleteButton)
        print('init table rows ', self.tab1TaskTable.rowCount())
        self.layout.setContentsMargins(3,3,3,0)
        self.setLayout(self.layout)


    # create button in taskline
    def createButton(self, t):
        butt = QtWidgets.QPushButton()
        butt.setMaximumSize(25, 25)
        butt.setStyleSheet("QPushButton{border:1px;}")
        if t == 'delete':
            butt.setIcon(QtGui.QIcon("icons/cancel-circle.png"))      
            butt.clicked.connect(self.deleteButtonAction)     
        elif t == 'checkmark':
            butt.setIcon(QtGui.QIcon("icons/checkmark.png"))
            butt.clicked.connect(self.checkButtonAction)
        return butt


    # create editable cell
    def createCellQlabel(self, idx):
        cellwidget = EditableCell(idx, self) 
        return cellwidget       


    def addLine(self):
        #QMessageBox.information(self, "Info", "Enter Pressed.")
        print('total rows before', self.tab1TaskTable.rowCount())
        if not self.textboxAdd.text().strip():
            QtWidgets.QMessageBox.information(self, "Info", "Empty content")
        else:
            taskline = TaskLine()
            taskline.parser(self.textboxAdd.text())
            self.add_trigger.emit(taskline)
            self.trigger.emit()
            self.textboxAdd.clear()           
        print('total rows after', self.tab1TaskTable.rowCount())
        # send signal to update tray icon
        
    
    
    def checkButtonAction(self):
        button = self.sender()
        if button:
            row = self.tab1TaskTable.indexAt(button.pos()).row()
            self.checkcellwidget = self.tab1TaskTable.cellWidget(row, 0)
            completion_date = datetime.now().replace(hour=0, second=0, microsecond=0)
            self.checkcellwidget.taskline.completion_date = completion_date
            self.checkcellwidget.taskline.mask = 'x'
            print('check format text', row, self.checkcellwidget.taskline.format_text())
            print('check plain text', row, self.tasks.tasklines[row].plain_text)
            self.tab1TaskTable.removeRow(row)
            self.check_trigger.emit(self.tasks.tasklines[row])
            del self.tasks.tasklines[row]
            
    
    def deleteButtonAction(self):
        button = self.sender()
        if button:
            row = self.tab1TaskTable.indexAt(button.pos()).row()
            #column = self.tab1TaskTable.column(button)
            self.tab1TaskTable.removeRow(row)
            del self.tasks.tasklines[row]
        print('delete', row)
        # send signal to update tray icon
        self.trigger.emit()


    def testbutton(self):
        print('press testbutton')