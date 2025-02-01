import base64
import re
import sys

from Crypto.Cipher import AES
from PyQt5.QtCore import Qt, QDateTime, QTimer, QSize, QRectF
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog, QPrintPreviewWidget
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QFormLayout, QLineEdit, QDateTimeEdit, QComboBox,
                             QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QSpinBox,
                             QCheckBox, QDialog, QLabel, QGraphicsDropShadowEffect, QMenu)
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtGui import QFont, QColor, QIcon, QPainter
from Crypto.Util.Padding import pad, unpad


class EditDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
                  QDialog {
                      background-color: #f5f7fa;
                  }
                  QLabel {
                      color: #4a5568;
                      font-size: 13px;
                  }
                  QPushButton {
                      background-color: #4c6ef5;
                      border: none;
                      color: white;
                      padding: 8px 16px;
                      border-radius: 6px;
                      min-width: 80px;
                      font-weight: 500;
                      font-size: 13px;
                  }
                  QPushButton:hover {
                      background-color: #3b5bdb;
                  }
                  QPushButton:pressed {
                      background-color: #2c4ac7;
                  }
              """)
        self.data = data
        self.setWindowTitle("编辑预约信息")
        self.setGeometry(480, 50, 960, 960)
        self.setWindowIcon(QIcon("icon.png"))
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # ID显示（不可编辑）
        self.id_label = QLabel(f"记录ID: {self.data[0]}")
        layout.addWidget(self.id_label)

        # 表单布局（复用主界面样式）
        form_layout = QFormLayout()

        self.name_edit = QLineEdit(self.data[1])
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["女", "男", "其他"])
        self.gender_combo.setCurrentText(self.data[2])
        # 继续添加其他控件...

        # 按需创建所有输入控件并设置值
        self.age_edit = QSpinBox()
        self.age_edit.setValue(int(self.data[3]))
        self.id_edit = QLineEdit(self.data[4])
        self.id_edit.setMaxLength(18)
        self.phone_edit = QLineEdit(self.data[5])
        self.phone_edit.setMaxLength(11)
        self.time_edit = QDateTimeEdit(QDateTime.fromString(self.data[6], "yyyy-MM-dd HH:mm"),calendarPopup=True)
        self.service_edit = QTextEdit(self.data[7])
        self.designer_combo = QComboBox()
        self.designer_combo.addItems(["孙总", "蔡医生"])
        self.designer_combo.setCurrentText(self.data[8])
        self.dept_combo = QComboBox()
        self.dept_combo.addItems(["仟美医疗美容"])
        self.dept_combo.setCurrentText(self.data[9])
        self.first_check = QCheckBox()
        self.first_check.setChecked(self.data[10] == "是")
        self.amount_edit = QLineEdit(self.data[11])
        self.notes_edit = QTextEdit(self.data[12])

        # 添加所有表单行...
        form_layout.addRow("客户姓名：", self.name_edit)
        form_layout.addRow("性别：", self.gender_combo)
        form_layout.addRow("年龄：", self.age_edit)
        form_layout.addRow("身份证号：", self.id_edit)
        form_layout.addRow("联系电话：", self.phone_edit)
        form_layout.addRow("预约时间：", self.time_edit)
        form_layout.addRow("项目：", self.service_edit)
        form_layout.addRow("设计总监：", self.designer_combo)
        form_layout.addRow("所属部门：", self.dept_combo)
        form_layout.addRow("首次登记：", self.first_check)
        form_layout.addRow("项目金额：", self.amount_edit)
        form_layout.addRow("备注信息：", self.notes_edit)

        # 按钮布局
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.on_save)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(form_layout)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def on_save(self):
        """保存按钮点击事件"""
        # 获取输入数据
        name = self.name_edit.text().strip()
        id_number = self.id_edit.text().strip()
        phone = self.phone_edit.text().strip()
        amount = self.amount_edit.text().strip()

        # 验证输入数据
        if not name:
            QMessageBox.warning(self, "警告", "客户姓名不能为空！")
            return
        if not self.validate_id(id_number):
            QMessageBox.warning(self, "警告", "身份证号格式错误！")
            return
        if not self.validate_phone(phone):
            QMessageBox.warning(self, "警告", "请输入有效的11位手机号码！")
            return
        if not self.validate_amount(amount):
            QMessageBox.warning(self, "警告", "项目金额格式错误！")
            return

        # 如果验证通过，则关闭弹窗
        self.accept()

    def validate_id(self, id_number):
        # 身份证格式校验
        id_pattern = re.compile(r'^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[0-9Xx]$')
        if not id_pattern.match(id_number):
            return False

        # 身份证校验码验证
        if not self.validate_chinese_id_check_digit(id_number):
            return False
        return True

    def validate_phone(self, phone):
        """验证手机号"""
        pattern = re.compile(r'^1[3-9]\d{9}$')
        if not pattern.match(phone):
            return False
        return True

    def validate_amount(self, amount):
        """验证金额"""
        if amount.strip() == "":
            return False
        if not amount.isdigit() or float(amount) <= 0:
            return False
        return True

    def validate_chinese_id_check_digit(self, id_number):
        """校验身份证号码的最后一位校验码"""
        factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_code_map = "10X98765432"
        total = sum(int(id_number[i]) * factors[i] for i in range(17))
        return check_code_map[total % 11] == id_number[-1].upper()


class AppointmentSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("仟美医疗项目登记系统")
        self.setGeometry(400, 50, 1280, 960)
        self.setWindowIcon(QIcon("icon.png"))
        self.showMaximized()
        self.encryption_key = b'thisisasecretkey'  # 16字节密钥（示例，实际应安全存储）

        # 初始化数据库
        self.init_db()

        # 设置界面样式
        self.setup_style()

        # 创建界面组件
        self.create_widgets()
        self.setup_layout()
        self.setup_connections()

        # 初始化数据
        self.refresh_table()

        # 初始化状态栏
        self.statusBar().showMessage("就绪 | 总预约数: 0")

    def encrypt(self, plain_text):
        cipher = AES.new(self.encryption_key, AES.MODE_ECB)
        padded_data = pad(plain_text.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted).decode('utf-8')

    def decrypt(self, cipher_text):
        cipher = AES.new(self.encryption_key, AES.MODE_ECB)
        encrypted_data = base64.b64decode(cipher_text)
        decrypted = cipher.decrypt(encrypted_data)
        return unpad(decrypted, AES.block_size).decode('utf-8')

    def setup_style(self):
        """设置全局样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QGroupBox {
                background: white;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                color: #495057;
                font-weight: bold;
            }
            QPushButton {
                background-color: #4dabf7;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #339af0;
            }
            QPushButton:pressed {
                background-color: #228be6;
            }
            QTableWidget {
                background: white;
                selection-color: black;  
                alternate-background-color: #f8f9fa;
                selection-background-color: #e7f5ff;
                border: 1px solid #dee2e6;
                gridline-color: #dee2e6;
            }
            QHeaderView::section {
                background-color: #4dabf7;
                color: white;
                padding: 8px;
                border: none;
            }
            QLineEdit, QDateTimeEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px;
                min-height: 28px;
            }
            QLineEdit:focus, QDateTimeEdit:focus, QComboBox:focus, 
            QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #a5d8ff;
            }
            QCheckBox {
                spacing: 8px;
            }
        """)
        self.setFont(QFont("Microsoft YaHei", 10))

    def add_shadow(widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(2, 2)
        widget.setGraphicsEffect(shadow)

    def create_widgets(self):
        """创建界面控件"""
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入客户姓名")

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["女", "男", "其他"])

        self.age_input = QSpinBox()
        self.age_input.setRange(0, 150)
        self.age_input.setValue(25)

        self.id_input = QLineEdit()
        self.id_input.setMaxLength(18)
        self.id_input.setPlaceholderText("请输入18位身份证号码")

        self.phone_input = QLineEdit()
        self.phone_input.setMaxLength(11)
        self.phone_input.setPlaceholderText("请输入11位联系电话")

        self.time_input = QDateTimeEdit(calendarPopup=True)
        self.time_input.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.time_input.setDisplayFormat("yyyy-MM-dd HH:mm")

        self.service_combo = QTextEdit()
        self.service_combo.setPlaceholderText("可填写项目详细信息...")

        self.designer_combo = QComboBox()
        self.designer_combo.addItems(["孙总", "蔡医生"])

        self.dept_combo = QComboBox()
        self.dept_combo.addItems(["仟美医疗美容"])

        self.first_time_check = QCheckBox("首次登记")

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("请输入金额")

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("可填写特殊要求或备注信息...")
        self.submit_btn = QPushButton("📅 提交登记")
        self.submit_btn.setIconSize(QSize(18, 18))

        # 搜索区域
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入姓名/电话搜索...")
        self.search_btn = QPushButton("🔍 搜索")
        self.reset_btn = QPushButton("🔄 重置")

        # 表格区域
        self.appointment_table = QTableWidget()
        self.appointment_table.setColumnCount(13)
        self.appointment_table.setHorizontalHeaderLabels(
            ["ID", "客户姓名", "性别", "年龄", "身份证号",
             "联系电话", "预约时间", "项目", "设计总监",
             "所属部门", "首次登记", "金额", "备注"]
        )
        self.appointment_table.verticalHeader().setVisible(False)
        self.appointment_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.appointment_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.appointment_table.setAlternatingRowColors(True)
        self.appointment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.appointment_table.setSortingEnabled(True)
        self.appointment_table.setContextMenuPolicy(Qt.CustomContextMenu)  # 启用右键菜单
        self.appointment_table.customContextMenuRequested.connect(self.show_context_menu)  # 连接右键

    def show_context_menu(self, position):
        # 创建右键菜单
        menu = QMenu(self)

        # 添加“删除”选项
        delete_action = menu.addAction("🗑️ 删除")
        delete_action.triggered.connect(self.delete_selected_row)

        # 添加“打印”选项
        print_action = menu.addAction("🖨️ 打印")
        print_action.triggered.connect(self.print_selected_row)

        # 显示菜单
        menu.exec_(self.appointment_table.viewport().mapToGlobal(position))

    def print_selected_row(self):
        # 获取选中的行
        selected_row = self.appointment_table.currentRow()
        if selected_row == -1:  # 如果没有选中行
            QMessageBox.warning(self, "警告", "请先选择要打印的行！")
            return

        # 获取选中行的数据
        row_data = []
        for col in range(self.appointment_table.columnCount()):
            item = self.appointment_table.item(selected_row, col)
            row_data.append(item.text() if item else "")

        # 生成打印内容
        self.generate_print_content(row_data)

    def generate_print_content(self, row_data):
        # 创建打印预览对话框
        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageMargins(20, 20, 20, 20, QPrinter.Millimeter)  # 设置页面边距
            preview_dialog = QPrintPreviewDialog(printer, self)
            preview_widget = preview_dialog.findChild(QPrintPreviewWidget)

            if preview_widget:
                # 设置缩放比例为50%
                preview_widget.setZoomFactor(0.8)
            preview_dialog.paintRequested.connect(lambda: self.render_print_content(printer, row_data))
            preview_dialog.exec_()
        except Exception as e:
            print(e)

    def render_print_content(self, printer, row_data):
        # 创建 QPainter 对象
        painter = QPainter()
        painter.begin(printer)

        # 设置字体
        font = QFont("Microsoft YaHei", 10)  # 使用更清晰的字体
        painter.setFont(font)
        painter.setPen(QColor(0, 0, 0))  # 黑色

        # 页面边距
        margin = 50
        page_width = printer.pageRect().width() - 2 * margin

        # 绘制标题
        title = "客户登记信息"
        title_font = QFont("Microsoft YaHei", 14, QFont.Bold)  # 标题字体加粗
        painter.setFont(title_font)
        title_rect = QRectF(margin, margin, page_width, 200)
        painter.drawText(title_rect, Qt.AlignCenter, title)

        # 设置表格样式
        table_font = QFont("Microsoft YaHei", 10)
        painter.setFont(table_font)
        row_height = 200  # 每行高度
        col_width = page_width / 2  # 每列宽度（两列布局：标签 + 值）

        # 绘制表格内容
        labels = [
                "ID","客户姓名:", "性别:", "年龄:", "身份证号:", "联系电话:",
            "预约时间:", "项目:", "设计总监:", "所属部门:", "首次登记:", "金额:", "备注:"
        ]

        y_offset = margin + 200  # 起始 Y 坐标（标题下方）

        for i, (label, value) in enumerate(zip(labels, row_data)):

            if "项目" in label or "备注" in label:
                row_height = row_height + 40  # 额外增加40像素高度

            # 绘制标签
                label_rect = QRectF(margin, y_offset + i * (row_height -40), col_width, y_offset + i * (row_height -40))
                painter.drawText(label_rect,Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, label)

                # 绘制值
                value_rect = QRectF(margin + col_width, y_offset + i * (row_height -40), col_width, y_offset + i * (row_height -40))
                painter.drawText(value_rect,Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, value)

                # 绘制表格线
                painter.drawLine(margin, y_offset + (i + 1) * row_height, margin + page_width,
                                 y_offset + (i + 1) * row_height)
            else:
                label_rect = QRectF(margin, y_offset + i * row_height, col_width, row_height)
                painter.drawText(label_rect,Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, label)

                # 绘制值
                value_rect = QRectF(margin + col_width, y_offset + i * row_height, col_width, row_height)
                painter.drawText(value_rect,Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, value)

                # 绘制表格线
                painter.drawLine(margin, y_offset + (i + 1) * row_height, margin + page_width,
                                 y_offset + (i + 1) * row_height)

        # 绘制表格边框
        painter.drawRect(margin, y_offset, page_width, len(labels) * row_height)

        # 结束绘制
        painter.end()

    def delete_selected_row(self):
        # 获取选中的行
        selected_row = self.appointment_table.currentRow()
        if selected_row == -1:  # 如果没有选中行
            QMessageBox.warning(self, "警告", "请先选择要删除的行！")
            return

        # 获取选中行的ID
        record_id = int(self.appointment_table.item(selected_row, 0).text())

        # 弹出确认对话框
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这条记录吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        # 从数据库中删除记录
        query = QSqlQuery()
        query.prepare("DELETE FROM appointments WHERE id = ?")
        query.addBindValue(record_id)

        if query.exec():
            # 从表格中移除行
            self.appointment_table.removeRow(selected_row)
            self.show_status("删除成功！", "success")
            self.refresh_table()  # 刷新表格数据
        else:
            QMessageBox.critical(self, "错误", f"删除失败: {query.lastError().text()}")

    def setup_layout(self):
        """设置界面布局"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 输入表单
        input_group = QGroupBox("客户登记信息")
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.addRow("客户姓名：", self.name_input)
        form_layout.addRow("性别：", self.gender_combo)
        form_layout.addRow("年龄：", self.age_input)
        form_layout.addRow("身份证号：", self.id_input)
        form_layout.addRow("联系电话：", self.phone_input)
        form_layout.addRow("预约时间：", self.time_input)
        form_layout.addRow("项目：", self.service_combo)
        form_layout.addRow("设计总监：", self.designer_combo)
        form_layout.addRow("所属部门：", self.dept_combo)
        form_layout.addRow("首次登记：", self.first_time_check)
        form_layout.addRow("项目金额：", self.amount_input)
        form_layout.addRow("备注信息：", self.notes_input)
        form_layout.addRow(self.submit_btn)
        input_group.setLayout(form_layout)

        # 搜索栏
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.reset_btn)

        # 表格区域
        table_group = QGroupBox("预约记录")
        table_layout = QVBoxLayout()
        table_layout.addLayout(search_layout)
        table_layout.addWidget(self.appointment_table)
        table_group.setLayout(table_layout)

        main_layout.addWidget(input_group, 1)
        main_layout.addWidget(table_group, 3)

    def setup_connections(self):
        """连接信号槽"""
        self.submit_btn.clicked.connect(self.add_appointment)
        self.search_btn.clicked.connect(self.search_appointments)
        self.reset_btn.clicked.connect(self.clear_search)
        self.search_input.textChanged.connect(self.delayed_search)
        self.appointment_table.cellDoubleClicked.connect(self.show_edit_dialog)
        # 在create_widgets方法中修改表格属性
        self.appointment_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 保持不可直接编辑
        self.appointment_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.appointment_table.setToolTip("双击行进行编辑")  # 添加提示

    def init_db(self):
        """初始化数据库"""
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName("qianmei.db")

        if not self.db.open():
            QMessageBox.critical(
                self, "数据库错误",
                f"无法打开数据库: {self.db.lastError().text()}"
            )
            return False

        query = QSqlQuery()
        query.exec("""
            CREATE TABLE IF NOT EXISTS qianmei (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                gender TEXT NOT NULL,
                age INTEGER NOT NULL,
                id_number TEXT NOT NULL,
                phone TEXT NOT NULL,
                appointment_time DATETIME NOT NULL,
                service_type TEXT NOT NULL,
                design_director TEXT NOT NULL,
                department TEXT NOT NULL,
                is_first_time INTEGER NOT NULL,
                amount TEXT NOT NULL,
                notes TEXT,
                submit_time DATETIME NOT NULL
            )
        """)
        return True

    def add_appointment(self):
        """添加新预约"""
        # 获取字段值
        name = self.name_input.text().strip()
        gender = self.gender_combo.currentText()
        age = self.age_input.value()
        id_number = self.id_input.text().replace(" ", "")
        phone = self.phone_input.text().strip()
        time = self.time_input.dateTime().toString("yyyy-MM-dd HH:mm")
        service = self.service_combo.toPlainText().strip()
        designer = self.designer_combo.currentText()
        dept = self.dept_combo.currentText()
        is_first = 1 if self.first_time_check.isChecked() else 0
        amount = self.amount_input.text().strip()
        notes = self.notes_input.toPlainText().strip()

        # 输入验证
        if not name:
            QMessageBox.warning(self, "警告", "客户姓名不能为空")
            self.name_input.setFocus()
            return
        if not self.id_check(id_number):
            QMessageBox.warning(self, "警告", "身份证号格式错误")
            self.id_input.setFocus()
            return
        if not self.phone_check(phone):
            QMessageBox.warning(self, "警告", "请输入有效的11位手机号码！")
            self.phone_input.setFocus()
            return
        if not self.amount_check(amount):
            QMessageBox.warning(self, "警告", "项目金额格式错误！")
            self.amount_input.setFocus()
            return

        id_number = self.encrypt(id_number)
        phone = self.encrypt(phone)

        # 插入数据库
        query = QSqlQuery()
        query.prepare("""
            INSERT INTO appointments 
            (customer_name, gender, age, id_number, phone,
             appointment_time, service_type, design_director, department,
             is_first_time, amount, notes, submit_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        params = [
            name, gender, age, id_number, phone,
            time, service, designer, dept, is_first, amount, notes,QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm")
        ]
        for value in params:
            query.addBindValue(value)

        if not query.exec():
            QMessageBox.critical(
                self, "数据库错误",
                f"保存失败: {query.lastError().text()}"
            )
            return

        self.clear_form()
        self.refresh_table()
        QMessageBox.information(self, "提示", "登记信息提交成功")
        self.show_status("登记信息提交成功！", "success")

    def search_appointments(self):
        """搜索预约"""
        keyword = self.search_input.text().strip()
        if keyword.strip() == "":
            return
        query = QSqlQuery()
        query.prepare("""
            SELECT id, customer_name, gender, age, id_number,
                   phone, strftime('%Y-%m-%d %H:%M', appointment_time),
                   service_type, design_director, department, 
                   CASE WHEN is_first_time THEN '是' ELSE '否' END,
                   amount, notes
            FROM appointments
            WHERE customer_name LIKE ? OR phone LIKE ?
            ORDER BY appointment_time
        """)
        query.addBindValue(f"%{keyword}%")
        query.addBindValue(f"%{keyword}%")

        self.appointment_table.setRowCount(0)
        if query.exec():
            while query.next():
                row = self.appointment_table.rowCount()
                self.appointment_table.insertRow(row)
                for col in range(13):
                    item = QTableWidgetItem(str(query.value(col)))
                    if col == 11:  # 金额列右对齐
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    elif col == 5 or col ==4:
                        item = QTableWidgetItem(str(self.decrypt(query.value(col))))
                    self.appointment_table.setItem(row, col, item)

            self.show_status(f"找到 {self.appointment_table.rowCount()} 条结果", "info")
        else:
            self.show_status("搜索失败", "error")

    def delayed_search(self):
        """延时搜索"""
        QTimer.singleShot(300, self.search_appointments)

    def clear_search(self):
        """清除搜索"""
        self.search_input.clear()
        self.refresh_table()

    def refresh_table(self):
        """刷新表格数据"""
        self.appointment_table.setRowCount(0)
        query = QSqlQuery("SELECT COUNT(*) FROM appointments")
        if query.next():
            self.statusBar().showMessage(f"就绪 | 总预约数: {query.value(0)}")

        query.exec("""
            SELECT id, customer_name, gender, age, id_number,
                   phone, strftime('%Y-%m-%d %H:%M', appointment_time),
                   service_type, design_director, department, 
                   CASE WHEN is_first_time THEN '是' ELSE '否' END,
                   amount, notes
            FROM appointments 
            ORDER BY appointment_time
        """)

        while query.next():
            row = self.appointment_table.rowCount()
            self.appointment_table.insertRow(row)
            for col in range(13):
                item = QTableWidgetItem(str(query.value(col)))
                if col == 11:  # 金额列右对齐
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col == 5 or col == 4:
                    item = QTableWidgetItem(str(self.decrypt(query.value(col))))
                self.appointment_table.setItem(row, col, item)

        # 设置时间状态颜色
        current_time = QDateTime.currentDateTime()
        for row in range(self.appointment_table.rowCount()):
            time_item = self.appointment_table.item(row, 6)  # 预约时间列
            appointment_time = QDateTime.fromString(time_item.text(), "yyyy-MM-dd HH:mm")
            if appointment_time < current_time:
                time_item.setForeground(QColor("#ff6b6b"))
                time_item.setToolTip("已过期预约")

    def clear_form(self):
        """清空输入表单"""
        self.name_input.clear()
        self.gender_combo.setCurrentIndex(0)
        self.age_input.setValue(25)
        self.id_input.clear()
        self.phone_input.clear()
        self.time_input.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.service_combo.clear()
        self.designer_combo.setCurrentIndex(0)
        self.dept_combo.setCurrentIndex(0)
        self.first_time_check.setChecked(False)
        self.notes_input.clear()

    def show_status(self, message, type="info"):
        """显示状态信息"""
        colors = {
            "info": "#4dabf7",
            "success": "#40c057",
            "warning": "#fab005",
            "error": "#fa5252"
        }
        self.statusBar().showMessage(message)
        self.statusBar().setStyleSheet(f"color: {colors.get(type, '#495057')};")

    def closeEvent(self, event):
        """关闭窗口时关闭数据库连接"""
        self.db.close()
        event.accept()

    def show_edit_dialog(self, row):
        # 获取记录ID
        record_id = int(self.appointment_table.item(row, 0).text())

        # 从数据库获取完整数据
        query = QSqlQuery()
        query.prepare("SELECT * FROM appointments WHERE id = ?")
        query.addBindValue(record_id)
        if not query.exec() or not query.next():
            QMessageBox.warning(self, "错误", "无法获取记录信息")
            return

        # 获取所有字段值
        data = []
        for i in range(13):
            val = query.value(i)
            if i == 4 or i == 5:
                val = self.decrypt(val)
            data.append(val)
        data[10] = "是" if data[10] else "否"  # 转换首次登记状态

        # 显示编辑对话框
        dialog = EditDialog(data, self)
        if dialog.exec() == QDialog.Accepted:
            # 获取修改后的值
            new_data = {
                "name": dialog.name_edit.text().strip(),
                "gender": dialog.gender_combo.currentText(),
                "age": dialog.age_edit.value(),
                "id_number": dialog.id_edit.text(),
                "phone": dialog.phone_edit.text(),
                "time": dialog.time_edit.dateTime().toString("yyyy-MM-dd HH:mm"),
                "service": dialog.service_edit.toPlainText(),
                "designer": dialog.designer_combo.currentText(),
                "dept": dialog.dept_combo.currentText(),
                "is_first": 1 if dialog.first_check.isChecked() else 0,
                "amount": dialog.amount_edit.text().replace(" ", ""),
                "notes": dialog.notes_edit.toPlainText()
            }

            # 输入验证（与主界面相同）
            if not self.validate_edit_data(new_data, record_id):
                return

            # 更新数据库
            query = QSqlQuery()
            query.prepare("""
                UPDATE appointments SET
                    customer_name = ?, gender = ?, age = ?, id_number = ?,
                    phone = ?, appointment_time = ?, service_type = ?,
                    design_director = ?, department = ?, is_first_time = ?,
                    amount = ?, notes = ?
                WHERE id = ?
            """)
            params = [
                new_data["name"], new_data["gender"], new_data["age"],
                self.encrypt(new_data["id_number"]), self.encrypt(new_data["phone"]), new_data["time"],
                new_data["service"], new_data["designer"], new_data["dept"],
                new_data["is_first"], new_data["amount"], new_data["notes"],
                record_id
            ]
            for value in params:
                query.addBindValue(value)

            if query.exec():
                self.refresh_table()
                self.show_status("更新成功！", "success")
            else:
                QMessageBox.critical(self, "错误", f"更新失败: {query.lastError().text()}")

    def validate_chinese_id_check_digit(self, id_number):
        """校验身份证号码的最后一位校验码"""
        factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_code_map = "10X98765432"
        total = sum(int(id_number[i]) * factors[i] for i in range(17))
        return check_code_map[total % 11] == id_number[-1].upper()

    def id_check(self,id_number):
        # 身份证格式校验
        id_pattern = re.compile(r'^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[0-9Xx]$')
        if not id_pattern.match(id_number):
            return False

        # 身份证校验码验证
        if not self.validate_chinese_id_check_digit(id_number):
            return False
        return True

    def phone_check(self,phone):
        pattern = re.compile(r'^1[3-9]\d{9}$')
        if not pattern.match(phone):
            return False
        return True
    def amount_check(self, amount):
        # 金额校验
        if amount.strip() =="":
            return False
        if not amount.isdigit() or float(amount) <= 0:
            return False
        return True


    def validate_edit_data(self, data, record_id):
        if not data["name"]:
            QMessageBox.warning(self, "警告", "客户姓名不能为空！")
            return False
            # 身份证校验码验证
        if not self.id_check(data["id_number"]):
            QMessageBox.warning(self, "警告", "身份证号格式错误！")
            return False
        # 电话号码格式校验
        if not self.phone_check(data["phone"]):
            QMessageBox.warning(self, "警告", "请输入有效的11位手机号码！")
            return False

        # 金额校验
        if not self.amount_check(data["amount"]):
            QMessageBox.warning(self, "警告", "项目金额格式错误！")
            return False

        return True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppointmentSystem()
    window.show()
    sys.exit(app.exec_())