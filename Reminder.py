import sys
import os
import csv
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QMessageBox, QTextEdit, QSystemTrayIcon, QMenu, QAction, QStyle, QDialog, 
                             QComboBox, QScrollArea, QSpinBox, QTableView, QHeaderView, QFileDialog, 
                             QStyledItemDelegate, QDateEdit, QAbstractItemView, QToolTip, QTimeEdit, 
                             QCheckBox, QDesktopWidget, QShortcut)
from PyQt5.QtCore import (QTimer, Qt, QSettings, pyqtSignal, QRect, QDate, QAbstractTableModel, 
                          QModelIndex, QVariant, QEvent, QTime, QPoint, QItemSelection, QItemSelectionModel)
from PyQt5.QtGui import QFont, QColor, QIcon, QCursor, QKeySequence, QFontMetrics
import traceback
from dateutil.relativedelta import relativedelta

def get_romanian_weekday(date):
    weekdays = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică']
    return weekdays[date.weekday()]

DEFAULT_SETTINGS = {
    'x': 500,
    'y': 1,
    'width': 581,
    'height': 1155,
    'eventNameFont': 28,
    'serviceEventFont': 24,
    'dateFont': 24,
    'deadlineFont': 24,
    'csvFontSize': 14,
    'tooltipFontSize': 12,
    'commemorationTypeFont': 14,
    'visibility_index': 1,
    'service_visibility': 'Evenimente serviciu vizibile',
    'use_work_schedule': False,
    'show_commemorations': True,
    'work_schedule': {
        'Luni': {'start': '08:00', 'end': '16:00', 'day_off': False},
        'Marți': {'start': '08:00', 'end': '16:00', 'day_off': False},
        'Miercuri': {'start': '08:00', 'end': '16:00', 'day_off': False},
        'Joi': {'start': '08:00', 'end': '16:00', 'day_off': False},
        'Vineri': {'start': '08:00', 'end': '16:00', 'day_off': False},
        'Sâmbătă': {'start': '00:00', 'end': '00:00', 'day_off': True},
        'Duminică': {'start': '00:00', 'end': '00:00', 'day_off': True}
    },
    'aniversari.csv_column_widths': {
        '0': 550, '1': 150, '2': 70, '3': 150, '4': 77, '5': 150, '6': 485
    },
    'informatii.csv_column_widths': {
        '0': 373, '1': 150, '2': 70, '3': 150, '4': 100, '5': 77, '6': 150, '7': 100, '8': 334
    },
    'sarbatori.csv_column_widths': {
        '0': 373, '1': 70, '2': 100, '3': 70, '4': 77, '5': 150, '6': 150, '7': 150
    },
    'mainButtonsFontSize': 14,
    'buttonSpacing': 2,
    'buttonVerticalPadding': 5,
    'maximized': False
}

LUNI_RO = ['Ianuarie', 'Februarie', 'Martie', 'Aprilie', 'Mai', 'Iunie', 'Iulie', 'August', 'Septembrie', 'Octombrie', 'Noiembrie', 'Decembrie']
LUNI_EN = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

def convert_luna(luna):
    if luna in LUNI_EN:
        return LUNI_RO[LUNI_EN.index(luna)]
    return luna

def obtine_mesaj_eveniment(data_curenta, data_eveniment, considera_weekend):
    zile_pana_la_eveniment = (data_eveniment - data_curenta).days

    if considera_weekend:
        zile_lucratoare = sum(1 for zi in range(zile_pana_la_eveniment) 
                              if (data_curenta + timedelta(days=zi)).weekday() < 5)
        
        if zile_pana_la_eveniment == 0:
            if data_curenta.weekday() >= 5:
                return "evenimentul este astăzi, e weekend și probabil că nu mai pot fi efectuate acțiuni"
            else:
                return "evenimentul este astăzi"
        elif zile_pana_la_eveniment == 1:
            if data_curenta.weekday() == 5:  # Sâmbătă
                return "evenimentul este mâine, e weekend și probabil că nu mai pot fi efectuate acțiuni"
            else:
                return "evenimentul este mâine"
        elif data_curenta.weekday() == 4 and data_eveniment.weekday() >= 5:  # Vineri
            return "astăzi e ultima zi utilă, deoarece evenimentul pică în weekend"
        elif data_curenta.weekday() == 3 and data_eveniment.weekday() >= 5:  # Joi
            return "mai sunt două zile utile, astăzi și mâine, deoarece evenimentul pică în weekend"
        else:
            if data_eveniment.weekday() >= 5:
                return f"mai sunt {zile_lucratoare} zile lucrătoare"
            else:
                return f"mai sunt {zile_lucratoare} zile lucrătoare, cu tot cu ziua evenimentului"
    else:
        if zile_pana_la_eveniment == 0:
            return "evenimentul este astăzi"
        elif zile_pana_la_eveniment == 1:
            return "evenimentul este mâine"
        elif zile_pana_la_eveniment < 0:
            if zile_pana_la_eveniment == -1:
                return "evenimentul a fost ieri"
            elif zile_pana_la_eveniment == -2:
                return "evenimentul a fost acum două zile"
            else:
                return f"evenimentul a fost acum {abs(zile_pana_la_eveniment)} zile"
        else:
            return f"mai sunt {zile_pana_la_eveniment} zile calendaristice"

class CustomTableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._data = data
        self._headers = headers
        self._sort_column = None
        self._sort_order = Qt.AscendingOrder
        print("CustomTableModel inițializat cu succes")

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            value = self._data[index.row()][index.column()]
            if pd.isna(value):
                return ""
            if isinstance(value, (int, float)):
                return str(value)
            return value
        elif role == Qt.TextAlignmentRole:
            if index.column() == 0:
                return Qt.AlignLeft | Qt.AlignVCenter
            else:
                return Qt.AlignCenter
        
        return QVariant()

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return QVariant()

    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def sort(self, column, order):
        print(f"Sortare începută pentru coloana {column}")
        self.layoutAboutToBeChanged.emit()
        self._sort_column = column
        self._sort_order = order
        
        if self._headers[column] == 'luna':
            self._data.sort(key=lambda row: LUNI_RO.index(row[column]) if row[column] in LUNI_RO else -1,
                            reverse=(order == Qt.DescendingOrder))
        elif self._headers[column] == 'ziua':
            self._data.sort(key=lambda row: (LUNI_RO.index(row[self._headers.index('luna')]), int(row[column])),
                            reverse=(order == Qt.DescendingOrder))
        elif self._headers[column] == 'data':
            self._data.sort(key=lambda row: self.getSortKeyForDate(row[column]),
                            reverse=(order == Qt.DescendingOrder))
        else:
            self._data.sort(key=lambda row: self.getSortKey(row[column]),
                            reverse=(order == Qt.DescendingOrder))
        
        self.layoutChanged.emit()
        print(f"Sortare finalizată pentru coloana {column}")
        print(f"Primele 5 rânduri după sortare: {self._data[:5]}")

    def getSortKey(self, value):
        print(f"Obținere cheie de sortare pentru valoarea: {value}")
        if pd.isna(value) or value == '':
            return (0, '')  # Valori goale vor fi sortate la început
        if isinstance(value, str):
            if value.lower() in ['true', 'false']:
                return (1, value.lower() == 'true')
            if value in LUNI_RO:
                return (2, LUNI_RO.index(value))
            try:
                return (3, int(value))
            except ValueError:
                try:
                    return (3, float(value))
                except ValueError:
                    return (4, value.lower())
        if isinstance(value, (int, float)):
            return (3, value)
        return (4, str(value).lower())
        
    def getSortKeyForDate(self, date_string):
        try:
            date = datetime.strptime(date_string, '%d-%m-%Y')
            return (date.month, date.day, date.year)
        except ValueError:
            return (13, 32, 9999)

    def updateData(self, new_data):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()

    def insertRow(self, position, parent=QModelIndex()):
        self.beginInsertRows(parent, position, position)
        empty_row = [''] * self.columnCount()
        self._data.insert(position, empty_row)
        self.endInsertRows()
        return True

    def removeRow(self, position, parent=QModelIndex()):
        self.beginRemoveRows(parent, position, position)
        del self._data[position]
        self.endRemoveRows()
        return True

    def moveRow(self, sourceParent, sourceRow, destinationParent, destinationChild):
        self.beginMoveRows(sourceParent, sourceRow, sourceRow, destinationParent, destinationChild)
        row = self._data.pop(sourceRow)
        self._data.insert(destinationChild, row)
        self.endMoveRows()
        return True

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent, items):
        super().__init__(parent)
        self.items = items

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.items)
        editor.setStyleSheet("QComboBox { text-align: center; } QComboBox QAbstractItemView { text-align: center; }")
        editor.currentIndexChanged.connect(lambda: self.commitAndCloseEditor(editor))
        editor.installEventFilter(self)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if value in self.items:
            editor.setCurrentText(value)
        elif value:
            editor.addItem(value)
            editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, Qt.EditRole)

    def commitAndCloseEditor(self, editor):
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)

    def paint(self, painter, option, index):
        if isinstance(self.parent(), QAbstractItemView):
            self.parent().openPersistentEditor(index)
        super().paint(painter, option, index)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            return True  # Blochează evenimentele de scroll
        return super().eventFilter(obj, event)

class DateDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("dd-MM-yyyy")
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        try:
            date = QDate.fromString(value, "dd-MM-yyyy")
            if not date.isValid():
                date = QDate.fromString(value, "yyyy-MM-dd")
            if date.isValid():
                editor.setDate(date)
        except:
            print(f"Eroare la setarea datei pentru valoarea: {value}")

    def setModelData(self, editor, model, index):
        value = editor.date().toString("dd-MM-yyyy")
        model.setData(index, value, Qt.EditRole)

