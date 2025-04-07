import sys
import os
import json
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QListWidget,
                           QStackedWidget, QLineEdit, QMessageBox, QListWidgetItem,
                           QFrame, QScrollArea, QSizePolicy, QSpacerItem, QMenu,
                           QButtonGroup, QRadioButton, QToolButton, QDialog, QDialogButtonBox,
                           QInputDialog, QCheckBox)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QCursor, QAction

class ExpenseCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多事件计算器")
        self.setGeometry(100, 100, 900, 650)
        
        # 确保history文件夹存在
        self.history_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history")
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)
            
        # 确保templates文件夹存在
        self.templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局
        layout = QHBoxLayout()
        main_widget.setLayout(layout)
        
        # 创建侧边栏
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(220)
        sidebar.setMaximumWidth(250)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(10, 15, 10, 15)
        sidebar_layout.setSpacing(10)
        sidebar.setLayout(sidebar_layout)
        
        # 添加历史记录标题
        history_label = QLabel("历史记录")
        history_label.setObjectName("sectionTitle")
        sidebar_layout.addWidget(history_label)
        
        # 添加历史记录列表
        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        self.history_list.setAlternatingRowColors(True)
        self.history_list.itemClicked.connect(self.history_item_clicked)
        self.history_list.itemDoubleClicked.connect(self.load_calculation_from_history)
        self.history_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self.show_history_context_menu)
        sidebar_layout.addWidget(self.history_list)
        
        # 添加按钮区域
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        # 添加新建按钮
        new_button = QPushButton("新建计算")
        new_button.setObjectName("primaryButton")
        new_button.clicked.connect(self.create_new_calculation)
        buttons_layout.addWidget(new_button)
        
        # 添加删除按钮
        delete_button = QPushButton("删除记录")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.delete_selected_record)
        buttons_layout.addWidget(delete_button)
        
        sidebar_layout.addLayout(buttons_layout)
        
        # 添加模板选项
        templates_label = QLabel("模板管理")
        templates_label.setObjectName("sectionTitle")
        sidebar_layout.addWidget(templates_label)
        
        templates_buttons = QHBoxLayout()
        
        save_template_button = QPushButton("保存模板")
        save_template_button.setObjectName("actionButton")
        save_template_button.clicked.connect(self.save_current_as_template)
        templates_buttons.addWidget(save_template_button)
        
        load_template_button = QPushButton("使用模板")
        load_template_button.setObjectName("actionButton")
        load_template_button.clicked.connect(self.load_from_template)
        templates_buttons.addWidget(load_template_button)
        
        sidebar_layout.addLayout(templates_buttons)
        
        layout.addWidget(sidebar)
        
        # 创建分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("separator")
        layout.addWidget(separator)
        
        # 创建主内容区域
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack")
        layout.addWidget(self.content_stack)
        
        # 创建欢迎页面
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout()
        welcome_widget.setLayout(welcome_layout)
        
        welcome_label = QLabel("欢迎使用多事件计算器")
        welcome_label.setObjectName("welcomeTitle")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(welcome_label)
        
        welcome_desc = QLabel("请从左侧选择历史记录或创建新计算")
        welcome_desc.setObjectName("welcomeDesc")
        welcome_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(welcome_desc)
        
        self.content_stack.addWidget(welcome_widget)
        
        # 初始化数据
        self.calculations = {}
        self.current_calculation_id = None
        self.templates = {}
        
        # 存储每个人的消费数据
        self.people_data = {}
        
        # 存储当前计算的人数
        self.current_num_people = 0
        
        # 存储人员总额标签的引用
        self.person_total_labels = []
        
        # 标记是否是直接添加模式
        self.direct_add_mode = False
        
        # 加载历史记录和模板
        self.load_history()
        self.load_templates()
        
    def history_item_clicked(self, item):
        """单击选中历史记录项"""
        # 通过样式显示选中状态
        for i in range(self.history_list.count()):
            self.history_list.item(i).setData(Qt.ItemDataRole.UserRole + 1, False)
        item.setData(Qt.ItemDataRole.UserRole + 1, True)
        self.history_list.update()
        
    def show_history_context_menu(self, position):
        """显示历史记录右键菜单"""
        item = self.history_list.itemAt(position)
        if not item:
            return
            
        context_menu = QMenu(self)
        
        open_action = QAction("打开", self)
        open_action.triggered.connect(lambda: self.load_calculation_from_history(item))
        
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_record(item))
        
        context_menu.addAction(open_action)
        context_menu.addAction(delete_action)
        
        context_menu.exec(QCursor.pos())
        
    def create_new_calculation(self):
        """创建新的计算"""
        try:
            # 清空当前人员数据
            self.people_data = {}
            
            # 创建新的计算记录
            import time
            calculation_id = f"calc_{int(time.time())}"
            calc_date = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 创建新计算结构
            self.calculations[calculation_id] = {
                "日期": calc_date,
                "标题": f"计算 {calc_date}",
                "人员": [],
                "数据": {}
            }
            
            # 设置当前计算ID
            self.current_calculation_id = calculation_id
            
            # 设置为直接添加模式
            self.direct_add_mode = True
            
            # 创建人员计算页面
            self.setup_people_calculation()
            
            # 显示添加人员对话框
            self.show_add_person_dialog()
            
            # 切换到人员计算页面
            self.content_stack.setCurrentIndex(1)
            
            # 更新历史记录列表
            self.update_history_list()
            
        except Exception as e:
            print(f"创建新计算时出错: {e}")
            QMessageBox.warning(self, "错误", f"创建新计算时出错: {e}")
    
    def add_person_to_calculation(self, name):
        """将人员添加到当前计算"""
        if not name:
            QMessageBox.warning(self, "错误", "人员名称不能为空！")
            return False
            
        # 确保当前有有效的计算
        if not self.current_calculation_id:
            QMessageBox.warning(self, "错误", "没有活动的计算！")
            return False
            
        # 检查是否重名
        if name in self.people_data:
            QMessageBox.warning(self, "错误", f"已存在名为 '{name}' 的人员！")
            return False
            
        # 初始化该人员的数据结构
        self.people_data[name] = {"衣": 0, "食": 0, "住": 0, "行": 0, "总额": 0}
        
        # 更新计算中的人员列表
        if self.current_calculation_id in self.calculations:
            if "人员" not in self.calculations[self.current_calculation_id]:
                self.calculations[self.current_calculation_id]["人员"] = []
                
            if name not in self.calculations[self.current_calculation_id]["人员"]:
                self.calculations[self.current_calculation_id]["人员"].append(name)
                
            # 更新计算数据
            self.calculations[self.current_calculation_id]["数据"] = self.people_data
            
        # 更新人员列表UI
        self.load_people_list()
        
        # 保存当前计算
        self.save_current_calculation()
        
        # 更新总费用显示
        self.update_all_totals()
        
        return True
        
    def show_add_person_dialog(self):
        """显示添加人员对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加人员")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        # 添加提示标签
        label = QLabel("请输入人员姓名:")
        layout.addWidget(label)
        
        # 添加输入框
        name_input = QLineEdit()
        name_input.setPlaceholderText("输入姓名")
        layout.addWidget(name_input)
        
        # 添加模板选择提示
        template_label = QLabel("或从模板中选择:")
        layout.addWidget(template_label)
        
        # 添加模板列表
        template_list = QListWidget()
        if hasattr(self, 'templates') and self.templates:
            for template in self.templates:
                template_list.addItem(template)
        layout.addWidget(template_list)
        
        # 添加按钮区域
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)
        
        # 连接信号
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        # 显示对话框
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # 获取输入的名称或选中的模板
            name = name_input.text().strip()
            selected_items = template_list.selectedItems()
            
            if selected_items and not name:
                # 使用选中的模板
                name = selected_items[0].text()
                
            # 添加人员
            if name:
                self.add_person_to_calculation(name)
            else:
                QMessageBox.warning(self, "错误", "请输入人员姓名或选择模板！")
    
    def start_people_setup(self, mode_id):
        """根据选择的模式开始设置人员"""
        self.direct_add_mode = (mode_id == 2)  # 2 是逐个添加模式
        
        if self.direct_add_mode:
            # 创建单人添加页面
            self.create_single_person_page()
        else:
            # 创建批量添加页面
            self.create_batch_people_page()
    
    def create_batch_people_page(self):
        """创建批量添加人员页面"""
        people_widget = QWidget()
        people_layout = QVBoxLayout()
        people_widget.setLayout(people_layout)
        
        # 添加页面标题
        title_label = QLabel("添加人员")
        title_label.setObjectName("pageTitle")
        people_layout.addWidget(title_label)
        
        people_layout.addSpacing(10)
        
        # 添加人员列表
        list_label = QLabel("已添加人员:")
        list_label.setObjectName("sectionTitle")
        people_layout.addWidget(list_label)
        
        self.people_list = QListWidget()
        self.people_list.setObjectName("peopleList")
        self.people_list.setAlternatingRowColors(True)
        self.people_list.setMinimumHeight(150)
        self.people_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.people_list.customContextMenuRequested.connect(self.show_people_list_context_menu)
        people_layout.addWidget(self.people_list)
        
        # 添加人员输入区域
        add_person_layout = QHBoxLayout()
        self.person_name_input = QLineEdit()
        self.person_name_input.setPlaceholderText("输入人员名称")
        self.person_name_input.setMinimumWidth(200)
        self.person_name_input.returnPressed.connect(self.add_new_person)
        
        add_person_button = QPushButton("添加人员")
        add_person_button.setObjectName("actionButton")
        add_person_button.clicked.connect(self.add_new_person)
        
        add_person_layout.addWidget(self.person_name_input)
        add_person_layout.addWidget(add_person_button)
        add_person_layout.addStretch()
        people_layout.addLayout(add_person_layout)
        
        people_layout.addSpacing(20)
        
        # 添加完成按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # 模板按钮
        template_button = QPushButton("从模板添加")
        template_button.setObjectName("actionButton")
        template_button.clicked.connect(self.add_from_template)
        buttons_layout.addWidget(template_button)
        
        buttons_layout.addSpacing(10)
        
        done_button = QPushButton("完成设置")
        done_button.setObjectName("primaryButton")
        done_button.setMinimumWidth(120)
        done_button.clicked.connect(self.setup_people_calculation)
        buttons_layout.addWidget(done_button)
        
        people_layout.addLayout(buttons_layout)
        
        # 添加并显示新页面
        self.content_stack.addWidget(people_widget)
        self.content_stack.setCurrentWidget(people_widget)
        
        # 设置焦点
        self.person_name_input.setFocus()
    
    def create_single_person_page(self):
        """创建单人添加页面"""
        single_widget = QWidget()
        single_layout = QVBoxLayout()
        single_widget.setLayout(single_layout)
        
        # 添加页面标题
        title_label = QLabel("添加单个人员")
        title_label.setObjectName("pageTitle")
        single_layout.addWidget(title_label)
        
        single_layout.addSpacing(15)
        
        # 添加人员输入区域
        input_frame = QFrame()
        input_frame.setObjectName("inputFrame")
        input_layout = QVBoxLayout(input_frame)
        
        name_label = QLabel("人员名称:")
        name_label.setObjectName("fieldLabel")
        
        self.single_person_name = QLineEdit()
        self.single_person_name.setPlaceholderText("输入人员名称")
        self.single_person_name.returnPressed.connect(self.add_single_person)
        
        input_layout.addWidget(name_label)
        input_layout.addWidget(self.single_person_name)
        
        single_layout.addWidget(input_frame)
        
        # 添加按钮区域
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # 添加模板按钮
        template_button = QPushButton("从模板添加")
        template_button.setObjectName("actionButton")
        template_button.clicked.connect(self.add_from_template)
        buttons_layout.addWidget(template_button)
        
        buttons_layout.addSpacing(10)
        
        # 添加确认按钮
        add_button = QPushButton("添加并计算")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.add_single_person)
        buttons_layout.addWidget(add_button)
        
        single_layout.addSpacing(15)
        single_layout.addLayout(buttons_layout)
        single_layout.addStretch()
        
        # 添加并显示新页面
        self.content_stack.addWidget(single_widget)
        self.content_stack.setCurrentWidget(single_widget)
        
        # 设置焦点
        self.single_person_name.setFocus()
    
    def show_people_list_context_menu(self, position):
        """人员列表右键菜单"""
        item = self.people_list.itemAt(position)
        if not item:
            return
            
        context_menu = QMenu(self)
        
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.remove_person_from_list(item))
        
        context_menu.addAction(delete_action)
        context_menu.exec(QCursor.pos())
    
    def remove_person_from_list(self, item):
        """从列表中删除人员"""
        row = self.people_list.row(item)
        person_name = item.text()
        
        # 从列表中删除项
        self.people_list.takeItem(row)
        
        # 从数据结构中删除
        person_names = self.calculations[self.current_calculation_id]["人员"]
        if person_name in person_names:
            person_names.remove(person_name)
            
        # 删除该人员的数据
        if person_name in self.people_data:
            del self.people_data[person_name]
            
        # 更新人数
        self.calculations[self.current_calculation_id]["人数"] = len(person_names)
        
        # 更新保存的数据
        self.calculations[self.current_calculation_id]["数据"] = self.people_data
    
    def add_new_person(self):
        """添加新人员到列表"""
        name = self.person_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "错误", "请输入人员名称！")
            return
            
        # 检查是否已存在同名人员
        person_names = self.calculations[self.current_calculation_id]["人员"]
        if name in person_names:
            QMessageBox.warning(self, "错误", f"已存在名为 '{name}' 的人员！")
            return
            
        # 添加到人员列表
        person_names.append(name)
        
        # 更新人数
        self.calculations[self.current_calculation_id]["人数"] = len(person_names)
        
        # 初始化该人员的数据
        if name not in self.people_data:
            self.people_data[name] = {"衣": 0, "食": 0, "住": 0, "行": 0, "总额": 0}
            
        # 保存最新数据
        self.calculations[self.current_calculation_id]["数据"] = self.people_data
        
        # 清空输入框并保持焦点
        self.person_name_input.clear()
        self.person_name_input.setFocus()
    
    def add_single_person(self):
        """添加单个人员并直接进入计算"""
        name = self.single_person_name.text().strip()
        if not name:
            QMessageBox.warning(self, "错误", "请输入人员名称！")
            return
            
        # 检查是否已存在同名人员
        person_names = self.calculations[self.current_calculation_id]["人员"]
        if name in person_names:
            QMessageBox.warning(self, "错误", f"已存在名为 '{name}' 的人员！")
            return
            
        # 添加到人员列表
        person_names.append(name)
        
        # 更新人数
        self.calculations[self.current_calculation_id]["人数"] = len(person_names)
        
        # 初始化人员数据
        if name not in self.people_data:
            self.people_data[name] = {"衣": 0, "食": 0, "住": 0, "行": 0, "总额": 0}
            
        # 直接创建人员计算页面
        self.setup_people_calculation()
    
    def setup_people_calculation(self):
        # 创建人员计算页面
        people_widget = QWidget()
        main_layout = QVBoxLayout()
        people_widget.setLayout(main_layout)
        
        # 添加标题
        title_layout = QHBoxLayout()
        back_button = QPushButton("返回")
        back_button.setObjectName("backButton")
        back_button.clicked.connect(self.show_main_screen)
        
        title_label = QLabel("消费计算")
        title_label.setObjectName("pageTitle")
        
        title_layout.addWidget(back_button)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        main_layout.addSpacing(15)
        
        # 创建上半部分内容（消费总览）和下半部分内容（人员列表）
        content_layout = QVBoxLayout()
        
        # 消费总览部分
        expense_summary = QWidget()
        expense_summary.setObjectName("expenseSummary")
        self.expense_layout = QVBoxLayout(expense_summary)
        
        content_layout.addWidget(expense_summary)
        content_layout.addSpacing(15)
        
        # 人员列表部分
        people_frame = QFrame()
        people_frame.setObjectName("peopleFrame")
        people_layout = QVBoxLayout(people_frame)
        
        # 添加标题栏
        people_header = QHBoxLayout()
        people_title = QLabel("人员列表")
        people_title.setObjectName("sectionTitle")
        
        add_person_button = QPushButton("添加人员")
        add_person_button.setObjectName("smallButton")
        add_person_button.clicked.connect(self.show_add_person_dialog)
        
        people_header.addWidget(people_title)
        people_header.addStretch()
        people_header.addWidget(add_person_button)
        people_layout.addLayout(people_header)
        
        # 添加人员列表
        self.people_list = QListWidget()
        self.people_list.setObjectName("peopleList")
        self.people_list.itemClicked.connect(self.on_person_clicked)
        
        people_layout.addWidget(self.people_list)
        
        content_layout.addWidget(people_frame)
        
        # 将内容布局添加到主布局
        main_layout.addLayout(content_layout)
        
        # 将页面添加到堆叠小部件
        self.content_stack.addWidget(people_widget)
        
        # 初始化人员总额标签列表
        self.person_total_labels = []

    def setup_styles(self):
        # 设置应用风格
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f7;
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                color: #333;
            }
            QLabel#appTitle {
                font-size: 24px;
                font-weight: bold;
                color: #333;
                padding: 10px;
            }
            QPushButton {
                background-color: #2979ff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
            QPushButton#smallButton {
                padding: 5px 10px;
                min-width: 60px;
                font-size: 12px;
            }
            QPushButton#backButton {
                background-color: #757575;
            }
            QPushButton#backButton:hover {
                background-color: #616161;
            }
            QPushButton#primaryButton {
                background-color: #2979ff;
                font-weight: bold;
            }
            QPushButton#deleteButton {
                background-color: #e53935;
            }
            QPushButton#deleteButton:hover {
                background-color: #d32f2f;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #2979ff;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                outline: none;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #2979ff;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QListWidget#historyList::item:alternate:selected {
                background-color: #2979ff;
                color: white;
            }
            QFrame#mainCard, QFrame#summaryFrame, QFrame#peopleFrame, QFrame#detailsFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
            QLabel#pageTitle, QLabel#sectionTitle {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
            QLabel#fieldHeader {
                font-weight: bold;
                color: #555;
            }
            QLabel#summaryLabel {
                font-size: 14px;
            }
            QLabel#summaryValue {
                font-size: 14px;
                font-weight: bold;
            }
            QLabel#totalLabel {
                font-size: 16px;
                font-weight: bold;
            }
            QLabel#totalValue, QLabel#finalTotalLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2979ff;
            }
            QFrame#totalFrame {
                background-color: #f5f5f7;
                border-radius: 4px;
                padding: 10px;
            }
            QFrame#separator {
                color: #e0e0e0;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QFrame#categoryItem {
                background-color: #f9f9f9;
                border-radius: 4px;
                padding: 5px;
                margin-bottom: 5px;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #2979ff;
                border: 1px solid #2979ff;
                border-radius: 3px;
            }
            QFrame#totalInfoFrame {
                background-color: #f5f5f7;
                border-radius: 4px;
                padding: a0px;
                margin-top: 10px;
            }
            QLabel#totalInfoLabel {
                font-size: 14px;
            }
        """)

    def show_add_person_dialog(self):
        """显示添加人员对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加人员")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        # 添加提示标签
        label = QLabel("请输入人员姓名:")
        layout.addWidget(label)
        
        # 添加输入框
        name_input = QLineEdit()
        name_input.setPlaceholderText("输入姓名")
        layout.addWidget(name_input)
        
        # 添加模板选择提示
        template_label = QLabel("或从模板中选择:")
        layout.addWidget(template_label)
        
        # 添加模板列表
        template_list = QListWidget()
        if hasattr(self, 'templates') and self.templates:
            for template in self.templates:
                template_list.addItem(template)
        layout.addWidget(template_list)
        
        # 添加按钮区域
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)
        
        # 连接信号
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        # 显示对话框
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # 获取输入的名称或选中的模板
            name = name_input.text().strip()
            selected_items = template_list.selectedItems()
            
            if selected_items and not name:
                # 使用选中的模板
                name = selected_items[0].text()
                
            # 添加人员
            if name:
                self.add_person_to_calculation(name)
            else:
                QMessageBox.warning(self, "错误", "请输入人员姓名或选择模板！")
    
    def delete_person(self, person_name):
        """从当前计算中删除人员"""
        if not self.current_calculation_id:
            return
            
        # 询问确认
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除 '{person_name}' 及其所有数据吗？", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 从人员数据中删除
                if person_name in self.people_data:
                    del self.people_data[person_name]
                
                # 从人员列表中删除
                calculation = self.calculations.get(self.current_calculation_id, {})
                person_list = calculation.get("人员", [])
                if person_name in person_list:
                    person_list.remove(person_name)
                
                # 更新计算数据
                calculation["数据"] = self.people_data
                
                # 保存更改
                self.save_current_calculation()
                
                # 更新界面
                self.load_people_list()
                self.update_all_totals()
                
            except Exception as e:
                print(f"删除人员时出错: {e}")
                QMessageBox.warning(self, "错误", f"删除人员时出错: {e}")
                
    def clear_content_pages(self):
        """清除内容页面"""
        # 保留主页面，移除其他页面
        while self.content_stack.count() > 1:
            widget = self.content_stack.widget(1)
            self.content_stack.removeWidget(widget)
            if widget:
                widget.deleteLater()
    
    def show_person_details(self, person_name):
        # 创建个人详情页面
        details_widget = QWidget()
        main_layout = QVBoxLayout()
        details_widget.setLayout(main_layout)
        
        # 添加标题
        title_layout = QHBoxLayout()
        back_button = QPushButton("返回")
        back_button.setObjectName("backButton")
        back_button.clicked.connect(self.return_from_details)
        
        title_label = QLabel(f"{person_name} - 消费详情")
        title_label.setObjectName("pageTitle")
        
        title_layout.addWidget(back_button)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        main_layout.addSpacing(15)
        
        # 添加消费类别
        details_frame = QFrame()
        details_frame.setObjectName("detailsFrame")
        details_layout = QVBoxLayout(details_frame)
        
        # 添加标题说明
        header_layout = QHBoxLayout()
        category_header = QLabel("消费类别")
        category_header.setObjectName("fieldHeader")
        category_header.setMinimumWidth(80)
        
        amount_header = QLabel("金额")
        amount_header.setObjectName("fieldHeader")
        amount_header.setMinimumWidth(80)
        
        reward_header = QLabel("标记为奖励")
        reward_header.setObjectName("fieldHeader")
        reward_header.setMinimumWidth(80)
        
        header_layout.addWidget(category_header)
        header_layout.addWidget(amount_header)
        header_layout.addWidget(reward_header)
        details_layout.addLayout(header_layout)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("separator")
        details_layout.addWidget(separator)
        details_layout.addSpacing(10)
        
        categories = ["衣", "食", "住", "行"]
        category_inputs = {}
        reward_checkboxes = {}
        
        for category in categories:
            category_frame = QFrame()
            category_frame.setObjectName("categoryItem")
            category_layout = QHBoxLayout(category_frame)
            
            category_label = QLabel(category)
            category_label.setObjectName("categoryLabel")
            category_label.setMinimumWidth(80)
            
            category_input = QLineEdit()
            category_input.setObjectName("amountInput")
            category_input.setPlaceholderText("输入金额")
            
            # 添加奖励复选框
            reward_checkbox = QCheckBox("奖励(2倍计算)")
            reward_checkbox.setObjectName("rewardCheckbox")
            
            # 如果有已保存的数据，显示在输入框中
            if person_name in self.people_data and category in self.people_data[person_name]:
                value = self.people_data[person_name][category]
                if value > 0:
                    category_input.setText(str(value))
                
                # 检查是否有奖励标记
                reward_key = f"{category}_奖励"
                if reward_key in self.people_data[person_name]:
                    reward_checkbox.setChecked(self.people_data[person_name][reward_key])
            
            category_layout.addWidget(category_label)
            category_layout.addWidget(category_input)
            category_layout.addWidget(reward_checkbox)
            
            details_layout.addWidget(category_frame)
            
            # 保存输入框和复选框的引用
            category_inputs[category] = category_input
            reward_checkboxes[category] = reward_checkbox
        
        # 添加总计信息
        total_frame = QFrame()
        total_frame.setObjectName("totalInfoFrame")
        total_layout = QVBoxLayout(total_frame)
        
        regular_total_label = QLabel("常规消费总计: 0.00")
        regular_total_label.setObjectName("totalInfoLabel")
        
        reward_total_label = QLabel("奖励总计: 0.00")
        reward_total_label.setObjectName("totalInfoLabel")
        
        final_total_label = QLabel("最终总计: 0.00")
        final_total_label.setObjectName("finalTotalLabel")
        
        total_layout.addWidget(regular_total_label)
        total_layout.addWidget(reward_total_label)
        total_layout.addWidget(final_total_label)
        
        details_layout.addSpacing(15)
        details_layout.addWidget(total_frame)
        
        main_layout.addWidget(details_frame)
        main_layout.addSpacing(15)
        
        # 添加按钮区域
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # 添加保存按钮
        save_button = QPushButton("保存")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(lambda: self.save_person_details(person_name, category_inputs, reward_checkboxes))
        buttons_layout.addWidget(save_button)
        
        main_layout.addLayout(buttons_layout)
        
        # 检查是否已经有详情页面，如果有则移除
        if self.content_stack.count() > 2:
            # 移除最后一个页面（即之前的详情页面）
            widget_to_remove = self.content_stack.widget(self.content_stack.count() - 1)
            self.content_stack.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()
        
        self.content_stack.addWidget(details_widget)
        self.content_stack.setCurrentWidget(details_widget)
        
        # 更新总计信息
        self.update_person_totals(person_name, category_inputs, reward_checkboxes, 
                                 regular_total_label, reward_total_label, final_total_label)
    
    def save_person_details(self, person_name, category_inputs, reward_checkboxes):
        # 确保该人员的数据字典已初始化
        if person_name not in self.people_data:
            self.people_data[person_name] = {}
        
        # 保存各个分类的金额
        for category, input_field in category_inputs.items():
            try:
                value = float(input_field.text()) if input_field.text() else 0
                self.people_data[person_name][category] = value
                
                # 保存奖励状态
                reward_key = f"{category}_奖励"
                self.people_data[person_name][reward_key] = reward_checkboxes[category].isChecked()
            except ValueError:
                QMessageBox.warning(self, "输入错误", f"请为 {category} 输入有效的数字金额")
                return
        
        # 保存当前计算
        self.save_current_calculation()
        
        # 更新总费用显示
        self.update_all_totals()
        
        # 返回到上一页
        self.return_from_details()
        
    def update_person_totals(self, person_name, category_inputs, reward_checkboxes, 
                           regular_total_label, reward_total_label, final_total_label):
        # 实时更新总计信息
        regular_total = 0
        reward_total = 0
        
        for category, input_field in category_inputs.items():
            try:
                value = float(input_field.text()) if input_field.text() else 0
                
                # 根据复选框状态判断是否为奖励
                if reward_checkboxes[category].isChecked():
                    reward_total += value
                else:
                    regular_total += value
            except ValueError:
                # 忽略无效输入
                continue
        
        # 奖励以2倍计算
        reward_amount = reward_total * 2
        final_total = regular_total + reward_amount
        
        # 更新标签
        regular_total_label.setText(f"常规消费总计: {regular_total:.2f}")
        reward_total_label.setText(f"奖励总计: {reward_total:.2f} (2倍计算为 {reward_amount:.2f})")
        final_total_label.setText(f"最终总计: {final_total:.2f}")
        
        # 为输入框添加信号连接
        for category, input_field in category_inputs.items():
            try:
                # 先断开旧连接以避免重复连接
                try:
                    input_field.textChanged.disconnect()
                except:
                    pass
                    
                # 添加新连接
                input_field.textChanged.connect(
                    lambda: self.update_person_totals(person_name, category_inputs, reward_checkboxes,
                                                   regular_total_label, reward_total_label, final_total_label)
                )
                
                # 为复选框添加信号连接
                try:
                    reward_checkboxes[category].toggled.disconnect()
                except:
                    pass
                    
                reward_checkboxes[category].toggled.connect(
                    lambda: self.update_person_totals(person_name, category_inputs, reward_checkboxes,
                                                   regular_total_label, reward_total_label, final_total_label)
                )
            except Exception as e:
                print(f"连接信号时出错: {e}")
    
    def return_from_details(self):
        """从详情页面返回到人员列表页面"""
        # 保存当前计算ID，避免页面重建时丢失
        calc_id = self.current_calculation_id
        
        # 获取当前详情页面
        current_widget = self.content_stack.currentWidget()
        
        # 如果没有当前计算ID，直接返回欢迎页
        if not calc_id:
            self.content_stack.setCurrentIndex(0)
            return
            
        # 获取人员计算页面的索引
        people_page_index = -1
        for i in range(self.content_stack.count()):
            widget = self.content_stack.widget(i)
            if widget and hasattr(widget, 'findChild'):
                if widget.findChild(QLabel, "totalLabel"):
                    people_page_index = i
                    break
        
        # 如果找不到人员页面，则默认使用索引1
        if people_page_index < 0:
            people_page_index = 1 if self.content_stack.count() > 1 else 0
            
        # 切换到人员页面
        if self.content_stack.count() > people_page_index:
            self.content_stack.setCurrentIndex(people_page_index)
        
        # 移除详情页面
        if current_widget and self.content_stack.indexOf(current_widget) != -1:
            self.content_stack.removeWidget(current_widget)
            current_widget.deleteLater()
        
        # 给UI一点时间处理页面切换
        QApplication.processEvents()
        
        # 重建人员计算页面，而不是尝试更新可能已删除的标签
        if calc_id == self.current_calculation_id:
            self.setup_people_calculation()
    
    def update_all_totals(self):
        # 计算各个支出类别的总额和每个人的总额
        total_by_category = {"衣": 0, "食": 0, "住": 0, "行": 0}
        total_by_person = {}
        grand_total = 0
        
        for person, data in self.people_data.items():
            person_regular_total = 0
            person_reward_total = 0
            
            for category in ["衣", "食", "住", "行"]:
                if category in data:
                    value = data[category]
                    
                    # 检查该类别是否被标记为奖励
                    reward_key = f"{category}_奖励"
                    is_reward = data.get(reward_key, False)
                    
                    if is_reward:
                        # 奖励项目以2倍计算
                        person_reward_total += value
                        # 奖励项目也计入类别总额
                        total_by_category[category] += value
                    else:
                        person_regular_total += value
                        total_by_category[category] += value
            
            # 计算含奖励的总额（奖励部分2倍计算）
            person_total = person_regular_total + (person_reward_total * 2)
            total_by_person[person] = person_total
            grand_total += person_total
            
            # 保存总额到人员数据中
            self.people_data[person]["总额"] = person_total
            self.people_data[person]["常规总额"] = person_regular_total
            self.people_data[person]["奖励总额"] = person_reward_total
        
        # 更新界面上的总额显示
        self.update_expense_display(total_by_category, total_by_person, grand_total)
    
    def update_expense_display(self, total_by_category, total_by_person, grand_total):
        """更新费用显示"""
        try:
            # 清除现有内容
            for i in reversed(range(self.expense_layout.count())):
                item = self.expense_layout.itemAt(i)
                if item.widget():
                    item.widget().deleteLater()
                self.expense_layout.removeItem(item)
            
            # 添加分类总额
            category_frame = QFrame()
            category_frame.setObjectName("summaryFrame")
            category_layout = QVBoxLayout(category_frame)
            
            category_title = QLabel("分类总额")
            category_title.setObjectName("sectionTitle")
            category_layout.addWidget(category_title)
            
            for category, total in total_by_category.items():
                item_layout = QHBoxLayout()
                item_label = QLabel(f"{category}:")
                item_label.setObjectName("summaryLabel")
                item_value = QLabel(f"{total:.2f}")
                item_value.setObjectName("summaryValue")
                
                item_layout.addWidget(item_label)
                item_layout.addStretch()
                item_layout.addWidget(item_value)
                
                category_layout.addLayout(item_layout)
            
            self.expense_layout.addWidget(category_frame)
            self.expense_layout.addSpacing(15)
            
            # 添加人员总额
            people_frame = QFrame()
            people_frame.setObjectName("summaryFrame")
            people_layout = QVBoxLayout(people_frame)
            
            people_title = QLabel("人员消费")
            people_title.setObjectName("sectionTitle")
            people_layout.addWidget(people_title)
            
            for person, total in total_by_person.items():
                item_layout = QHBoxLayout()
                
                # 获取常规总额和奖励总额
                regular_total = self.people_data[person].get("常规总额", 0)
                reward_total = self.people_data[person].get("奖励总额", 0)
                reward_amount = reward_total * 2
                
                person_button = QPushButton(person)
                person_button.setObjectName("personButton")
                person_button.clicked.connect(lambda checked, name=person: self.show_person_details(name))
                
                reward_info = ""
                if reward_total > 0:
                    reward_info = f" (常规: {regular_total:.2f}, 奖励: {reward_total:.2f}x2)"
                    
                total_value = QLabel(f"{total:.2f}{reward_info}")
                total_value.setObjectName("summaryValue")
                
                item_layout.addWidget(person_button)
                item_layout.addStretch()
                item_layout.addWidget(total_value)
                
                people_layout.addLayout(item_layout)
            
            self.expense_layout.addWidget(people_frame)
            self.expense_layout.addSpacing(15)
            
            # 添加总计
            total_frame = QFrame()
            total_frame.setObjectName("totalFrame")
            total_layout = QHBoxLayout(total_frame)
            
            total_label = QLabel("总计:")
            total_label.setObjectName("totalLabel")
            total_value = QLabel(f"{grand_total:.2f}")
            total_value.setObjectName("totalValue")
            
            total_layout.addWidget(total_label)
            total_layout.addStretch()
            total_layout.addWidget(total_value)
            
            self.expense_layout.addWidget(total_frame)
            
        except Exception as e:
            print(f"更新费用显示时出错: {e}")
    
    def save_current_calculation(self):
        """将当前计算保存到JSON文件"""
        if not self.current_calculation_id:
            return
            
        # 准备保存的数据
        calculation_data = self.calculations[self.current_calculation_id]
        
        # 生成文件名
        file_name = f"{self.current_calculation_id}.json"
        file_path = os.path.join(self.history_dir, file_name)
        
        # 保存到文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(calculation_data, f, ensure_ascii=False, indent=2)
            
            # 更新历史记录列表
            self.update_history_list()
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"无法保存计算数据: {str(e)}")
    
    def load_history(self):
        """加载所有历史记录"""
        try:
            # 清空当前历史记录
            self.calculations = {}
            self.history_list.clear()
            
            # 遍历history目录中的所有JSON文件
            if os.path.exists(self.history_dir):
                for file_name in os.listdir(self.history_dir):
                    if file_name.endswith('.json'):
                        file_path = os.path.join(self.history_dir, file_name)
                        calculation_id = file_name.replace('.json', '')
                        
                        with open(file_path, 'r', encoding='utf-8') as f:
                            calculation_data = json.load(f)
                            self.calculations[calculation_id] = calculation_data
            
            # 更新历史记录列表
            self.update_history_list()
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"无法加载历史记录: {str(e)}")
    
    def update_history_list(self):
        """更新历史记录列表显示"""
        self.history_list.clear()
        
        # 按创建时间排序（最新的在前面）
        sorted_calculations = sorted(
            self.calculations.items(),
            key=lambda x: x[1].get("创建时间", ""),
            reverse=True
        )
        
        for calc_id, calc_data in sorted_calculations:
            create_time = calc_data.get("创建时间", "未知时间")
            num_people = calc_data.get("人数", 0)
            item_text = f"{create_time} ({num_people}人)"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, calc_id)  # 存储计算ID
            self.history_list.addItem(item)
    
    def load_calculation_from_history(self, index):
        # 获取选中项的数据
        calculation_id = self.history_list.selectedItems()[0].data(Qt.ItemDataRole.UserRole)
        
        # 检查ID是否有效
        if calculation_id in self.calculations:
            # 重置UI以反映我们正在查看历史记录
            self.direct_add_mode = False
            
            # 保存当前计算ID
            old_calculation_id = self.current_calculation_id
            self.current_calculation_id = calculation_id
            
            try:
                # 从历史记录中获取数据
                calculation_data = self.calculations[calculation_id]
                
                # 深拷贝数据，防止意外修改原始数据
                import copy
                self.people_data = copy.deepcopy(calculation_data.get("数据", {}))
                
                # 在转到人员计算页面前加载人员列表
                self.load_people_list()
                
                # 更新费用显示
                self.update_all_totals()
                
                # 切换到人员计算页面
                if self.content_stack.count() <= 1:
                    # 如果还没创建过计算页面，创建一个新的
                    self.setup_people_calculation()
                
                # 确保UI显示正确页面
                self.content_stack.setCurrentIndex(1)
                
            except Exception as e:
                print(f"加载计算时出错: {e}")
                QMessageBox.warning(self, "错误", f"加载计算时出错: {e}")
                # 恢复之前的计算ID
                self.current_calculation_id = old_calculation_id
        else:
            QMessageBox.warning(self, "错误", "无法找到选中的计算数据")
            
    def load_people_list(self):
        """加载当前计算的人员列表"""
        # 清空当前列表
        self.people_list.clear()
        
        try:
            # 获取当前计算的人员
            person_names = list(self.people_data.keys())
            
            # 添加每个人员到列表
            for name in person_names:
                if name in self.people_data:
                    # 跳过特殊键
                    if name in ["总额", "常规总额", "奖励总额"]:
                        continue
                        
                    item = QListWidgetItem(name)
                    item.setData(Qt.ItemDataRole.UserRole, name)
                    self.people_list.addItem(item)
            
            # 设置右键菜单
            self.people_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.people_list.customContextMenuRequested.connect(self.show_people_list_menu)
            
        except Exception as e:
            print(f"加载人员列表时出错: {e}")
    
    def show_people_list_menu(self, position):
        """显示人员列表的右键菜单"""
        item = self.people_list.itemAt(position)
        if not item:
            return
            
        # 获取人员名称
        person_name = item.data(Qt.ItemDataRole.UserRole)
        
        # 创建菜单
        menu = QMenu()
        
        # 添加菜单项
        view_action = QAction("查看详情", self)
        view_action.triggered.connect(lambda: self.show_person_details(person_name))
        menu.addAction(view_action)
        
        menu.addSeparator()
        
        delete_action = QAction("删除人员", self)
        delete_action.triggered.connect(lambda: self.delete_person(person_name))
        menu.addAction(delete_action)
        
        # 显示菜单
        menu.exec(self.people_list.mapToGlobal(position))
    
    def on_person_clicked(self, item):
        """处理人员列表项点击事件"""
        person_name = item.data(Qt.ItemDataRole.UserRole)
        if person_name:
            self.show_person_details(person_name)
    
    def set_current_calculation(self, calculation_id=None):
        """设置当前计算并创建人员计算页面"""
        # 保存先前的计算ID
        old_calculation_id = self.current_calculation_id
        
        # 更新当前计算ID
        self.current_calculation_id = calculation_id
        
        # 清空人员数据
        self.people_data = {}
        
        # 如果有指定的计算ID
        if calculation_id is not None and calculation_id in self.calculations:
            # 深拷贝数据
            import copy
            self.people_data = copy.deepcopy(self.calculations[calculation_id].get("数据", {}))
        
        # 加载人员列表
        self.load_people_list()
        
        # 设置直接添加模式标志
        self.direct_add_mode = calculation_id is None
        
        try:
            # 调整界面，添加人员计算页面如果需要的话
            self.setup_people_calculation()
            
            # 更新总额显示
            self.update_all_totals()
            
            # 切换到人员计算页面
            self.content_stack.setCurrentIndex(1)
            
        except Exception as e:
            print(f"设置当前计算时出错: {e}")
            # 恢复旧的计算ID
            self.current_calculation_id = old_calculation_id
    
    def show_main_screen(self):
        """显示主屏幕"""
        self.content_stack.setCurrentIndex(0)
    
    def delete_selected_record(self):
        """删除选中的历史记录"""
        selected_items = self.history_list.selectedItems()
        
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要删除的记录")
            return
            
        # 提示确认删除
        item = selected_items[0]
        item_text = item.text()
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除记录 \"{item_text}\" 吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # 获取计算ID
        calc_id = item.data(Qt.ItemDataRole.UserRole)
        
        # 从文件系统中删除
        file_path = os.path.join(self.history_dir, f"{calc_id}.json")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                
            # 从内存中删除
            if calc_id in self.calculations:
                del self.calculations[calc_id]
                
            # 更新列表
            self.update_history_list()
            
            # 如果删除的是当前正在查看的记录，返回欢迎页面
            if calc_id == self.current_calculation_id:
                self.current_calculation_id = None
                self.clear_content_pages()
                self.content_stack.setCurrentIndex(0)
                
            QMessageBox.information(self, "成功", "记录已成功删除")
            
        except Exception as e:
            QMessageBox.warning(self, "删除失败", f"无法删除记录: {str(e)}")
    
    def load_templates(self):
        """加载所有模板"""
        try:
            # 清空当前模板
            self.templates = {}
            
            # 遍历templates目录中的所有JSON文件
            if os.path.exists(self.templates_dir):
                for file_name in os.listdir(self.templates_dir):
                    if file_name.endswith('.json'):
                        file_path = os.path.join(self.templates_dir, file_name)
                        template_name = file_name.replace('.json', '')
                        
                        with open(file_path, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                            self.templates[template_name] = template_data
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"无法加载模板: {str(e)}")
    
    def save_current_as_template(self):
        """将当前人员设置保存为模板"""
        # 检查是否有当前计算
        if not self.current_calculation_id or not self.calculations[self.current_calculation_id]["人员"]:
            QMessageBox.warning(self, "错误", "没有可保存的人员设置！")
            return
        
        # 获取模板名称
        template_name, ok = QInputDialog.getText(
            self, "保存模板", "请输入模板名称:", QLineEdit.EchoMode.Normal, "")
        
        if ok and template_name:
            # 检查名称合法性和是否已存在
            if not self.is_valid_filename(template_name):
                QMessageBox.warning(self, "错误", "模板名称包含非法字符！")
                return
                
            # 生成文件名
            file_name = f"{template_name}.json"
            file_path = os.path.join(self.templates_dir, file_name)
            
            # 检查是否已存在
            if os.path.exists(file_path):
                reply = QMessageBox.question(
                    self, "确认覆盖", 
                    f"模板 \"{template_name}\" 已存在！是否覆盖？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # 准备模板数据
            template_data = {
                "人员": self.calculations[self.current_calculation_id]["人员"],
                "人数": len(self.calculations[self.current_calculation_id]["人员"])
            }
            
            # 保存到文件
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, ensure_ascii=False, indent=2)
                
                # 更新模板字典
                self.templates[template_name] = template_data
                
                QMessageBox.information(self, "成功", f"模板 \"{template_name}\" 已保存！")
            except Exception as e:
                QMessageBox.warning(self, "保存失败", f"无法保存模板: {str(e)}")
    
    def load_from_template(self):
        """从模板加载人员设置"""
        # 检查是否有模板
        if not self.templates:
            QMessageBox.information(self, "提示", "没有可用的模板！")
            return
        
        # 创建模板选择对话框
        template_dialog = QDialog(self)
        template_dialog.setWindowTitle("选择模板")
        template_dialog.resize(300, 400)
        
        dialog_layout = QVBoxLayout(template_dialog)
        
        template_list = QListWidget()
        template_list.setAlternatingRowColors(True)
        
        # 添加模板项
        for name, data in self.templates.items():
            item_text = f"{name} ({data.get('人数', 0)}人)"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, name)
            template_list.addItem(item)
        
        dialog_layout.addWidget(template_list)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        
        delete_button = QPushButton("删除模板")
        delete_button.clicked.connect(lambda: self.delete_template(template_list))
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(template_dialog.accept)
        button_box.rejected.connect(template_dialog.reject)
        
        button_layout.addWidget(delete_button)
        button_layout.addStretch()
        button_layout.addWidget(button_box)
        
        dialog_layout.addLayout(button_layout)
        
        # 显示对话框
        if template_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_items = template_list.selectedItems()
            if selected_items:
                template_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
                self.apply_template(template_name)
    
    def delete_template(self, template_list):
        """删除选中的模板"""
        selected_items = template_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要删除的模板")
            return
            
        template_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除模板 \"{template_name}\" 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # 从文件系统中删除
        file_path = os.path.join(self.templates_dir, f"{template_name}.json")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                
            # 从内存中删除
            if template_name in self.templates:
                del self.templates[template_name]
                
            # 从列表中删除项
            row = template_list.row(selected_items[0])
            template_list.takeItem(row)
            
            QMessageBox.information(self, "成功", f"模板 \"{template_name}\" 已删除")
            
        except Exception as e:
            QMessageBox.warning(self, "删除失败", f"无法删除模板: {str(e)}")
    
    def apply_template(self, template_name):
        """应用选中的模板"""
        if template_name not in self.templates:
            return
            
        # 获取模板数据
        template_data = self.templates[template_name]
        person_names = template_data.get("人员", [])
        
        if not self.current_calculation_id:
            # 如果没有当前计算，创建一个新的
            self.current_calculation_id = datetime.now().strftime("%Y%m%d%H%M%S")
            self.calculations[self.current_calculation_id] = {
                "创建时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "人数": len(person_names),
                "人员": person_names.copy(),
                "数据": {}
            }
        else:
            # 将模板人员添加到当前计算
            current_names = self.calculations[self.current_calculation_id]["人员"]
            
            # 检查重复人员
            duplicates = []
            added_names = []
            
            for name in person_names:
                if name in current_names:
                    duplicates.append(name)
                else:
                    current_names.append(name)
                    added_names.append(name)
            
            # 更新人数
            self.calculations[self.current_calculation_id]["人数"] = len(current_names)
            
            # 初始化新添加的人员数据
            for name in added_names:
                if name not in self.people_data:
                    self.people_data[name] = {"衣": 0, "食": 0, "住": 0, "行": 0, "总额": 0}
            
            # 如果有重复人员，显示提示
            if duplicates:
                QMessageBox.information(
                    self, 
                    "部分人员已存在", 
                    f"以下人员已存在，不会重复添加：\n{', '.join(duplicates)}"
                )
        
        # 根据当前状态决定下一步操作
        if self.direct_add_mode or self.content_stack.currentIndex() > 1:
            # 如果是直接添加模式或已在计算页面，直接更新计算页面
            self.setup_people_calculation()
        else:
            # 否则，如果正在添加人员页面，更新列表
            for i in range(self.content_stack.count()):
                widget = self.content_stack.widget(i)
                if hasattr(widget, 'findChild') and widget.findChild(QListWidget, "peopleList"):
                    self.people_list.clear()
                    for name in self.calculations[self.current_calculation_id]["人员"]:
                        self.people_list.addItem(name)
                    break
    
    def add_from_template(self):
        """从模板添加人员"""
        # 如果没有当前计算，先创建
        if not self.current_calculation_id:
            self.current_calculation_id = datetime.now().strftime("%Y%m%d%H%M%S")
            self.calculations[self.current_calculation_id] = {
                "创建时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "人数": 0,
                "人员": [],
                "数据": {}
            }
            
        # 调用加载模板功能
        self.load_from_template()
    
    def is_valid_filename(self, filename):
        """检查文件名是否合法"""
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        return not any(char in filename for char in invalid_chars)

    def delete_record(self, item):
        """删除历史记录"""
        item_text = item.text()
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除记录 \"{item_text}\" 吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # 获取计算ID
        calc_id = item.data(Qt.ItemDataRole.UserRole)
        
        # 从文件系统中删除
        file_path = os.path.join(self.history_dir, f"{calc_id}.json")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                
            # 从内存中删除
            if calc_id in self.calculations:
                del self.calculations[calc_id]
                
            # 从列表中删除项
            row = self.history_list.row(item)
            if row >= 0:
                self.history_list.takeItem(row)
            
            # 如果删除的是当前正在查看的记录，返回欢迎页面
            if calc_id == self.current_calculation_id:
                self.current_calculation_id = None
                self.clear_content_pages()
                self.content_stack.setCurrentIndex(0)
                
            QMessageBox.information(self, "成功", "记录已成功删除")
            
        except Exception as e:
            QMessageBox.warning(self, "删除失败", f"无法删除记录: {str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 应用深色主题样式表
    dark_stylesheet = """
        QMainWindow, QDialog {
            background-color: #2b2b2b;
            color: #e0e0e0;
        }
        
        QWidget {
            background-color: #2b2b2b;
            color: #e0e0e0;
        }
        
        QLabel {
            color: #e0e0e0;
        }
        
        QLabel#pageTitle {
            font-size: 18px;
            font-weight: bold;
            color: #ffffff;
            padding: 5px;
        }
        
        QLabel#welcomeTitle {
            font-size: 24px;
            font-weight: bold;
            color: #ffffff;
            margin-bottom: 10px;
        }
        
        QLabel#welcomeDesc {
            font-size: 14px;
            color: #b0b0b0;
        }
        
        QLabel#sectionTitle {
            font-size: 14px;
            font-weight: bold;
            color: #ffffff;
            padding-bottom: 5px;
        }
        
        QLabel#personName {
            font-size: 14px;
            font-weight: bold;
            color: #ffffff;
        }
        
        QLabel#personTotal {
            color: #4fc3f7;
            font-weight: bold;
            min-width: 100px;
        }
        
        QLabel#totalLabel {
            font-size: 14px;
            font-weight: bold;
        }
        
        QLabel#grandTotal {
            font-size: 16px;
            font-weight: bold;
            color: #4fc3f7;
        }
        
        QLabel#categoryLabel {
            font-size: 14px;
            font-weight: bold;
        }
        
        QLabel#fieldLabel {
            font-size: 13px;
            font-weight: bold;
            color: #e0e0e0;
        }
        
        QPushButton {
            background-color: #424242;
            color: #e0e0e0;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        
        QPushButton:hover {
            background-color: #4a4a4a;
        }
        
        QPushButton:pressed {
            background-color: #383838;
        }
        
        QPushButton#primaryButton {
            background-color: #2196f3;
            color: white;
        }
        
        QPushButton#primaryButton:hover {
            background-color: #1e88e5;
        }
        
        QPushButton#primaryButton:pressed {
            background-color: #1976d2;
        }
        
        QPushButton#dangerButton {
            background-color: #f44336;
            color: white;
        }
        
        QPushButton#dangerButton:hover {
            background-color: #e53935;
        }
        
        QPushButton#dangerButton:pressed {
            background-color: #d32f2f;
        }
        
        QPushButton#detailButton {
            background-color: #5a5d5f;
            min-width: 80px;
        }
        
        QPushButton#backButton {
            background-color: #5a5d5f;
            min-width: 50px;
            padding: 5px 10px;
        }
        
        QPushButton#actionButton {
            background-color: #4caf50;
            color: white;
        }
        
        QPushButton#actionButton:hover {
            background-color: #43a047;
        }
        
        QPushButton#actionButton:pressed {
            background-color: #388e3c;
        }
        
        QToolButton {
            background-color: transparent;
            border: none;
            color: #bbbbbb;
            padding: 2px;
        }
        
        QToolButton:hover {
            color: #ffffff;
        }
        
        QToolButton#deleteButton {
            color: #e57373;
            font-size: 16px;
        }
        
        QToolButton#deleteButton:hover {
            color: #f44336;
        }
        
        QLineEdit {
            background-color: #3c3f41;
            color: #e0e0e0;
            border: 1px solid #5a5d5f;
            padding: 8px;
            border-radius: 4px;
        }
        
        QLineEdit:focus {
            border: 1px solid #2196f3;
        }
        
        QListWidget {
            background-color: #353535;
            color: #e0e0e0;
            border: 1px solid #454545;
            border-radius: 4px;
            outline: none;
            padding: 5px;
        }
        
        QListWidget::item {
            padding: 8px;
            border-bottom: 1px solid #454545;
        }
        
        QListWidget::item:selected {
            background-color: #2979ff;
            color: white;
        }
        
        QListWidget::item:hover:!selected {
            background-color: #454545;
        }
        
        QListWidget#historyList::item:alternate {
            background-color: #383838;
        }
        
        QListWidget#historyList::item:alternate:selected {
            background-color: #2979ff;
            color: white;
        }
        
        QRadioButton {
            color: #e0e0e0;
            spacing: 8px;
        }
        
        QRadioButton::indicator {
            width: 16px;
            height: 16px;
        }
        
        QRadioButton::indicator:unchecked {
            border: 2px solid #5a5d5f;
            border-radius: 8px;
            background-color: #353535;
        }
        
        QRadioButton::indicator:checked {
            border: 2px solid #2196f3;
            border-radius: 8px;
            background-color: #2196f3;
        }
        
        QFrame#sidebar {
            background-color: #252525;
            border-right: 1px solid #353535;
        }
        
        QFrame#separator {
            background-color: #353535;
            max-width: 1px;
        }
        
        QFrame#personCard {
            background-color: #353535;
            border-radius: 6px;
        }
        
        QFrame#totalFrame {
            background-color: #353535;
            border-radius: 6px;
            padding: 10px;
            margin-top: 10px;
        }
        
        QFrame#detailsFrame {
            background-color: #353535;
            border-radius: 6px;
            padding: 15px;
        }
        
        QFrame#categoryItem {
            padding: 5px;
            margin-bottom: 5px;
        }
        
        QFrame#selectionFrame, QFrame#inputFrame {
            background-color: #353535;
            border-radius: 6px;
            padding: 15px;
        }
        
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        
        QScrollBar:vertical {
            background-color: #2b2b2b;
            width: 12px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #5a5d5f;
            min-height: 20px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #6a6d6f;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background-color: #2b2b2b;
        }
        
        QMessageBox {
            background-color: #2b2b2b;
        }
        
        QMessageBox QLabel {
            color: #e0e0e0;
        }
        
        QMessageBox QPushButton {
            min-width: 80px;
            padding: 5px 10px;
        }
        
        QDialog {
            background-color: #2b2b2b;
        }
        
        QDialog QListWidget {
            min-height: 250px;
        }
    """
    app.setStyleSheet(dark_stylesheet)
    
    window = ExpenseCalculator()
    window.show()
    sys.exit(app.exec())