from PyQt5.QtWidgets import QWidget, QApplication, QListWidgetItem, QMessageBox
from PyQt5.uic import loadUi
from PyQt5 import QtCore
import sys
import sqlite3


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        loadUi("main.ui", self)
        self.calendarWidget.selectionChanged.connect(self.calendarDateChanged)
        self.calendarDateChanged()
        self.saveButton.clicked.connect(self.saveChanges)
        self.addButton.clicked.connect(self.addTask)
        self.deleteButton.clicked.connect(self.deleteTask)


    def calendarDateChanged(self):
        print("The Calendar Date has been changed")
        dateSelected = self.calendarWidget.selectedDate().toPyDate()
        print("Date Selected", dateSelected)
        self.updateList(dateSelected)


    def updateList(self, date):
        self.listWidget.clear()


        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        query = "SELECT task, completed FROM planner WHERE date = ?"
        row = (date,)
        results = cursor.execute(query, row).fetchall()
        for result in results:
            item = QListWidgetItem(str(result[0]))
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            if result[1] == "YES":
                item.setCheckState(QtCore.Qt.Checked)
            elif result[1] == "NO":
                item.setCheckState(QtCore.Qt.Unchecked)
            self.listWidget.addItem(item)


    def saveChanges(self):
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        date = self.calendarWidget.selectedDate().toPyDate()

        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            task = item.text()
            if item.checkState() == QtCore.Qt.Checked:
                query = "UPDATE planner SET completed = 'YES' WHERE task = ? AND date = ?"
            else:
                query = "UPDATE planner SET completed = 'NO' WHERE task = ? AND date = ?"
        
            row = (task, date,)

            cursor.execute(query, row)

        conn.commit()

        messageBox = QMessageBox()
        messageBox.setText("Changes have been saved")
        messageBox.setStandardButtons(QMessageBox.Ok)
        messageBox.exec()


    def addTask(self):
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        newTask = str(self.taskLineEdit.text())

        newStartTime = str(self.startTimeEdit.text())

        newEndTime = str(self.endTimeEdit.text())

        query = "INSERT INTO planner (task, completed, date, startTime, endTime) VALUES (?, ?, ?, ?, ?)"
        row = (newTask, "NO", self.calendarWidget.selectedDate().toPyDate(), newStartTime, newEndTime)

        cursor.execute(query, row)

        conn.commit()

        self.updateList(self.calendarWidget.selectedDate().toPyDate())

        self.taskLineEdit.setText("")


    def deleteTask(self):
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        date = str(self.calendarWidget.selectedDate().toPyDate())
        startTime = str(self.startTimeEdit.text())
        endTime = str(self.endTimeEdit.text())

        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            task = item.text()
            if item.checkState() == QtCore.Qt.Checked:
                query = "DELETE FROM planner WHERE task = ? AND date = ? AND startTime = ? AND endTime = ?"
                row = (task, date, startTime, endTime)

                cursor.execute(query, row)

        conn.commit()

        self.updateList(self.calendarWidget.selectedDate().toPyDate())




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())