class CSVEditorDialog(QDialog):
    def __init__(self, csv_file, parent=None):
        super().__init__(parent)
        self.csv_file = csv_file
        self.parent = parent
        self.column_widths = {}
        self.tooltips = {}
        self.current_sort_column = -1
        self.current_sort_order = Qt.AscendingOrder
        self.initial_data = None
        self.clipboard = QApplication.clipboard()
        self.initUI()
        self.loadCSV()

    def initUI(self):
        self.setWindowTitle(f'Editare {os.path.basename(self.csv_file)}')
        
        settings = QSettings('MyCompany', 'ReminderApp')
        geometry = settings.value(f'{os.path.basename(self.csv_file)}_geometry', QRect(100, 100, 800, 600))
        self.setGeometry(geometry)

        layout = QVBoxLayout()

        self.table = QTableView()
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().sectionClicked.connect(self.onHeaderClicked)
        self.table.horizontalHeader().sectionResized.connect(self.onColumnResized)
        self.table.horizontalHeader().setMouseTracking(True)
        self.table.horizontalHeader().installEventFilter(self)
        layout.addWidget(self.table)

        buttonLayout = QHBoxLayout()
        self.addButton = QPushButton('Adaugă Rând')
        self.deleteButton = QPushButton('Șterge Rând')
        self.moveUpButton = QPushButton('Mută Rând Sus')
        self.moveDownButton = QPushButton('Mută Rând Jos')
        self.sortButton = QPushButton('Sortare Cronologică')
        
        button_font = QFont()
        button_font.setPointSize(20)
        self.addButton.setFont(button_font)
        self.deleteButton.setFont(button_font)
        self.moveUpButton.setFont(button_font)
        self.moveDownButton.setFont(button_font)
        self.sortButton.setFont(button_font)
        
        buttonLayout.addWidget(self.addButton)
        buttonLayout.addWidget(self.deleteButton)
        buttonLayout.addWidget(self.moveUpButton)
        buttonLayout.addWidget(self.moveDownButton)
        buttonLayout.addWidget(self.sortButton)

        layout.addLayout(buttonLayout)

        self.setLayout(layout)

        self.addButton.clicked.connect(self.addRow)
        self.deleteButton.clicked.connect(self.deleteRow)
        self.moveUpButton.clicked.connect(self.moveRowUp)
        self.moveDownButton.clicked.connect(self.moveRowDown)
        self.sortButton.clicked.connect(self.sortChronologically)

        font_size = self.parent.settings.get('csvFontSize', 12)
        font = QFont()
        font.setPointSize(font_size)
        self.table.setFont(font)

        QShortcut(QKeySequence.Copy, self, self.copySelection)
        QShortcut(QKeySequence.Paste, self, self.pasteSelection)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.showContextMenu)

        print("Inițializare UI completă")

    def loadCSV(self):
        print(f"Încărcare CSV: {self.csv_file}")
        try:
            if not os.path.exists(self.csv_file):
                print(f"Fișierul {self.csv_file} nu există. Se creează un fișier gol.")
                self.createEmptyCSV(self.csv_file)
            
            df = pd.read_csv(self.csv_file, encoding='utf-8')
            print(f"Date încărcate din {self.csv_file}:")
            print(df.head())
            print(f"Tipuri de date: {df.dtypes}")
            
            headers = df.columns.tolist()
            data = df.values.tolist()

            for row in data:
                for i, value in enumerate(row):
                    if isinstance(value, pd.Timestamp):
                        row[i] = value.strftime('%d-%m-%Y')
                    elif pd.isna(value):
                        row[i] = ''
                    elif isinstance(value, bool):
                        row[i] = str(value)

            if self.csv_file.endswith('sarbatori.csv'):
                for row in data:
                    luna_index = headers.index('luna')
                    row[luna_index] = convert_luna(row[luna_index])
                if 'sarbatoare_cruce_rosie' not in headers:
                    headers.append('sarbatoare_cruce_rosie')
                    for row in data:
                        row.append('')
                print("Coloane în sarbatori.csv:", headers)

            self.model = CustomTableModel(data, headers)
            self.table.setModel(self.model)

            self.column_widths = self.parent.settings.get(f'{os.path.basename(self.csv_file)}_column_widths', {})
            
            for col in range(self.model.columnCount()):
                if str(col) in self.column_widths:
                    self.table.setColumnWidth(col, self.column_widths[str(col)])
                else:
                    if headers[col] in ['serviciu', 'weekend']:
                        self.table.setColumnWidth(col, 100)
                    elif headers[col] in ['eveniment', 'observatii']:
                        self.table.setColumnWidth(col, 300)
                    else:
                        self.table.setColumnWidth(col, 150)
                
                if col == 0:
                    self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)

            self.setupDelegates(headers)
            self.initial_data = [row[:] for row in self.model._data]  # Copie profundă a datelor inițiale
            
            print("Finalizare încărcare CSV și setare delegați")
        except Exception as e:
            error_msg = f"Eroare la încărcarea {self.csv_file}: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            self.parent.log_error(error_msg)
            QMessageBox.critical(self, "Eroare", f"Nu s-a putut încărca fișierul {self.csv_file}. Se va crea un fișier gol.")
            self.createEmptyCSV(self.csv_file)

    def createEmptyCSV(self, filename):
        headers = []
        if filename == 'informatii.csv':
            headers = ['eveniment', 'data', 'avanszile', 'ciclu', 'weekend', 'rosu', 'stare', 'serviciu', 'observatii', 'data_notificare']
        elif filename == 'aniversari.csv':
            headers = ['eveniment', 'data', 'avanszile', 'ciclu', 'rosu', 'stare', 'observatii', 'data_notificare']
        elif filename == 'sarbatori.csv':
            headers = ['eveniment', 'ziua', 'luna', 'avanszile', 'rosu', 'tip', 'sarbatoare_cruce_rosie', 'observatii', 'data_notificare']
        df = pd.DataFrame(columns=headers)
        df.to_csv(filename, index=False, encoding='utf-8')

    def setupDelegates(self, headers):
        print("Începe setarea delegaților...")
        print(f"Headerele tabelului: {headers}")
        
        self.tooltips = {}
        if 'avanszile' in headers:
            self.tooltips[headers.index('avanszile')] = "Cu câte zile înainte doriți să se activeze anunțul"
        if 'rosu' in headers:
            self.tooltips[headers.index('rosu')] = "Cu câte zile înainte doriți ca anunțul activat să devină roșu"
        if 'stare' in headers:
            self.tooltips[headers.index('stare')] = "Dacă să mai apară vizibil în ciclul acesta sau nu"
        if 'serviciu' in headers:
            self.tooltips[headers.index('serviciu')] = "Dacă evenimentul este unul legat de serviciu sau nu"
        if 'weekend' in headers:
            self.tooltips[headers.index('weekend')] = "Dacă evenimentul nu poate fi rezolvat în weekend alegeți (TRUE), și invers"
        if 'observatii' in headers:
            self.tooltips[headers.index('observatii')] = "Introduceți observații suplimentare pentru acest eveniment"
        
        if 'ciclu' in headers:
            ciclu_column = headers.index('ciclu')
            ciclu_options = ['', 'lunar', 'anual'] + [f'la {i} {"luni" if i != 1 else "luna"}' for i in range(2, 12)] + [f'la {i} {"ani" if i != 1 else "an"}' for i in range(2, 11)]
            ciclu_delegate = ComboBoxDelegate(self.table, ciclu_options)
            self.table.setItemDelegateForColumn(ciclu_column, ciclu_delegate)
            print(f"Delegat setat pentru coloana Ciclu (index {ciclu_column})")
        
        for bool_column in ['weekend', 'serviciu']:
            if bool_column in headers:
                column_index = headers.index(bool_column)
                bool_delegate = ComboBoxDelegate(self.table, ['True', 'False'])
                self.table.setItemDelegateForColumn(column_index, bool_delegate)
                print(f"Delegat setat pentru coloana {bool_column} (index {column_index})")
        
        if 'stare' in headers:
            stare_column = headers.index('stare')
            stare_delegate = ComboBoxDelegate(self.table, ['pastreaza', 'indeplinit'])
            self.table.setItemDelegateForColumn(stare_column, stare_delegate)
            print(f"Delegat setat pentru coloana Stare (index {stare_column})")

        if 'data' in headers:
            data_column = headers.index('data')
            data_delegate = DateDelegate(self)
            self.table.setItemDelegateForColumn(data_column, data_delegate)
            print(f"Delegat setat pentru coloana Data (index {data_column})")

        if 'luna' in headers:
            luna_column = headers.index('luna')
            luna_delegate = ComboBoxDelegate(self.table, LUNI_RO)
            self.table.setItemDelegateForColumn(luna_column, luna_delegate)
            print(f"Delegat setat pentru coloana Luna (index {luna_column})")

        if 'tip' in headers:
            tip_column = headers.index('tip')
            tip_options = [
                '',
                'Post obișnuit',
                'Post negru',
                'Post cu dezlegare la ulei și vin',
                'Post cu dezlegare la pește',
                'Post cu dezlegare la ouă, lactate și pește',
                'Numai seara, pâine și apă',
                'Harți (dezlegare la toate)'
            ]
            tip_delegate = ComboBoxDelegate(self.table, tip_options)
            self.table.setItemDelegateForColumn(tip_column, tip_delegate)
            print(f"Delegat setat pentru coloana Tip (index {tip_column})")

        if 'sarbatoare_cruce_rosie' in headers:
            cruce_rosie_column = headers.index('sarbatoare_cruce_rosie')
            cruce_rosie_options = ['', 'sărbătoare cu cruce roșie']
            cruce_rosie_delegate = ComboBoxDelegate(self.table, cruce_rosie_options)
            self.table.setItemDelegateForColumn(cruce_rosie_column, cruce_rosie_delegate)
            print(f"Delegat setat pentru coloana Sărbătoare cu cruce roșie (index {cruce_rosie_column})")

        for col, header in enumerate(headers):
            if header not in ['ciclu', 'weekend', 'serviciu', 'stare', 'data', 'luna', 'tip', 'sarbatoare_cruce_rosie']:
                self.table.setItemDelegateForColumn(col, QStyledItemDelegate(self.table))
                print(f"Delegat implicit setat pentru coloana {header} (index {col})")

        print("Finalizarea setării delegaților")

    def addRow(self):
        print("Începe adăugarea unui rând nou")
        
        # Obținem numărul curent de rânduri, care va fi poziția noului rând
        rowPosition = self.model.rowCount()
        print(f"Poziția noului rând: {rowPosition}")

        # Creăm un nou rând gol cu numărul corect de coloane
        new_row = [''] * self.model.columnCount()
        print(f"Rând nou creat cu {len(new_row)} coloane")

        # Obținem headerele pentru a putea seta valori implicite corecte
        headers = self.model._headers
        print(f"Headerele tabelului: {headers}")

        # Setăm valori implicite pentru fiecare coloană relevantă
        if 'data' in headers:
            data_column = headers.index('data')
            new_row[data_column] = datetime.now().strftime("%d-%m-%Y")
            print(f"Data implicită setată: {new_row[data_column]}")

        if 'ziua' in headers:
            ziua_column = headers.index('ziua')
            new_row[ziua_column] = str(datetime.now().day)
            print(f"Ziua implicită setată: {new_row[ziua_column]}")

        if 'luna' in headers:
            luna_column = headers.index('luna')
            new_row[luna_column] = LUNI_RO[datetime.now().month - 1]
            print(f"Luna implicită setată: {new_row[luna_column]}")

        if 'avanszile' in headers:
            avanszile_column = headers.index('avanszile')
            new_row[avanszile_column] = '0'
            print("Avanszile implicit setat la 0")

        if 'ciclu' in headers:
            ciclu_column = headers.index('ciclu')
            new_row[ciclu_column] = ''
            print("Ciclu implicit setat la gol")

        if 'weekend' in headers:
            weekend_column = headers.index('weekend')
            new_row[weekend_column] = 'False'
            print("Weekend implicit setat la False")

        if 'rosu' in headers:
            rosu_column = headers.index('rosu')
            new_row[rosu_column] = '0'
            print("Rosu implicit setat la 0")

        if 'stare' in headers:
            stare_column = headers.index('stare')
            new_row[stare_column] = 'pastreaza'
            print("Stare implicită setată la 'pastreaza'")

        if 'serviciu' in headers:
            serviciu_column = headers.index('serviciu')
            new_row[serviciu_column] = 'False'
            print("Serviciu implicit setat la False")

        if 'observatii' in headers:
            observatii_column = headers.index('observatii')
            new_row[observatii_column] = ''
            print("Observații implicite setate la gol")

        if 'tip' in headers:
            tip_column = headers.index('tip')
            new_row[tip_column] = ''
            print("Tip implicit setat la gol")

        if 'sarbatoare_cruce_rosie' in headers:
            cruce_rosie_column = headers.index('sarbatoare_cruce_rosie')
            new_row[cruce_rosie_column] = ''
            print("Sărbătoare cu cruce roșie implicită setată la gol")

        if 'data_notificare' in headers:
            data_notificare_column = headers.index('data_notificare')
            self.tooltips[data_notificare_column] = "Data calculată automat când începe notificarea pentru acest eveniment"

        # Adăugăm noul rând la datele modelului
        self.model._data.append(new_row)
        print(f"Rând nou adăugat la datele modelului")

        # Notificăm modelul că layout-ul s-a schimbat
        self.model.layoutChanged.emit()
        print("Notificare emisă pentru schimbarea layout-ului modelului")

        print(f"Rând nou adăugat cu succes la poziția {rowPosition}")

    def deleteRow(self):
        selectedRows = set(index.row() for index in self.table.selectionModel().selectedIndexes())
        if not selectedRows:
            QMessageBox.warning(self, "Avertisment", "Vă rugăm să selectați cel puțin un rând pentru ștergere.")
            return
        
        reply = QMessageBox.question(self, 'Confirmare', 
                                     f"Sunteți sigur că doriți să ștergeți {len(selectedRows)} rând(uri)?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            for row in sorted(selectedRows, reverse=True):
                self.model.removeRow(row)
            self.model._data = [row for i, row in enumerate(self.model._data) if i not in selectedRows]
            self.model.layoutChanged.emit()
            print(f"Rânduri șterse: {selectedRows}")
        else:
            print("Ștergerea rândurilor a fost anulată de utilizator.")

    def saveCSV(self):
        print("Începe salvarea CSV...")
        headers = self.model._headers
        data = self.model._data
        
        df = pd.DataFrame(data, columns=headers)
        
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], format='%d-%m-%Y', errors='coerce')
            df['data'] = df['data'].dt.strftime('%d-%m-%Y')
        
        for bool_column in ['weekend', 'serviciu']:
            if bool_column in df.columns:
                df[bool_column] = df[bool_column].map({'True': True, 'False': False})
        
        df.to_csv(self.csv_file, index=False, encoding='utf-8')
        print(f"Date salvate în fișierul {self.csv_file}")
        QMessageBox.information(self, "Succes", "Datele au fost salvate cu succes!")

    def onColumnResized(self, column, oldWidth, newWidth):
        self.column_widths[str(column)] = newWidth
        self.parent.settings[f'{os.path.basename(self.csv_file)}_column_widths'] = self.column_widths
        self.parent.saveSettings()
        print(f"Coloana {column} redimensionată de la {oldWidth} la {newWidth}")

    def closeEvent(self, event):
        if self.isDataModified():
            reply = QMessageBox.question(self, 'Confirmare',
                "Doriți să salvați modificările înainte de a închide?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)

            if reply == QMessageBox.Yes:
                self.saveCSV()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

        if event.isAccepted():
            settings = QSettings('MyCompany', 'ReminderApp')
            settings.setValue(f'{os.path.basename(self.csv_file)}_geometry', self.geometry())
            self.parent.settings[f'{os.path.basename(self.csv_file)}_column_widths'] = self.column_widths
            self.parent.saveSettings()
        
        print("Fereastra de editare CSV închisă")

    def onHeaderClicked(self, logicalIndex):
        print(f"Header clicked pentru coloana {logicalIndex}")
        if self.current_sort_column == logicalIndex:
            self.current_sort_order = Qt.DescendingOrder if self.current_sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self.current_sort_column = logicalIndex
            self.current_sort_order = Qt.AscendingOrder
        
        print(f"Noua stare: Coloana {self.current_sort_column}, Ordine {self.current_sort_order}")
        
        self.model.sort(self.current_sort_column, self.current_sort_order)
        self.table.horizontalHeader().setSortIndicator(self.current_sort_column, self.current_sort_order)
        
        self.table.reset()
        
        print("Reapplicăm delegații după sortare")
        self.setupDelegates(self.model._headers)
        
        self.checkModelViewConsistency()

    def checkModelViewConsistency(self):
        print("Verificăm consistența între model și view:")
        for row in range(min(5, self.model.rowCount())):
            for col in range(self.model.columnCount()):
                model_data = self.model._data[row][col]
                view_data = self.table.model().data(self.table.model().index(row, col), Qt.DisplayRole)
                print(f"Rândul {row}, Coloana {col}: Model: {model_data}, View: {view_data}")
                if str(model_data) != str(view_data):
                    print(f"Atenție: Neconcordanță la rândul {row}, coloana {col}")
        print(f"Ordinea curentă de sortare a modelului: {self.model._sort_order}")

    def isDataModified(self):
        current_data = self.model._data
        if len(current_data) != len(self.initial_data):
            return True
        for current_row, initial_row in zip(current_data, self.initial_data):
            if current_row != initial_row:
                return True
        return False

    def sortChronologically(self):
        headers = self.model._headers
        data = self.model._data

        if 'data' in headers:
            date_column = headers.index('data')
            data.sort(key=lambda x: self.model.getSortKeyForDate(x[date_column]))
        elif 'ziua' in headers and 'luna' in headers:
            day_column = headers.index('ziua')
            month_column = headers.index('luna')
            data.sort(key=lambda x: (LUNI_RO.index(x[month_column]), int(x[day_column])))
        else:
            QMessageBox.warning(self, "Avertisment", "Nu s-a putut determina coloana de dată pentru sortare.")
            return

        self.model.updateData(data)
        QMessageBox.information(self, "Succes", "Datele au fost sortate cronologic.")

    def moveRowUp(self):
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()))
        if not selected_rows or selected_rows[0] == 0:
            return

        for row in selected_rows:
            self.model._data[row-1], self.model._data[row] = self.model._data[row], self.model._data[row-1]

        self.model.layoutChanged.emit()
        new_selection = QItemSelection()
        for row in selected_rows:
            new_selection.select(self.model.index(row-1, 0), self.model.index(row-1, self.model.columnCount()-1))
        self.table.selectionModel().select(new_selection, QItemSelectionModel.ClearAndSelect)
        self.table.scrollTo(self.model.index(selected_rows[0]-1, 0))

    def moveRowDown(self):
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        if not selected_rows or selected_rows[-1] == self.model.rowCount() - 1:
            return

        for row in selected_rows:
            self.model._data[row], self.model._data[row+1] = self.model._data[row+1], self.model._data[row]

        self.model.layoutChanged.emit()
        new_selection = QItemSelection()
        for row in selected_rows:
            new_selection.select(self.model.index(row+1, 0), self.model.index(row+1, self.model.columnCount()-1))
        self.table.selectionModel().select(new_selection, QItemSelectionModel.ClearAndSelect)
        self.table.scrollTo(self.model.index(selected_rows[-1]+1, 0))

    def showContextMenu(self, position):
        menu = QMenu()
        copyAction = menu.addAction("Copiază")
        pasteAction = menu.addAction("Lipește")

        action = menu.exec_(self.table.viewport().mapToGlobal(position))
        if action == copyAction:
            self.copySelection()
        elif action == pasteAction:
            self.pasteSelection()

    def copySelection(self):
        selection = self.table.selectedIndexes()
        if not selection:
            return

        rows = sorted(set(index.row() for index in selection))
        cols = sorted(set(index.column() for index in selection))

        data = []
        for row in rows:
            row_data = []
            for col in cols:
                item = self.model.data(self.model.index(row, col), Qt.DisplayRole)
                row_data.append(str(item))
            data.append('\t'.join(row_data))

        text = '\n'.join(data)
        self.clipboard.setText(text)

    def pasteSelection(self):
        selection = self.table.selectedIndexes()
        if not selection:
            return

        clipboard_text = self.clipboard.text()
        rows = clipboard_text.split('\n')
        paste_data = [row.split('\t') for row in rows]

        top_left = selection[0]
        for i, row_data in enumerate(paste_data):
            for j, value in enumerate(row_data):
                row = top_left.row() + i
                col = top_left.column() + j
                if row < self.model.rowCount() and col < self.model.columnCount():
                    self.model.setData(self.model.index(row, col), value, Qt.EditRole)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            self.copySelection()
        elif event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            self.pasteSelection()
        else:
            super().keyPressEvent(event)

    def eventFilter(self, source, event):
        if (source is self.table.horizontalHeader() and
            event.type() == QEvent.HoverMove):
            index = self.table.horizontalHeader().logicalIndexAt(event.pos())
            if index in self.tooltips:
                QToolTip.showText(self.mapToGlobal(event.pos()), self.tooltips[index])
            else:
                QToolTip.hideText()
        return super().eventFilter(source, event)

class WorkScheduleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle('Setări Program de Lucru')
        self.setGeometry(300, 300, 400, 500)
        
        self.schedule = self.parent.settings.get('work_schedule', {})
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        days = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică']
        for day in days:
            day_layout = QHBoxLayout()
            day_layout.addWidget(QLabel(day))
            
            start_time = QTimeEdit()
            end_time = QTimeEdit()
            day_off = QCheckBox('Zi liberă')

            if day in self.schedule:
                if self.schedule[day].get('day_off', False):
                    day_off.setChecked(True)
                    start_time.setEnabled(False)
                    end_time.setEnabled(False)
                else:
                    start_time.setTime(QTime.fromString(self.schedule[day]['start'], "hh:mm"))
                    end_time.setTime(QTime.fromString(self.schedule[day]['end'], "hh:mm"))
            else:
                if day in ['Sâmbătă', 'Duminică']:
                    day_off.setChecked(True)
                    start_time.setEnabled(False)
                    end_time.setEnabled(False)
                else:
                    start_time.setTime(QTime(8, 0))
                    end_time.setTime(QTime(16, 0))
            
            day_off.stateChanged.connect(lambda state, st=start_time, et=end_time: self.toggle_time_edits(state, st, et))
            
            day_layout.addWidget(start_time)
            day_layout.addWidget(end_time)
            day_layout.addWidget(day_off)
            
            scroll_layout.addLayout(day_layout)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        save_button = QPushButton('Salvează')
        save_button.clicked.connect(self.save_schedule)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def toggle_time_edits(self, state, start_time, end_time):
        start_time.setEnabled(not state)
        end_time.setEnabled(not state)

    def save_schedule(self):
        days = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică']
        new_schedule = {}
        
        for i, day in enumerate(days):
            day_layout = self.layout().itemAt(0).widget().widget().layout().itemAt(i)
            start_time = day_layout.itemAt(1).widget().time().toString("hh:mm")
            end_time = day_layout.itemAt(2).widget().time().toString("hh:mm")
            day_off = day_layout.itemAt(3).widget().isChecked()
            
            new_schedule[day] = {
                'start': start_time,
                'end': end_time,
                'day_off': day_off
            }
        
        self.parent.settings['work_schedule'] = new_schedule
        self.parent.saveSettings()
        self.close()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle('Setări')
        self.setGeometry(300, 300, 500, 500)
        
        layout = QVBoxLayout()
        
        self.checkButton = QPushButton('Verifică Evenimente și Aniversări')
        self.checkButton.setFont(QFont('Arial', 14))
        self.checkButton.clicked.connect(parent.checkEvents)
        layout.addWidget(self.checkButton)

        self.visibilityComboBox = QComboBox()
        self.visibilityComboBox.addItems(['Afișează toate evenimentele', 'Ascunde evenimente îndeplinite'])
        self.visibilityComboBox.setFont(QFont('Arial', 14))
        self.visibilityComboBox.currentIndexChanged.connect(self.onVisibilityChanged)
        layout.addWidget(self.visibilityComboBox)

        layout.addWidget(QLabel('Setări Fonturi:'))

        self.eventNameFont = self.createFontSetting('Nume Eveniment:', parent.settings.get('eventNameFont', 30))
        layout.addLayout(self.eventNameFont)

        self.serviceEventFont = self.createFontSetting('Eveniment de Serviciu:', parent.settings.get('serviceEventFont', 24))
        layout.addLayout(self.serviceEventFont)

        self.dateFont = self.createFontSetting('Data Limită:', parent.settings.get('dateFont', 24))
        layout.addLayout(self.dateFont)

        self.deadlineFont = self.createFontSetting('Termen Limită:', parent.settings.get('deadlineFont', 24))
        layout.addLayout(self.deadlineFont)

        self.csvFont = self.createFontSetting('Font Tabele CSV:', parent.settings.get('csvFontSize', 14))
        layout.addLayout(self.csvFont)

        self.tooltipFont = self.createFontSetting('Font Tooltip:', parent.settings.get('tooltipFontSize', 12))
        layout.addLayout(self.tooltipFont)

        self.commemorationTypeFont = self.createFontSetting('Font Tip Sărbătoare:', parent.settings.get('commemorationTypeFont', 22))
        layout.addLayout(self.commemorationTypeFont)

        self.mainButtonsFont = self.createFontSetting('Font Butoane Principale:', parent.settings.get('mainButtonsFontSize', 14))
        layout.addLayout(self.mainButtonsFont)

        self.buttonSpacing = self.createSpacingSetting('Spațiu între butoane:', parent.settings.get('buttonSpacing', 2))
        layout.addLayout(self.buttonSpacing)

        self.buttonVerticalPadding = self.createSpacingSetting('Spațiu vertical buton:', parent.settings.get('buttonVerticalPadding', 5))
        layout.addLayout(self.buttonVerticalPadding)

        self.useWorkScheduleCheckBox = QCheckBox('Utilizează program de lucru')
        self.useWorkScheduleCheckBox.setChecked(self.parent.settings.get('use_work_schedule', False))
        self.useWorkScheduleCheckBox.stateChanged.connect(self.onUseWorkScheduleChanged)
        layout.addWidget(self.useWorkScheduleCheckBox)

        self.workScheduleButton = QPushButton('Setări Program de Lucru')
        self.workScheduleButton.clicked.connect(self.openWorkSchedule)
        layout.addWidget(self.workScheduleButton)

        self.showHolidaysCheckBox = QCheckBox('Afișează Sărbători')
        self.showHolidaysCheckBox.setChecked(self.parent.settings.get('show_commemorations', False))
        self.showHolidaysCheckBox.stateChanged.connect(self.onShowHolidaysChanged)
        layout.addWidget(self.showHolidaysCheckBox)

        self.saveButton = QPushButton('Salvează Setările')
        self.saveButton.clicked.connect(self.saveSettings)
        layout.addWidget(self.saveButton)
        
        self.setLayout(layout)

    def createFontSetting(self, label, defaultSize):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        spinBox = QSpinBox()
        spinBox.setRange(8, 72)
        spinBox.setValue(defaultSize)
        layout.addWidget(spinBox)
        return layout

    def createSpacingSetting(self, label, defaultValue):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        spinBox = QSpinBox()
        spinBox.setRange(0, 20)
        spinBox.setValue(defaultValue)
        layout.addWidget(spinBox)
        return layout

    def onVisibilityChanged(self, index):
        print(f"Schimbare index vizibilitate: {index}")
        self.parent.settings['visibility_index'] = index
        self.parent.checkEvents()

    def onUseWorkScheduleChanged(self, state):
        print(f"Schimbare stare Utilizează program de lucru: {state}")
        self.parent.settings['use_work_schedule'] = (state == Qt.Checked)
        self.parent.updateServiceVisibilityState()
        self.parent.checkEvents()

    def openWorkSchedule(self):
        dialog = WorkScheduleDialog(self.parent)
        dialog.exec_()

    def onShowHolidaysChanged(self, state):
        self.parent.settings['show_commemorations'] = (state == Qt.Checked)
        self.parent.saveSettings()
        self.parent.checkEvents()

    def saveSettings(self):
        print("Salvare setări")
        self.parent.settings['eventNameFont'] = self.eventNameFont.itemAt(1).widget().value()
        self.parent.settings['serviceEventFont'] = self.serviceEventFont.itemAt(1).widget().value()
        self.parent.settings['dateFont'] = self.dateFont.itemAt(1).widget().value()
        self.parent.settings['deadlineFont'] = self.deadlineFont.itemAt(1).widget().value()
        self.parent.settings['csvFontSize'] = self.csvFont.itemAt(1).widget().value()
        self.parent.settings['tooltipFontSize'] = self.tooltipFont.itemAt(1).widget().value()
        self.parent.settings['commemorationTypeFont'] = self.commemorationTypeFont.itemAt(1).widget().value()
        self.parent.settings['mainButtonsFontSize'] = self.mainButtonsFont.itemAt(1).widget().value()
        self.parent.settings['buttonSpacing'] = self.buttonSpacing.itemAt(1).widget().value()
        self.parent.settings['buttonVerticalPadding'] = self.buttonVerticalPadding.itemAt(1).widget().value()
        self.parent.settings['visibility_index'] = self.visibilityComboBox.currentIndex()
        self.parent.settings['use_work_schedule'] = self.useWorkScheduleCheckBox.isChecked()
        self.parent.settings['show_commemorations'] = self.showHolidaysCheckBox.isChecked()
        self.parent.saveSettings()
        self.parent.updateServiceVisibilityState()
        self.parent.checkEvents()
        self.parent.set_tooltip_style(self.parent.settings['tooltipFontSize'])
        self.parent.updateHolidaysButtonVisibility()
        self.parent.updateMainButtonsFont(self.parent.settings['mainButtonsFontSize'])
        self.parent.adjustAllButtonHeights()
        self.close()
        print("Setări salvate și aplicate")

class ReminderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.is_initial_startup = True
        self.settings = {}
        self.serviceVisibilityButton = None
        self.tray_icon = None
        self.openHolidaysButton = None
        self.mainButtonsFont = None
        self.openEventsButton = None
        self.openAnniversariesButton = None
        self.settingsButton = None
        QTimer.singleShot(1000, self.delayedInit)
        print(f"După __init__ - Poziție: X={self.pos().x()}, Y={self.pos().y()}")

    def moveEvent(self, event):
        super().moveEvent(event)
        # Prevenim pozițiile Y negative și logăm încercări de poziționare negativă
        if self.pos().y() < 0:
            print(f"Încercare de poziționare negativă detectată: X={self.pos().x()}, Y={self.pos().y()}")
            print(f"Dimensiune decorațiuni fereastră: {self.frameGeometry().height() - self.geometry().height()}")
            self.move(self.pos().x(), 1)

    def delayedInit(self):
        try:
            print(f"Început delayedInit - Poziție: X={self.pos().x()}, Y={self.pos().y()}")
            self.loadSettings()
            print(f"După loadSettings - Poziție: X={self.pos().x()}, Y={self.pos().y()}")
            
            self.createEmptyCSVIfNotExists()
            print(f"Înainte de initUI - Poziție: X={self.pos().x()}, Y={self.pos().y()}")
            self.initUI()
            print(f"După initUI - Poziție: X={self.pos().x()}, Y={self.pos().y()}")
            
            # Verificăm și geometria ferestrei
            frameGeom = self.frameGeometry()
            print(f"Detalii fereastră:")
            print(f"Geometrie cadru - X={frameGeom.x()}, Y={frameGeom.y()}, Height={frameGeom.height()}")
            print(f"Dimensiune cadru decorațiuni: {self.frameGeometry().height() - self.geometry().height()}")
            print(f"Înălțime totală disponibilă ecran: {QDesktopWidget().availableGeometry().height()}")
            
            self.loadData()
            self.updateServiceVisibilityState()
            self.set_tooltip_style(self.settings.get('tooltipFontSize', 12))
            self.checkEvents()
            
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.checkEvents)
            self.timer.start(21600000)
            
            self.setupTrayIcon()
            print(f"Înainte de restoreWindowState - Poziție: X={self.pos().x()}, Y={self.pos().y()}")
            self.restoreWindowState()
            print(f"După restoreWindowState - Poziție: X={self.pos().x()}, Y={self.pos().y()}")
            
            self.show()
            print(f"După show - Poziție: X={self.pos().x()}, Y={self.pos().y()}")
            
            print("ReminderApp inițializat cu succes")
        except Exception as e:
            error_msg = f"Eroare în inițializarea ReminderApp: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            self.log_error(error_msg)
            QMessageBox.critical(self, "Eroare de Inițializare", f"Eroare în inițializarea ReminderApp: {str(e)}\nVerificați error_log.txt pentru detalii.")

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # Logăm poziția doar când utilizatorul termină de mutat fereastra
        print(f"Poziție după mutare: X={self.pos().x()}, Y={self.pos().y()}")            

    def log_error(self, error_msg):
        try:
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'error_log.txt')
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now()}: {error_msg}\n\n")
        except Exception as e:
            print(f"Eroare la scrierea în fișierul de log: {e}")
            QMessageBox.warning(self, "Avertisment", f"Nu s-a putut scrie în fișierul de log: {e}")

    def createEmptyCSVIfNotExists(self):
        csv_files = ['informatii.csv', 'aniversari.csv', 'sarbatori.csv']
        for file in csv_files:
            if not os.path.exists(file):
                self.createEmptyCSV(file)

    def createEmptyCSV(self, filename):
        headers = []
        if filename == 'informatii.csv':
            headers = ['eveniment', 'data', 'avanszile', 'ciclu', 'weekend', 'rosu', 'stare', 'serviciu', 'observatii']
        elif filename == 'aniversari.csv':
            headers = ['eveniment', 'data', 'avanszile', 'ciclu', 'rosu', 'stare', 'observatii']
        elif filename == 'sarbatori.csv':
            headers = ['eveniment', 'ziua', 'luna', 'avanszile', 'rosu', 'tip', 'sarbatoare_cruce_rosie', 'observatii']
        df = pd.DataFrame(columns=headers)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Fișier CSV gol creat: {filename}")

    def initUI(self):
        print("Inițializare UI ReminderApp")
        self.setWindowTitle('Program de Reamintire Evenimente și Aniversări')
        
        # Obținem înălțimea decorațiunilor ferestrei
        decoration_height = self.frameGeometry().height() - self.geometry().height()
        
        # Setăm geometria inițială luând în considerare decorațiunile
        self.setGeometry(
            self.settings.get('x', 300),
            max(decoration_height, 1),  # Folosim cel puțin înălțimea decorațiunilor
            self.settings.get('width', 900),
            self.settings.get('height', 700)
        )
        self.setWindowFlags(self.windowFlags() | Qt.Tool)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(self.settings.get('buttonSpacing', 2))

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollContents = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollContents)
        self.scrollArea.setWidget(self.scrollContents)
        layout.addWidget(self.scrollArea)

        self.mainButtonsFont = QFont('Arial', self.settings.get('mainButtonsFontSize', 14))

        self.openEventsButton = self.createMainButton('Deschide Fișier Evenimente', lambda: self.openCSVEditor('informatii.csv'))
        layout.addWidget(self.openEventsButton)

        self.openAnniversariesButton = self.createMainButton('Deschide Fișier Aniversări', lambda: self.openCSVEditor('aniversari.csv'))
        layout.addWidget(self.openAnniversariesButton)

        self.openHolidaysButton = self.createMainButton('Deschide Fișier Sărbători', lambda: self.openCSVEditor('sarbatori.csv'))
        layout.addWidget(self.openHolidaysButton)

        self.serviceVisibilityButton = self.createMainButton('Evenimente serviciu vizibile', self.toggleServiceVisibility)
        layout.addWidget(self.serviceVisibilityButton)

        self.settingsButton = self.createMainButton('Setări', self.openSettings)
        layout.addWidget(self.settingsButton)

        name_label = QLabel('Mereu Mihai')
        name_label.setFont(QFont('Arial', 12))
        name_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        layout.addWidget(name_label)

        self.setLayout(layout)
        self.updateHolidaysButtonVisibility()
        print("UI ReminderApp inițializat")

    def createMainButton(self, text, onClickFunction):
        button = QPushButton(text)
        button.setFont(self.mainButtonsFont)
        button.clicked.connect(onClickFunction)
        self.adjustButtonHeight(button)
        return button

    def adjustButtonHeight(self, button):
        font_metrics = QFontMetrics(button.font())
        text_height = font_metrics.height()
        vertical_padding = self.settings.get('buttonVerticalPadding', 5)
        button_height = text_height + (vertical_padding * 2)
        button.setFixedHeight(button_height)
        button.setStyleSheet(f"QPushButton {{ padding-top: {vertical_padding}px; padding-bottom: {vertical_padding}px; }}")

    def adjustAllButtonHeights(self):
        for button in [self.openEventsButton, self.openAnniversariesButton, self.openHolidaysButton, 
                       self.serviceVisibilityButton, self.settingsButton]:
            if button:
                self.adjustButtonHeight(button)

    def updateMainButtonsFont(self, font_size):
        self.mainButtonsFont = QFont('Arial', font_size)
        for button in [self.openEventsButton, self.openAnniversariesButton, self.openHolidaysButton, 
                       self.serviceVisibilityButton, self.settingsButton]:
            if button:
                button.setFont(self.mainButtonsFont)
                self.adjustButtonHeight(button)
        
        main_layout = self.layout()
        if isinstance(main_layout, QVBoxLayout):
            main_layout.setSpacing(self.settings.get('buttonSpacing', 2))

    def loadSettings(self):
        print("Încărcare setări")
        try:
            with open('window_settings.json', 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
            # Forțăm Y să fie 1, indiferent de valoarea salvată
            self.settings['y'] = 1
            print("Setări încărcate cu succes")
        except (FileNotFoundError, json.JSONDecodeError):
            print("Nu s-au găsit setări sau fișierul este corupt. Se folosesc setările implicite.")
            self.settings = DEFAULT_SETTINGS.copy()
        
        # Asigurăm-ne că avem setarea pentru commemorationTypeFont
        self.settings['commemorationTypeFont'] = self.settings.get('commemorationTypeFont', 14)

    def saveSettings(self):
        print("Salvare setări")
        self.settings.update({
            'x': self.pos().x(),
            'y': 1,  # Forțăm salvarea lui Y ca 1
            'width': self.width(),
            'height': self.height(),
            'maximized': self.isMaximized(),
            'service_visibility': self.serviceVisibilityButton.text() if self.serviceVisibilityButton else 'Evenimente serviciu vizibile'
        })
        with open('window_settings.json', 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=4)
        print("Setări salvate cu succes")

    def restoreWindowState(self):
        # Obținem înălțimea decorațiunilor ferestrei (bara de titlu + margini)
        decoration_height = self.frameGeometry().height() - self.geometry().height()
        
        # Ajustăm poziția Y pentru a compensa decorațiunile
        desired_y = max(decoration_height, self.settings.get('y', 1))
        
        self.setGeometry(
            self.settings.get('x', 300),
            desired_y,  # Folosim poziția Y ajustată
            self.settings.get('width', 900),
            self.settings.get('height', 700)
        )
        
        if self.settings.get('maximized', False):
            self.showMaximized()

    def saveWindowState(self):
        self.settings['x'] = self.pos().x()
        self.settings['y'] = self.pos().y()
        self.settings['width'] = self.width()
        self.settings['height'] = self.height()
        self.settings['maximized'] = self.isMaximized()
        self.saveSettings()

    def openSettings(self):
        print("Deschidere dialog setări")
        settingsDialog = SettingsDialog(self)
        settingsDialog.visibilityComboBox.setCurrentIndex(self.settings.get('visibility_index', 0))
        settingsDialog.exec_()

    def loadData(self):
        print("Încărcare date")
        self.loadCSV('informatii.csv')
        self.loadCSV('aniversari.csv')
        self.loadCSV('sarbatori.csv')

    def loadCSV(self, filename):
        print(f"Încărcare CSV: {filename}")
        try:
            if not os.path.exists(filename):
                self.createEmptyCSV(filename)
                return
            
            df = pd.read_csv(filename, encoding='utf-8')
            
            if filename != 'sarbatori.csv' and 'data' in df.columns:
                # Convertim data în format corect și salvăm înapoi în CSV
                df['data'] = pd.to_datetime(df['data'], format='%d-%m-%Y', errors='coerce')
                df['data'] = df['data'].dt.strftime('%d-%m-%Y')
                df.to_csv(filename, index=False, encoding='utf-8')
            
            if 'ciclu' in df.columns:
                df['ciclu'] = df['ciclu'].fillna('').astype(str)
            
            for col in ['weekend', 'serviciu']:
                if col in df.columns:
                    df[col] = df[col].fillna(False).astype(bool)
            
            if 'avanszile' in df.columns:
                df['avanszile'] = df['avanszile'].fillna(0).astype(int)

            if 'rosu' in df.columns:
                df['rosu'] = df['rosu'].fillna(0).astype(int)
            
            if 'stare' in df.columns:
                df['stare'] = df['stare'].fillna('pastreaza').astype(str)
            
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Date procesate și salvate în {filename}")
        except Exception as e:
            error_msg = f"Eroare la încărcarea {filename}: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            self.log_error(error_msg)
            self.createEmptyCSV(filename)

    def openCSVEditor(self, filename):
        print(f"Deschidere editor CSV pentru {filename}")
        file_path = os.path.join(os.getcwd(), filename)
        if os.path.exists(file_path):
            editor = CSVEditorDialog(file_path, self)
            editor.exec_()
            self.loadData()
            self.checkEvents()
        else:
            QMessageBox.warning(self, 'Eroare', f'Fișierul {filename} nu a fost găsit.')

    def updateServiceVisibilityState(self):
        print("Actualizare stare vizibilitate evenimente de serviciu")
        if self.settings.get('use_work_schedule', True):
            current_time = QTime.currentTime()
            current_day = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică'][datetime.now().weekday()]
            work_schedule = self.settings.get('work_schedule', {})
            
            is_work_time = False
            if current_day in work_schedule:
                if not work_schedule[current_day].get('day_off', False):
                    start_time = QTime.fromString(work_schedule[current_day]['start'], "hh:mm")
                    end_time = QTime.fromString(work_schedule[current_day]['end'], "hh:mm")
                    is_work_time = start_time <= current_time <= end_time
            
            if is_work_time:
                self.serviceVisibilityButton.setText('Evenimente serviciu vizibile')
                self.settings['service_visibility'] = 'Evenimente serviciu vizibile'
            else:
                self.serviceVisibilityButton.setText('Evenimente serviciu ascunse')
                self.settings['service_visibility'] = 'Evenimente serviciu ascunse'
        else:
            # Dacă programul de lucru nu este utilizat, păstrăm ultima stare cunoscută
            self.serviceVisibilityButton.setText(self.settings.get('service_visibility', 'Evenimente serviciu vizibile'))
        
        print(f"Stare actualizată: {self.settings['service_visibility']}")
        self.saveSettings()

    def toggleServiceVisibility(self):
        print("Comutare vizibilitate evenimente de serviciu")
        if self.serviceVisibilityButton.text() == 'Evenimente serviciu vizibile':
            self.serviceVisibilityButton.setText('Evenimente serviciu ascunse')
            self.settings['service_visibility'] = 'Evenimente serviciu ascunse'
        else:
            self.serviceVisibilityButton.setText('Evenimente serviciu vizibile')
            self.settings['service_visibility'] = 'Evenimente serviciu vizibile'
        self.saveSettings()
        self.checkEvents()
        print(f"Stare actualizată: {self.settings['service_visibility']}")

    def checkEvents(self):
        print("Verificare evenimente")
        try:
            moment_curent = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            evenimente_de_notificat = []
            aniversari_de_notificat = []
            sarbatori_de_notificat = []

            print(f"Verificare evenimente pentru data: {moment_curent}")

            arata_ascunse = self.settings.get('visibility_index', 0) == 0
            arata_serviciu = self.settings['service_visibility'] == 'Evenimente serviciu vizibile'
            arata_sarbatori = self.settings.get('show_commemorations', True)
            
            # Procesare evenimente din informatii.csv
            tabel_evenimente = pd.read_csv('informatii.csv')
            tabel_evenimente['data'] = pd.to_datetime(tabel_evenimente['data'], format='%d-%m-%Y', errors='coerce')
            tabel_evenimente = tabel_evenimente.sort_values('data')

            for index, eveniment in tabel_evenimente.iterrows():
                try:
                    data_eveniment = self.adjust_date_custom(eveniment['data'], moment_curent, str(eveniment['ciclu']))
                    
                    if pd.notnull(data_eveniment) and eveniment['ciclu'] and eveniment['stare'] == 'indeplinit':
                        data_originala = eveniment['data']
                        if data_eveniment.date() != data_originala.date():
                            tabel_evenimente.loc[index, 'stare'] = 'pastreaza'
                            tabel_evenimente['data'] = tabel_evenimente['data'].dt.strftime('%d-%m-%Y')
                            tabel_evenimente.to_csv('informatii.csv', index=False)
                    
                    if pd.notnull(data_eveniment):
                        # Calculăm data de notificare și o salvăm
                        data_notificare = self.calculate_notification_date(data_eveniment, eveniment['avanszile'])
                        tabel_evenimente.loc[index, 'data_notificare'] = data_notificare
                        
                        zile_pana_la_eveniment = (data_eveniment - moment_curent).days
                        este_in_perioada_notificare = zile_pana_la_eveniment <= eveniment['avanszile']
                        este_rosu = zile_pana_la_eveniment <= eveniment['rosu'] and eveniment['rosu'] > 0
                        
                        if (arata_serviciu or not eveniment['serviciu']) and (arata_ascunse or eveniment['stare'] != 'indeplinit'):
                            if este_in_perioada_notificare:
                                zile_weekend = self.count_weekend_days(moment_curent, data_eveniment) if eveniment['weekend'] else 0
                                zile_lucratoare = max(0, zile_pana_la_eveniment + 1 - zile_weekend)
                                evenimente_de_notificat.append((
                                    eveniment['eveniment'],
                                    data_eveniment,
                                    zile_pana_la_eveniment,
                                    zile_lucratoare,
                                    zile_weekend,
                                    eveniment['weekend'],
                                    este_rosu,
                                    index,
                                    'event',
                                    eveniment['ciclu'],
                                    eveniment['serviciu'],
                                    eveniment['observatii']
                                ))
                except Exception as e:
                    print(f"Eroare la procesarea evenimentului: {str(e)}")

            # Salvăm tabelul cu datele de notificare actualizate
            tabel_evenimente['data'] = tabel_evenimente['data'].dt.strftime('%d-%m-%Y')
            tabel_evenimente.to_csv('informatii.csv', index=False)

            # Procesare aniversări din aniversari.csv
            tabel_aniversari = pd.read_csv('aniversari.csv', parse_dates=['data'], date_format='%d-%m-%Y')
            tabel_aniversari = tabel_aniversari.sort_values('data')

            for index, aniversare in tabel_aniversari.iterrows():
                try:
                    data_nastere = aniversare['data']
                    urmatoarea_aniversare = data_nastere.replace(year=moment_curent.year)
                    if urmatoarea_aniversare < moment_curent:
                        urmatoarea_aniversare = urmatoarea_aniversare.replace(year=moment_curent.year + 1)
                    
                    # Calculăm și salvăm data de notificare pentru aniversare
                    data_notificare = self.calculate_notification_date(urmatoarea_aniversare, aniversare['avanszile'])
                    tabel_aniversari.loc[index, 'data_notificare'] = data_notificare
                    
                    zile_pana_la_aniversare = (urmatoarea_aniversare - moment_curent).days
                    este_in_perioada_notificare = zile_pana_la_aniversare <= aniversare['avanszile']
                    este_rosu = zile_pana_la_aniversare <= aniversare.get('rosu', 0) and aniversare.get('rosu', 0) > 0
                    
                    if arata_ascunse or aniversare['stare'] != 'indeplinit':
                        if este_in_perioada_notificare:
                            varsta = urmatoarea_aniversare.year - data_nastere.year
                            aniversari_de_notificat.append((
                                aniversare['eveniment'],
                                urmatoarea_aniversare,
                                zile_pana_la_aniversare,
                                varsta,
                                este_rosu,
                                index,
                                'anniversary',
                                aniversare.get('observatii', '')
                            ))
                            print(f"Aniversare de notificat: {aniversare['eveniment']}, Data: {urmatoarea_aniversare.strftime('%d-%m-%Y')}, Zile până la aniversare: {zile_pana_la_aniversare}, Vârsta: {varsta}, Este roșu: {este_rosu}")
                except Exception as e:
                    print(f"Eroare la procesarea aniversării: {str(e)}")

            # Salvăm tabelul aniversărilor cu datele de notificare actualizate
            tabel_aniversari['data'] = tabel_aniversari['data'].dt.strftime('%d-%m-%Y')
            tabel_aniversari.to_csv('aniversari.csv', index=False)

            # Procesare sărbători din sarbatori.csv
            if arata_sarbatori:
                print("Procesare sărbători:")
                tabel_sarbatori = pd.read_csv('sarbatori.csv')
                tabel_sarbatori = tabel_sarbatori.sort_values(['luna', 'ziua'])

                for index, sarbatoare in tabel_sarbatori.iterrows():
                    try:
                        index_luna = LUNI_RO.index(sarbatoare['luna']) + 1
                        data_sarbatoare = datetime(moment_curent.year, index_luna, sarbatoare['ziua'])
                        if data_sarbatoare < moment_curent:
                            data_sarbatoare = data_sarbatoare.replace(year=moment_curent.year + 1)
                        
                        # Calculăm și salvăm data de notificare pentru sărbătoare
                        data_notificare = self.calculate_notification_date(data_sarbatoare, sarbatoare['avanszile'])
                        tabel_sarbatori.loc[index, 'data_notificare'] = data_notificare
                        
                        zile_pana_la_sarbatoare = (data_sarbatoare - moment_curent).days
                        este_in_perioada_notificare = zile_pana_la_sarbatoare <= sarbatoare['avanszile']
                        este_rosu = zile_pana_la_sarbatoare <= sarbatoare.get('rosu', 0) and sarbatoare.get('rosu', 0) > 0
                        
                        if este_in_perioada_notificare:
                            sarbatori_de_notificat.append((
                                sarbatoare['eveniment'],
                                data_sarbatoare,
                                zile_pana_la_sarbatoare,
                                este_rosu,
                                index,
                                'holiday',
                                sarbatoare['tip'],
                                sarbatoare['sarbatoare_cruce_rosie'],
                                sarbatoare.get('observatii', '')
                            ))
                            print(f"Sărbătoare de notificat: {sarbatoare['eveniment']}, Data: {data_sarbatoare.strftime('%d-%m-%Y')}, Zile până la sărbătoare: {zile_pana_la_sarbatoare}, Este roșu: {este_rosu}, Tip: {sarbatoare['tip']}, Sărbătoare cu cruce roșie: {sarbatoare['sarbatoare_cruce_rosie']}")
                    except Exception as e:
                        print(f"Eroare la procesarea sărbătorii: {str(e)}")
                        print(f"Rând problematic: {sarbatoare}")

                # Salvăm tabelul sărbătorilor cu datele de notificare actualizate
                tabel_sarbatori.to_csv('sarbatori.csv', index=False)
            else:
                print("Afișarea sărbătorilor este dezactivată.")

            toate_notificarile = sarbatori_de_notificat + evenimente_de_notificat + aniversari_de_notificat
            toate_notificarile.sort(key=lambda x: x[1])

            if toate_notificarile:
                self.showNotification(toate_notificarile)
            else:
                self.clearNotifications()
                eticheta = QLabel('Niciun eveniment, aniversare sau sărbătoare de notificat')
                eticheta.setFont(QFont('Arial', 18))
                eticheta.setAlignment(Qt.AlignCenter)
                self.scrollLayout.addWidget(eticheta)

            return True

        except Exception as e:
            mesaj_eroare = f"Eroare în checkEvents: {str(e)}\n{traceback.format_exc()}"
            print(mesaj_eroare)
            self.log_error(mesaj_eroare)
            return False

    def adjust_date_custom(self, event_date, now, ciclu):
        print(f"Ajustare dată: event_date={event_date}, now={now}, ciclu={ciclu}")
        if pd.isna(ciclu) or ciclu == '' or not isinstance(ciclu, str):
            return event_date
        
        try:
            if pd.isna(event_date):
                return event_date
                
            if not isinstance(event_date, datetime):
                try:
                    event_date = pd.to_datetime(event_date)
                except:
                    return event_date
            
            if ciclu == 'lunar':
                while event_date <= now:
                    event_date = event_date + relativedelta(months=1)
            elif ciclu == 'anual':
                while event_date <= now:
                    event_date = event_date + relativedelta(years=1)
            elif ciclu.startswith('la '):
                parts = ciclu.split()
                if len(parts) == 3:
                    number = int(parts[1])
                    unit = parts[2]
                    while event_date <= now:
                        if unit in ['ani', 'an']:
                            event_date = event_date + relativedelta(years=number)
                        elif unit in ['luni', 'luna']:
                            event_date = event_date + relativedelta(months=number)
            
            return event_date
        except Exception as e:
            print(f"Eroare la ajustarea datei pentru ciclul '{ciclu}': {str(e)}")
            return event_date

    def calculate_notification_date(self, event_date, avanszile):
        """
        Calculează data la care ar trebui să înceapă notificarea pentru un eveniment.
        """
        if isinstance(event_date, str):
            event_date = datetime.strptime(event_date, '%d-%m-%Y')
        return (event_date - timedelta(days=avanszile)).strftime('%d-%m-%Y')

    def count_weekend_days(self, start_date, end_date):
        weekend_days = sum(1 for day in pd.date_range(start_date, end_date) if day.dayofweek >= 5)
        print(f"Zile de weekend între {start_date} și {end_date}: {weekend_days}")
        return weekend_days

    def get_holiday_time_text(self, days_until_holiday):
        if days_until_holiday == 0:
            return "azi"
        elif days_until_holiday == 1:
            return "mâine"
        elif days_until_holiday == 2:
            return "peste două zile"
        else:
            return f"peste {days_until_holiday} zile"

    def showNotification(self, notifications):
        print(f"Afișare notificări: {len(notifications)} notificări")
        self.clearNotifications()

        zile_romanesti = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică']
        luni_romanesti = ['ianuarie', 'februarie', 'martie', 'aprilie', 'mai', 'iunie', 'iulie', 'august', 'septembrie', 'octombrie', 'noiembrie', 'decembrie']

        for notification in notifications:
            try:
                if len(notification) > 8 and notification[8] == 'event':  # Eveniment obișnuit
                    event, date, days_until_event, workdays, weekend_days, consider_weekend, is_red, index, _, ciclu, is_service, observatii = notification
                    event_label = QLabel()
                
                    event_text = f"<span style='font-size: {self.settings['eventNameFont']}px;'><b>{event}</b></span><br>"
                    if is_service:
                        event_text += f"<span style='color: blue; font-size: {self.settings['serviceEventFont']}px;'>[Eveniment de serviciu]</span><br>"
                    event_text += f"<span style='font-size: {self.settings['dateFont']}px;'>Data limită: {zile_romanesti[date.weekday()]}, {date.day} {luni_romanesti[date.month-1]} {date.year}</span><br>"
                
                    deadline_text = obtine_mesaj_eveniment(datetime.now().date(), date.date(), consider_weekend)
                    deadline_color = "red" if is_red else "orange"
                    event_text += f"<span style='color: {deadline_color}; font-size: {self.settings['deadlineFont']}px;'>{deadline_text}</span>"
                    if ciclu and not pd.isna(ciclu) and ciclu.lower() != 'nan':
                        event_text += f"<br><span style='font-size: 14px;'>Ciclu: {ciclu}</span>"
                
                    event_label.setText(event_text)
                    event_label.setStyleSheet("""
                        background-color: #f0f0f0;
                        border: 1px solid #dcdcdc;
                        padding: 15px;
                    """)
                    event_label.setAlignment(Qt.AlignCenter)
                    event_label.setWordWrap(True)
                    event_label.setMinimumHeight(120)
                    event_label.mousePressEvent = lambda e, index=index: self.showEventOptions(index)
                    
                    if observatii and not pd.isna(observatii):
                        event_label.setMouseTracking(True)
                        event_label.enterEvent = lambda e, obs=observatii: QToolTip.showText(QCursor.pos(), obs)
                        event_label.leaveEvent = lambda e: QToolTip.hideText()
                    
                    self.scrollLayout.addWidget(event_label)
                
                elif len(notification) > 6 and notification[6] == 'anniversary':  # Aniversare
                    event, date, days_until_anniversary, age, is_red, index, _, observatii = notification
                    event_label = QLabel()
                    
                    color = "red" if is_red else "black"
                    
                    event_text = f"<span style='font-size: {self.settings['eventNameFont']}px;'><b>{event}</b></span><br>"
                    weekday = get_romanian_weekday(date)
                    event_text += f"<span style='color: {color}; font-size: {self.settings['dateFont']}px;'>împlinește {age} ani peste {days_until_anniversary} zile,</span><br>"
                    event_text += f"<span style='color: {color}; font-size: {self.settings['dateFont']}px;'>{weekday}, {date.day} {luni_romanesti[date.month-1]} {date.year}</span>"
                    
                    event_label.setText(event_text)
                    event_label.setStyleSheet("""
                        background-color: #f0f0f0;
                        border: 1px solid #dcdcdc;
                        padding: 15px;
                    """)
                    event_label.setAlignment(Qt.AlignCenter)
                    event_label.setWordWrap(True)
                    event_label.setMinimumHeight(120)
                    event_label.mousePressEvent = lambda e, index=index: self.showEventOptions(index, 'aniversari.csv')
                    
                    if observatii and not pd.isna(observatii):
                        event_label.setMouseTracking(True)
                        event_label.enterEvent = lambda e, obs=observatii: QToolTip.showText(QCursor.pos(), obs)
                        event_label.leaveEvent = lambda e: QToolTip.hideText()
                    
                    self.scrollLayout.addWidget(event_label)

                elif len(notification) > 5 and notification[5] == 'holiday':  # Sărbătoare
                    event, date, days_until_holiday, is_red, index, _, tip, sarbatoare_cruce_rosie, observatii = notification
                    event_label = QLabel()
                    
                    color = "red" if is_red else "black"
                    
                    event_text = f"<span style='font-size: {self.settings['eventNameFont']}px;'><b>{event}</b></span><br>"
                    time_text = self.get_holiday_time_text(days_until_holiday)
                    weekday = get_romanian_weekday(date)
                    event_text += f"<span style='color: {color}; font-size: {self.settings['dateFont']}px;'>{time_text},</span><br>"
                    event_text += f"<span style='color: {color}; font-size: {self.settings['dateFont']}px;'>{weekday}, {date.day} {luni_romanesti[date.month-1]} {date.year}</span>"
                    
                    holiday_info = []
                    if tip and not pd.isna(tip) and str(tip).strip() and str(tip).lower() != 'nan':
                        holiday_info.append(str(tip))
                    if sarbatoare_cruce_rosie and not pd.isna(sarbatoare_cruce_rosie) and str(sarbatoare_cruce_rosie).strip() and str(sarbatoare_cruce_rosie).lower() != 'nan':
                        holiday_info.append(f"<span style='color: red;'>{str(sarbatoare_cruce_rosie)}</span>")
                    
                    if holiday_info:
                        event_text += f"<br><span style='font-size: {self.settings['commemorationTypeFont']}px;'>{', '.join(holiday_info)}</span>"
                    
                    event_label.setText(event_text)
                    event_label.setStyleSheet("""
                        background-color: #f0f0f0;
                        border: 1px solid #dcdcdc;
                        padding: 15px;
                    """)
                    event_label.setAlignment(Qt.AlignCenter)
                    event_label.setWordWrap(True)
                    event_label.setMinimumHeight(120)
                    event_label.mousePressEvent = lambda e, index=index: self.openCSVEditor('sarbatori.csv')
                    
                    if observatii and not pd.isna(observatii):
                        event_label.setMouseTracking(True)
                        event_label.enterEvent = lambda e, obs=observatii: QToolTip.showText(QCursor.pos(), obs)
                        event_label.leaveEvent = lambda e: QToolTip.hideText()
                    
                    self.scrollLayout.addWidget(event_label)
                
                else:
                    print(f"Notificare necunoscută: {notification}")
                    continue

            except Exception as e:
                print(f"Eroare la procesarea notificării: {e}")
                print(f"Notificare problematică: {notification}")
                continue

        self.scrollLayout.addStretch()
        self.logNotifications(notifications)
        print("Notificări afișate")

    def clearNotifications(self):
        print("Ștergere notificări existente")
        while self.scrollLayout.count():
            child = self.scrollLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def logNotifications(self, notifications):
        print("Înregistrare notificări în log")
        try:
            with open('log.txt', 'a', encoding='utf-8') as log_file:
                log_file.write(f"{datetime.now()}: Notificări:\n")
                for notification in notifications:
                    if len(notification) > 8 and notification[8] == 'event':  # Eveniment obișnuit
                        event, date, days_until_event, workdays, weekend_days, consider_weekend, is_red, _, _, ciclu, is_service, observatii = notification
                        if consider_weekend and weekend_days > 0:
                            log_file.write(f"  - Eveniment: {event} (Data: {date.strftime('%d-%m-%Y')}, Zile weekend: {weekend_days}, Zile lucrătoare: {workdays}, Ciclu: {ciclu}, Roșu: {is_red}, Serviciu: {is_service}, Observații: {observatii})\n")
                        else:
                            log_file.write(f"  - Eveniment: {event} (Data: {date.strftime('%d-%m-%Y')}, Zile rămase: {days_until_event}, Ciclu: {ciclu}, Roșu: {is_red}, Serviciu: {is_service}, Observații: {observatii})\n")
                    elif len(notification) > 6 and notification[6] == 'anniversary':  # Aniversare
                        event, date, days_until_anniversary, age, is_red, _, _, observatii = notification
                        log_file.write(f"  - Aniversare: {event} ({age} ani, Data: {date.strftime('%d-%m-%Y')}, Zile rămase: {days_until_anniversary}, Roșu: {is_red}, Observații: {observatii})\n")
                    elif len(notification) > 5 and notification[5] == 'holiday':  # Sărbătoare
                        event, date, days_until_holiday, is_red, _, _, tip, sarbatoare_cruce_rosie, observatii = notification
                        log_file.write(f"  - Sărbătoare: {event} (Data: {date.strftime('%d-%m-%Y')}, Zile rămase: {days_until_holiday}, Roșu: {is_red}, Tip: {tip}, Sărbătoare cu cruce roșie: {sarbatoare_cruce_rosie}, Observații: {observatii})\n")
            print("Notificări înregistrate în log")
        except Exception as e:
            print(f"Eroare la scrierea în fișierul de log: {e}")

    def setupTrayIcon(self):
        print("Configurare icon tray")
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))  # Folosim o iconiță standard
        
        # Creăm meniul pentru iconița din tray
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Arată")
        quit_action = tray_menu.addAction("Ieșire")
        
        # Conectăm acțiunile la funcții
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.quitApplication)
        
        # Setăm meniul pentru iconița din tray
        self.tray_icon.setContextMenu(tray_menu)
        
        # Afișăm iconița în tray
        self.tray_icon.show()

        # Conectăm evenimentul de click pe iconița din tray
        self.tray_icon.activated.connect(self.trayIconActivated)

    def trayIconActivated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def quitApplication(self):
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        if not hasattr(self, 'tray_icon') or self.tray_icon is None:
            self.saveWindowState()
            event.accept()
            return

        msgBox = QMessageBox(self)
        msgBox.setWindowTitle('Confirmare')
        msgBox.setText("Doriți să închideți complet aplicația sau să o minimizați în bară?")
        
        inchideButton = msgBox.addButton("Închide", QMessageBox.YesRole)
        minimizeazaButton = msgBox.addButton("Minimizează", QMessageBox.NoRole)
        
        msgBox.setDefaultButton(minimizeazaButton)
        
        msgBox.exec_()
        
        if msgBox.clickedButton() == inchideButton:
            self.saveWindowState()
            self.saveSettings()
            self.tray_icon.hide()
            event.accept()
            QApplication.quit()
        else:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Reminder App",
                "Aplicația rulează în fundal. Click dreapta pe iconiță pentru opțiuni.",
                QSystemTrayIcon.Information,
                2000
            )

    def showEventOptions(self, index, file='informatii.csv'):
        print(f"Afișare opțiuni eveniment pentru indexul {index}")
        dialog = QDialog(self)
        dialog.setWindowTitle("Opțiuni Eveniment")
        layout = QVBoxLayout()

        if file != 'sarbatori.csv':
            label = QLabel("Setați starea evenimentului:")
            label.setFont(QFont('Arial', 18))
            layout.addWidget(label)

            keep_button = QPushButton("Păstrează")
            keep_button.setFont(QFont('Arial', 18))
            keep_button.clicked.connect(lambda: self.updateEventStatus(index, 'pastreaza', dialog, file))
            layout.addWidget(keep_button)

            complete_button = QPushButton("Îndeplinit")
            complete_button.setFont(QFont('Arial', 18))
            complete_button.clicked.connect(lambda: self.updateEventStatus(index, 'indeplinit', dialog, file))
            layout.addWidget(complete_button)
        else:
            label = QLabel("Deschideți fișierul de sărbători pentru editare:")
            label.setFont(QFont('Arial', 18))
            layout.addWidget(label)

            open_button = QPushButton("Deschide fișier sărbători")
            open_button.setFont(QFont('Arial', 18))
            open_button.clicked.connect(lambda: self.openCSVEditor('sarbatori.csv'))
            layout.addWidget(open_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def updateEventStatus(self, index, status, dialog, file):
        print(f"Actualizare stare eveniment: index={index}, status={status}, file={file}")
        try:
            df = pd.read_csv(file)
            df.loc[index, 'stare'] = status
            df.to_csv(file, index=False)
            dialog.accept()
            self.checkEvents()
            print("Stare eveniment actualizată cu succes")
        except Exception as e:
            error_msg = f"Nu s-a putut actualiza starea evenimentului: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Eroare", error_msg)

    def set_tooltip_style(self, font_size=12):
        style = f"""
        QToolTip {{
            font-size: {font_size}pt;
            background-color: #FFFFC8;
            color: black;
            border: 1px solid black;
            padding: 2px;
        }}
        """
        QApplication.instance().setStyleSheet(QApplication.instance().styleSheet() + style)

    def updateHolidaysButtonVisibility(self):
        show_holidays = self.settings.get('show_commemorations', True)
        if self.openHolidaysButton:
            self.openHolidaysButton.setVisible(show_holidays)

    def checkFilePermissions(self):
        files_to_check = ['informatii.csv', 'aniversari.csv', 'sarbatori.csv', 'window_settings.json']
        for file in files_to_check:
            if not os.access(file, os.R_OK | os.W_OK):
                QMessageBox.warning(self, "Avertisment", f"Nu aveți permisiuni suficiente pentru fișierul {file}.")
                return False
        return True

    def checkIntegrity(self):
        required_files = ['informatii.csv', 'aniversari.csv', 'sarbatori.csv', 'window_settings.json']
        for file in required_files:
            if not os.path.exists(file):
                self.log_error(f"Fișierul {file} lipsește. Se va crea un fișier gol.")
                self.createEmptyCSV(file)
        # Verificați și alte condiții de integritate aici

def main():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    
    # Setăm handler-ul global pentru excepții
    sys.excepthook = global_exception_handler
    
    try:
        ex = ReminderApp()
        ex.show()  # Facem fereastra vizibilă la pornire
        sys.exit(app.exec_())
    except Exception as e:
        error_msg = f"Eroare la inițializarea aplicației: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        with open('error_log.txt', 'w', encoding='utf-8') as f:
            f.write(error_msg)
        QMessageBox.critical(None, "Eroare de Inițializare", f"Eroare la inițializarea aplicației: {str(e)}\nVerificați error_log.txt pentru detalii.")
        sys.exit(1)

def global_exception_handler(exctype, value, tb):
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    print("A apărut o excepție neașteptată:")
    print(error_msg)
    with open('error_log.txt', 'w', encoding='utf-8') as f:
        f.write(error_msg)
    QMessageBox.critical(None, "Eroare", "A apărut o excepție neașteptată. Verificați error_log.txt pentru detalii.")

if __name__ == '__main__':
    main()
    