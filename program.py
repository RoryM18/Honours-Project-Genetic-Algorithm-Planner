from PyQt5.QtWidgets import QWidget, QApplication, QListWidgetItem, QMessageBox, QInputDialog, QProgressBar, QVBoxLayout
from PyQt5.uic import loadUi
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QTimer
import sys
import sqlite3
import datetime as dateTime
import calendar
from geneticAlgorithm import geneticAlgorithm


def getAllDates(year, month):
    startDate = dateTime.date(year, month, 1)
    # Calculate the last day of the month
    last_day = calendar.monthrange(year, month)[1]
    endDate = dateTime.date(year, month, last_day)
    delta = dateTime.timedelta(days=1)

    allDates = []

    currentDate = startDate
    while currentDate <= endDate:
        allDates.append(currentDate)
        currentDate += delta

    return allDates

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        loadUi("main.ui", self)
        self.calendarWidget.selectionChanged.connect(self.calendarDateChanged)
        self.calendarDateChanged()
        self.saveButton.clicked.connect(self.saveChanges)
        self.addButton.clicked.connect(self.addTask)
        self.deleteButton.clicked.connect(self.deleteTask)
        self.priorityComboBox.addItems(["One-time event", "Occasional event", "Regular Event", "Everyday Event"])
        self.editButton.clicked.connect(self.editTask)
        self.editButton.clicked.connect(self.editTask)
        self.listWidget.itemSelectionChanged.connect(self.handleItemSelectionChanged)
        self.clearButton.clicked.connect(self.clearPlanner)
        self.optimiseButton.clicked.connect(self.optimiseSchedule)

        #Layout Setup
        self.progressBar = None
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)


    def showProgressBar(self):
        #Create and customise progress bar
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)

        #Add progress bar to layout and show it 
        self.layout.addWidget(self.progressBar)
        self.progressBar.show()

    def hideProgressBar(self):
        if self.progressBar:
            self.progressBar.hide()
            self.layout.removeWidget(self.progressBar)
            self.progressBar.deleteLater()  # Remove progress bar from memory
            self.progressBar = None  # Reset progress bar variable
    
    def updateProgressBar(self, value):
        self.progressBar.setValue(int(value))

    def optimiseSchedule(self):
        # Show progress bar
        self.showProgressBar()

        selected_date = self.calendarWidget.selectedDate().toPyDate()

        # Fetch tasks from SQLite for the specific date
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM planner WHERE date = ?", (selected_date,))
        task_data = cursor.fetchall()
        conn.close()

        tasks = [{'task_name': row[1], 'date': row[3], 'start_time': row[4], 'end_time': row[5], 'priority': row[6]} for row in task_data]

        print(f"Optimizing schedule for date: {selected_date}")

        # Run genetic algorithm for the specific date
        optimise_schedule = geneticAlgorithm(tasks, progressCallback=self.updateProgressBar)

        print(f"Optimized schedule for date {selected_date}: {optimise_schedule}")

        # Update the planner with the optimized schedule for the specific date
        self.updatePlannerWithSchedule(optimise_schedule, [selected_date])

        # Update the list widget with the tasks for the currently selected date
        self.updateList(selected_date)

        # Hide progress bar
        self.hideProgressBar()

    

    def updatePlannerWithSchedule(self, schedule, dates):
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        # Clear existing tasks for the selected dates
        for date in dates:
            cursor.execute("DELETE FROM planner WHERE date = ?", (date,))

            # Insert the optimized schedule into the planner for each date
            for task in schedule:
                query = "INSERT INTO planner (task, completed, date, startTime, endTime, priority) VALUES (?, ?, ?, ?, ?, ?)"
                row = (task.get('task_name', ''), "NO", date, task.get('start_time', ''), task.get('end_time', ''), task.get('priority', ''))
                cursor.execute(query, row)

        conn.commit()
        

    def handleItemSelectionChanged(self):
        # Enable or disable edit and delete buttons based on selection
        selected_items = self.listWidget.selectedItems()
        self.editButton.setEnabled(len(selected_items) == 1)
        self.deleteButton.setEnabled(len(selected_items) == 1)
        

    def calendarDateChanged(self):
        print("The Calendar Date has been changed")
        dateSelected = self.calendarWidget.selectedDate().toPyDate()
        print("Date Selected", dateSelected)
        self.updateList(dateSelected)


    def updateList(self, date=None):
        self.listWidget.clear()

        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        if date is not None:
            query = "SELECT task, completed, startTime, endTime, priority FROM planner WHERE date = ?"
            row = (date,)
        else:
            query = "SELECT task, completed, startTime, endTime, priority FROM planner"
            row = ()

        results = cursor.execute(query, row).fetchall()

        priority_mapping = {1: "One-time event", 2: "Occasional event", 3: "Regular Event", 4: "Everyday Event"}

        for result in results:
            task = result[0]
            completed = result[1]
            start_time = result[2]
            end_time = result[3]
            priority_value = result[4]
            priority_word = priority_mapping.get(priority_value, "Unknown")

            item = QListWidgetItem(f"{task} - {start_time} - {end_time} - Priority: {priority_word}")
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

        # Map priority values based on ComboBox selection
        priorityMapping = {"One-time event": 1, "Occasional event": 2, "Regular Event": 3, "Everyday Event": 4}
        priority = priorityMapping.get(self.priorityComboBox.currentText(), 0)

        query = "INSERT INTO planner (task, completed, date, startTime, endTime, priority) VALUES (?, ?, ?, ?, ?, ?)"
        row = (newTask, "NO", self.calendarWidget.selectedDate().toPyDate(), newStartTime, newEndTime, priority)

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

        selected_items = self.listWidget.selectedItems()
        if not selected_items:
            return

        # Assuming only one item is selected
        selected_item = selected_items[0]
        task_details = selected_item.text().split(" - ")

        # Extracting task details
        task, date, startTime, endTime = task_details[0], date, task_details[1], task_details[2]

        query = "DELETE FROM planner WHERE task = ? AND date = ? AND startTime = ? AND endTime = ?"
        row = (task, date, startTime, endTime)

        cursor.execute(query, row)
        print("Task Deleted")

        conn.commit()
        print("Changes Saved")

        messageBox = QMessageBox()
        messageBox.setText("Task has been deleteted")
        messageBox.setStandardButtons(QMessageBox.Ok)
        messageBox.exec()

        self.updateList(self.calendarWidget.selectedDate().toPyDate())


    def editTask(self):

        selected_items = self.listWidget.selectedItems()
        if not selected_items:
            return

        # Assuming only one item is selected
        selected_item = selected_items[0]
        task_details = selected_item.text().split(" - ")

        # Extracting task details
        task_name, start_time, end_time, priority = task_details[0], task_details[1], task_details[2], task_details[3].strip()

        # Ask user for new details
        new_task_name, ok = QInputDialog.getText(self, "Edit Task", "Enter new task name:", text=task_name)
        if not ok:
            return

        new_start_time, ok = QInputDialog.getText(self, "Edit Task", "Enter new start time:", text=start_time)
        if not ok:
            return

        new_end_time, ok = QInputDialog.getText(self, "Edit Task", "Enter new end time:", text=end_time)
        if not ok:
            return
        
        new_priority, ok = QInputDialog.getItem(self, "Edit Task", "Select new priority:", ["One-time event", "Occasional event", "Regular Event", "Everyday Event"], 0, False)
        if not ok:
            return

        # Update the database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        date = self.calendarWidget.selectedDate().toPyDate()

        query = "UPDATE planner SET task = ?, startTime = ?, endTime = ?, priority = ? WHERE task = ? AND date = ? AND startTime = ? AND endTime = ? AND priority = ?"
        row = (new_task_name, new_start_time, new_end_time, new_priority, task_name, date, start_time, end_time, priority)

        cursor.execute(query, row)
        conn.commit()

        # Update the list widget
        self.updateList(date)
    

    def clearPlanner(self):
        reply = QMessageBox.question(self, 'Message', 'Are you sure you want to clear the planner?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()

            query = "DELETE FROM planner"
            cursor.execute(query)
            conn.commit()

            self.updateList()

            messageBox = QMessageBox()
            messageBox.setText("Planner has been cleared")
            messageBox.setStandardButtons(QMessageBox.Ok)
            messageBox.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())