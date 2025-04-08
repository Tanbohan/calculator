import sys
import os
import json
import shutil
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QListWidget,
                           QStackedWidget, QLineEdit, QMessageBox, QListWidgetItem,
                           QFrame, QScrollArea, QSizePolicy, QSpacerItem, QMenu,
                           QButtonGroup, QRadioButton, QToolButton, QDialog, QDialogButtonBox,
                           QInputDialog, QCheckBox, QGridLayout, QTabWidget)
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
            
        # 创建垃圾桶文件夹
        self.trash_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trash")
        if not os.path.exists(self.trash_dir):
            os.makedirs(self.trash_dir)
            
        # 添加垃圾桶过期时间（7天）
        self.trash_expiry_days = 7
        
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
        
        # 添加垃圾桶按钮
        trash_button = QPushButton("垃圾桶")
        trash_button.setObjectName("trashButton")
        trash_button.clicked.connect(self.show_trash_contents)
        sidebar_layout.addWidget(trash_button)
        
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
        
        # 存储每个人的消费数据 (现在是投注数据)
        self.people_data = {}
        
        # 存储当前计算的人数 (保持用于显示)
        self.current_num_people = 0
        
        # 存储人员总额标签的引用 (可能不再需要)
        # self.person_total_labels = [] 
        
        # 预先初始化 people_list 和 results_layout (原 expense_layout)
        self.people_list = None
        self.results_layout = None # 重命名
        
        # 标记是否是直接添加模式
        self.direct_add_mode = False
        
        # 加载历史记录和模板
        self.load_history()
        self.load_templates()
        
        # 设置应用风格
        self.setup_styles()
        
    def history_item_clicked(self, item):
        """单击选中历史记录项"""
        # 通过样式显示选中状态
        for i in range(self.history_list.count()):
            self.history_list.item(i).setData(Qt.ItemDataRole.UserRole + 1, False)
        item.setData(Qt.ItemDataRole.UserRole + 1, True)
        self.history_list.update()
        
    def show_history_context_menu(self, position):
        """显示历史记录的上下文菜单"""
        menu = QMenu()
        
        load_action = menu.addAction("加载")
        rename_action = menu.addAction("重命名")
        delete_action = menu.addAction("删除")
        
        # 获取当前选中的项
        item = self.history_list.itemAt(position)
        if item is None:
            return
            
        # 显示菜单并获取选择的操作
        action = menu.exec(self.history_list.mapToGlobal(position))
        
        if action == load_action:
            self.load_calculation_from_history(item)
        elif action == rename_action:
            self.rename_history_record(item)
        elif action == delete_action:
            self.delete_record(item)
            
    def rename_history_record(self, item):
        """重命名历史记录"""
        if item is None:
            return
            
        # 获取当前记录ID和标题
        calc_id = item.data(Qt.ItemDataRole.UserRole)
        current_title = ""
        
        if calc_id in self.calculations:
            current_title = self.calculations[calc_id].get("标题", "")
        
        # 显示输入对话框
        new_title, ok = QInputDialog.getText(
            self, "重命名记录", "请输入新的记录名称:", 
            QLineEdit.EchoMode.Normal, current_title
        )
        
        # 如果用户取消或输入为空，直接返回
        if not ok or not new_title.strip():
            return
            
        # 更新计算数据
        if calc_id in self.calculations:
            self.calculations[calc_id]["标题"] = new_title.strip()
            
            # 保存到文件
            file_name = f"{calc_id}.json"
            file_path = os.path.join(self.history_dir, file_name)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.calculations[calc_id], f, ensure_ascii=False, indent=2)
                
                # 更新历史记录列表
                self.update_history_list()
                
                # 如果当前正在查看的是被重命名的记录，则更新标题
                if calc_id == self.current_calculation_id:
                    self.setWindowTitle(f"多事件计算器 - {new_title}")
                
                QMessageBox.information(self, "重命名成功", "记录已成功重命名。")
            except Exception as e:
                QMessageBox.warning(self, "重命名失败", f"重命名记录时出错: {str(e)}")
    
    def create_new_calculation(self):
        """创建新的计算"""
        try:
            # 清空当前人员数据
            self.people_data = {}
            
            # 创建新的计算记录 ID 和日期
            import time
            calculation_id = f"calc_{int(time.time())}"
            calc_date = time.strftime("%Y-%m-%d %H:%M:%S")
            default_title = f"计算 {calc_date}"
            
            # 弹出对话框让用户命名
            new_title, ok = QInputDialog.getText(
                self, "新建计算", "请输入记录名称:", 
                QLineEdit.EchoMode.Normal, default_title
            )
            
            # 如果用户取消，直接返回，不创建新计算
            if not ok:
                return
            
            # 如果输入为空，使用默认标题
            if not new_title.strip():
                record_title = default_title
            else:
                record_title = new_title.strip()
            
            # 创建新计算结构
            self.calculations[calculation_id] = {
                "日期": calc_date,
                "创建时间": calc_date,
                "标题": record_title, # 使用用户输入或默认标题
                "人员": [],
                "人数": 0,
                "数据": {},
                "开奖设置": {"中奖号码": None, "赔率": None}, # 初始化开奖设置
                "总览": {}, # 初始化总览
                "用户结果": {} # 初始化用户结果
            }
            
            # 设置当前计算ID
            self.current_calculation_id = calculation_id
            
            # 立即保存一次新记录，使其出现在历史列表中
            # 因为是新文件，is_existing_record 会是 False，不会弹确认框
            self.save_current_calculation()
            
            # 更新历史记录列表（现在应该能看到新记录了）
            self.update_history_list()
            
            # 设置为直接添加模式
            self.direct_add_mode = True
            
            # 创建人员计算页面
            self.setup_people_calculation()
            
            # 显示添加人员对话框
            self.show_add_person_dialog()
            
            # 切换到人员计算页面 (确保索引是正确的)
            calc_page_index = 1 # 假设计算页面总是在索引1
            if self.content_stack.count() > calc_page_index:
                self.content_stack.setCurrentIndex(calc_page_index)
            else:
                print("错误：无法切换到计算页面")
            
        except Exception as e:
            print(f"创建新计算时出错: {e}")
            QMessageBox.warning(self, "错误", f"创建新计算时出错: {e}")
    
    def add_person_to_calculation(self, person_name):
        # 确保当前计算ID有效
        if not self.current_calculation_id or self.current_calculation_id not in self.calculations:
            # 如果没有有效的当前计算，则创建一个新的
            self.create_new_calculation()
            # 新建计算后，current_calculation_id 会被设置
            if not self.current_calculation_id: # 再次检查以防万一
                QMessageBox.warning(self, "错误", "无法创建或找到当前计算记录")
                return

        # 获取当前计算数据
        calc_data = self.calculations[self.current_calculation_id]

        # 确保人员列表存在
        if "人员" not in calc_data:
            calc_data["人员"] = []
            
        # 确保数据字典存在
        if "数据" not in calc_data:
            calc_data["数据"] = {}

        # 检查人员是否已存在
        if person_name not in calc_data["人员"]:
            # 添加人员到列表
            calc_data["人员"].append(person_name)
            
            # 在数据字典中为新人员创建条目（如果不存在）
            if person_name not in calc_data["数据"]:
                calc_data["数据"][person_name] = {} # 初始化为空字典，表示没有投注
                
            # 更新人数
            calc_data["人数"] = len(calc_data["人员"])
            
            # 更新内存中的 people_data
            self.people_data = calc_data["数据"]
            
            # 刷新界面列表
            self.load_people_list()
            
            # 更新总额（如果需要）
            self.update_all_totals()
            
            # # 移除自动保存
            # self.save_current_calculation()
            
            print(f"人员 '{person_name}' 已添加到计算 '{self.current_calculation_id}'")
        else:
            QMessageBox.information(self, "提示", f"人员 '{person_name}' 已存在于当前计算中。")
        
        # 如果是直接添加模式，则显示详情页
        if self.direct_add_mode:
            self.show_person_details(person_name)
            self.direct_add_mode = False # 重置模式
    
    def show_add_person_dialog(self):
        """显示添加人员对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加人员")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        # 创建选项卡
        tabs = QTabWidget()
        
        # 创建单人添加选项卡
        single_person_tab = QWidget()
        single_layout = QVBoxLayout(single_person_tab)
        
        single_label = QLabel("输入人员姓名:")
        single_layout.addWidget(single_label)
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("输入姓名")
        single_layout.addWidget(name_input)
        
        single_layout.addStretch()
        
        # 创建模板选项卡
        template_tab = QWidget()
        template_layout = QVBoxLayout(template_tab)
        
        template_label = QLabel("选择要应用的模板:")
        template_layout.addWidget(template_label)
        
        template_list = QListWidget()
        if hasattr(self, 'templates') and self.templates:
            for template_name, template_data in self.templates.items():
                person_count = template_data.get("人数", 0)
                item_text = f"{template_name} ({person_count}人)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, template_name)
                template_list.addItem(item)
        template_layout.addWidget(template_list)
        
        # 添加选项卡到选项卡控件
        tabs.addTab(single_person_tab, "添加单人")
        tabs.addTab(template_tab, "使用模板")
        
        # 添加选项卡控件到主布局
        layout.addWidget(tabs)
        
        # 添加按钮区域
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)
        
        # 连接信号
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        # 显示对话框
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            current_tab = tabs.currentIndex()
            
            if current_tab == 0:  # 单人添加选项卡
                name = name_input.text().strip()
                if name:
                    self.add_person_to_calculation(name)
                else:
                    QMessageBox.warning(self, "错误", "请输入人员姓名！")
            else:  # 模板选项卡
                selected_items = template_list.selectedItems()
                if selected_items:
                    template_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
                    self.apply_template(template_name)
                else:
                    QMessageBox.warning(self, "错误", "请选择一个模板！")
    
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
            self.people_data[name] = {} # 初始化为空字典
        
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
            self.people_data[name] = {} # 初始化为空字典
        
        # 直接创建人员计算页面
        self.setup_people_calculation()
    
    def setup_people_calculation(self):
        # 创建人员计算页面
        people_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        people_widget.setLayout(main_layout)
        
        # 添加标题
        title_layout = QHBoxLayout()
        back_button = QPushButton("返回")
        back_button.setObjectName("backButton")
        back_button.clicked.connect(self.show_main_screen)
        
        # 修改标题为投注计算
        title_label = QLabel("投注计算") 
        title_label.setObjectName("pageTitle")
        
        title_layout.addWidget(back_button)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        main_layout.addSpacing(10)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # 创建滚动内容窗口部件
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(15)
        
        # 开奖设置区域 (原奖励设置)
        prize_frame = QFrame()
        prize_frame.setObjectName("summaryFrame")
        prize_layout = QVBoxLayout(prize_frame)
        
        prize_title = QLabel("开奖设置")
        prize_title.setObjectName("sectionTitle")
        prize_layout.addWidget(prize_title)
        
        # 添加中奖号码和赔率输入
        prize_input_layout = QHBoxLayout()
        
        winning_number_label = QLabel("中奖号码 (1-49):")
        self.winning_number_input = QLineEdit()
        self.winning_number_input.setPlaceholderText("输入数字")
        self.winning_number_input.setMaximumWidth(100)
        self.winning_number_input.textChanged.connect(self.save_prize_settings) # 连接信号
        
        payout_rate_label = QLabel("赔率:")
        self.payout_rate_input = QLineEdit()
        self.payout_rate_input.setPlaceholderText("输入倍数")
        self.payout_rate_input.setMaximumWidth(100)
        self.payout_rate_input.textChanged.connect(self.save_prize_settings) # 连接信号
        
        prize_input_layout.addWidget(winning_number_label)
        prize_input_layout.addWidget(self.winning_number_input)
        prize_input_layout.addSpacing(20)
        prize_input_layout.addWidget(payout_rate_label)
        prize_input_layout.addWidget(self.payout_rate_input)
        prize_input_layout.addStretch()
        
        prize_layout.addLayout(prize_input_layout)
        
        # 恢复保存的设置
        if self.current_calculation_id in self.calculations:
            calc_data = self.calculations[self.current_calculation_id]
            prize_settings = calc_data.get("开奖设置", {})
            self.winning_number_input.setText(str(prize_settings.get("中奖号码", "")))
            self.payout_rate_input.setText(str(prize_settings.get("赔率", "")))
            
        content_layout.addWidget(prize_frame)
        
        # 结果总览部分 (原消费总览)
        # 保存对结果总览QWidget的引用
        self.results_summary_widget = QWidget() 
        self.results_summary_widget.setObjectName("resultsSummary")
        self.results_layout = QVBoxLayout(self.results_summary_widget) # 将布局应用到QWidget
        
        content_layout.addWidget(self.results_summary_widget) # 将QWidget添加到主内容布局
        
        # 用户列表部分 (原人员列表)
        people_frame = QFrame()
        people_frame.setObjectName("peopleFrame")
        people_layout = QVBoxLayout(people_frame)
        
        # 添加标题栏
        people_header = QHBoxLayout()
        people_title = QLabel("用户列表") # 修改标题
        people_title.setObjectName("sectionTitle")
        
        add_person_button = QPushButton("添加用户") # 修改按钮文本
        add_person_button.setObjectName("smallButton")
        add_person_button.clicked.connect(self.show_add_person_dialog)
        
        people_header.addWidget(people_title)
        people_header.addStretch()
        people_header.addWidget(add_person_button)
        people_layout.addLayout(people_header)
        
        # 添加用户列表
        self.people_list = QListWidget()
        self.people_list.setObjectName("peopleList")
        self.people_list.itemClicked.connect(self.on_person_clicked)
        self.people_list.setMinimumHeight(250)
        
        people_layout.addWidget(self.people_list)
        
        content_layout.addWidget(people_frame)
        
        # 设置滚动区域的内容
        scroll_area.setWidget(scroll_content)
        
        # 将滚动区域添加到主布局，并设置拉伸因子
        main_layout.addWidget(scroll_area, 1)
        
        # 将页面添加到堆叠小部件
        # 检查是否已有计算页面，避免重复添加
        existing_widget = None
        for i in range(self.content_stack.count()):
             widget = self.content_stack.widget(i)
             # 假设计算页面可以通过查找特定对象名称来识别
             if widget.findChild(QLabel, "pageTitle") and widget.findChild(QLabel, "pageTitle").text() == "投注计算":
                 existing_widget = widget
                 break
        
        if existing_widget:
             # 如果已存在，先移除旧的
             self.content_stack.removeWidget(existing_widget)
             existing_widget.deleteLater()
             
        self.content_stack.addWidget(people_widget)
        
        # 初始化人员总额标签列表 (可能不再需要或需要修改用途)
        # self.person_total_labels = [] 
        
        # 加载人员列表
        self.load_people_list()
        
        # 更新费用显示
        self.update_all_totals()
    
    def setup_styles(self):
        # 设置应用风格
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
                font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
            QLabel {
                color: #e0e0e0;
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
            QPushButton#dangerButton {
                background-color: #e53935;
                color: white;
            }
            QPushButton#dangerButton:hover {
                background-color: #d32f2f;
            }
            QPushButton#personButton {
                background-color: #424242;
                color: #ffffff;
                text-align: left;
            }
            QPushButton#personButton:hover {
                background-color: #4a4a4a;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #5a5d5f;
                border-radius: 4px;
                background-color: #3c3f41;
                color: #e0e0e0;
            }
            QLineEdit:focus {
                border: 1px solid #2979ff;
            }
            QListWidget {
                background-color: #353535;
                border: 1px solid #454545;
                border-radius: 4px;
                outline: none;
                padding: 5px;
                color: #e0e0e0;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #454545;
                color: #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #2979ff;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #454545;
            }
            QListWidget#historyList::item:alternate {
                background-color: #383838;
                color: #e0e0e0;
            }
            QListWidget#historyList::item:alternate:selected {
                background-color: #2979ff;
                color: white;
            }
            QFrame#mainCard, QFrame#summaryFrame, QFrame#peopleFrame, QFrame#detailsFrame {
                background-color: #353535;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #454545;
            }
            QLabel#pageTitle, QLabel#sectionTitle {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
                margin-bottom: 10px;
            }
            QLabel#fieldHeader {
                font-weight: bold;
                color: #e0e0e0;
            }
            QLabel#summaryLabel {
                font-size: 14px;
                color: #e0e0e0;
            }
            QLabel#summaryValue {
                font-size: 14px;
                font-weight: bold;
                color: #e0e0e0;
            }
            QLabel#totalLabel {
                font-size: 16px;
                font-weight: bold;
                color: #e0e0e0;
            }
            QLabel#totalValue, QLabel#finalTotalLabel {
                font-size: 16px;
                font-weight: bold;
                color: #4fc3f7; 
            }
            QLabel#categoryLabel {
                font-size: 14px;
                font-weight: bold;
                color: #e0e0e0;
            }
            QLabel#categoryLabelReward {
                font-size: 14px;
                font-weight: bold;
                color: #4fc3f7;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 14px;
                margin: 0px;
                border-radius: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #5a5d5f;
                min-height: 30px;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6a6d6f;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QFrame#categoryItem {
                background-color: #3a3a3a;
                border-radius: 4px;
                padding: 5px;
                margin-bottom: 5px;
            }
            QCheckBox {
                spacing: 5px;
                color: #e0e0e0;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #3c3f41;
                border: 1px solid #5a5d5f;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #2979ff;
                border: 1px solid #2979ff;
                border-radius: 3px;
            }
            QFrame#totalInfoFrame {
                background-color: #3a3a3a;
                border-radius: 4px;
                padding: 10px;
                margin-top: 10px;
            }
            QLabel#totalInfoLabel {
                font-size: 14px;
                color: #e0e0e0;
            }
        """)

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
        main_layout.setContentsMargins(10, 10, 10, 10)
        details_widget.setLayout(main_layout)
        
        # 添加标题
        title_layout = QHBoxLayout()
        back_button = QPushButton("返回")
        back_button.setObjectName("backButton")
        back_button.clicked.connect(self.return_from_details)
        
        # 修改标题为用户投注详情
        title_label = QLabel(f"{person_name} - 用户投注详情") 
        title_label.setObjectName("pageTitle")
        
        title_layout.addWidget(back_button)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        main_layout.addSpacing(10)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # 创建滚动内容窗口部件
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        
        # 添加投注数字区域
        details_frame = QFrame()
        details_frame.setObjectName("detailsFrame")
        details_layout = QVBoxLayout(details_frame)
        
        # 创建网格布局来显示数字输入框 (7列 x 7行)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        category_inputs = {}
        
        # 生成1-49的输入框
        for i in range(1, 50):
            number_label = QLabel(str(i))
            number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            number_label.setMinimumWidth(30)
            
            number_input = QLineEdit()
            number_input.setObjectName(f"numberInput_{i}")
            number_input.setPlaceholderText("金额")
            number_input.setMaximumWidth(80)
            
            # 获取当前用户的投注数据
            # 使用 self.people_data (它应该在 update_all_totals 后被更新为清理过的数据)
            user_bets = self.people_data.get(person_name, {})
            bet_amount = user_bets.get(str(i)) # 获取金额，可能是数字或None
            
            # 如果有投注金额，显示在输入框中，否则保持为空
            if bet_amount is not None and bet_amount > 0:
                number_input.setText(f"{bet_amount:.2f}") # 格式化显示
            # else: # 如果是 None 或 0，输入框默认就是空的，不需要setText('')
            
            # 计算行列位置
            row = (i - 1) // 7
            col = (i - 1) % 7
            
            # 添加到网格布局
            grid_layout.addWidget(number_label, row, col * 2) # 标签占一列
            grid_layout.addWidget(number_input, row, col * 2 + 1) # 输入框占一列
            
            # 保存输入框引用，用数字字符串作为键
            category_inputs[str(i)] = number_input
            
        details_layout.addLayout(grid_layout)
        details_layout.addSpacing(15)
        
        # 添加总计信息区域
        total_frame = QFrame()
        total_frame.setObjectName("totalInfoFrame")
        total_layout = QVBoxLayout(total_frame)
        
        # 显示投注总额和中奖金额（将在update_person_total中更新）
        total_bet_label = QLabel("投注总额: 0.00")
        total_bet_label.setObjectName("totalBetLabel") # 新的对象名
        
        winning_amount_label = QLabel("中奖金额: 0.00")
        winning_amount_label.setObjectName("winningAmountLabel") # 新的对象名
        
        total_layout.addWidget(total_bet_label)
        total_layout.addWidget(winning_amount_label)
        
        details_layout.addWidget(total_frame)
        
        # 添加详情框架到滚动区域内容
        scroll_layout.addWidget(details_frame)
        
        # 设置滚动区域内容
        scroll_area.setWidget(scroll_content)
        
        # 添加滚动区域到主布局
        main_layout.addWidget(scroll_area, 1)
        
        # 添加按钮区域
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # 添加保存按钮
        save_button = QPushButton("保存")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(lambda: self.save_person_details(person_name, category_inputs)) # 传递 category_inputs
        buttons_layout.addWidget(save_button)
        
        main_layout.addLayout(buttons_layout)
        
        # 检查并移除旧的详情页
        if self.content_stack.count() > 2:
            widget_to_remove = self.content_stack.widget(self.content_stack.count() - 1)
            self.content_stack.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()
        
        # 添加新页面并切换
        self.content_stack.addWidget(details_widget)
        self.content_stack.setCurrentWidget(details_widget)
        
        # 计算并更新个人总计
        self.update_person_total(person_name, category_inputs, total_bet_label, winning_amount_label)
    
    def update_person_total(self, person_name, category_inputs, total_bet_label, winning_amount_label):
        """实时更新用户投注详情页的总计信息"""
        total_bet = 0.0
        winning_amount = 0.0
        
        # 获取当前记录的开奖设置
        prize_settings = {}
        if self.current_calculation_id in self.calculations:
            prize_settings = self.calculations[self.current_calculation_id].get("开奖设置", {})
            
        winning_number = prize_settings.get("中奖号码")
        payout_rate = prize_settings.get("赔率")
        
        # 检查开奖设置是否有效
        can_calculate_winnings = winning_number is not None and payout_rate is not None and payout_rate > 0
        
        # 计算投注总额和中奖金额
        for number_str, input_field in category_inputs.items():
            try:
                value_text = input_field.text().strip()
                if not value_text: # 如果输入为空，跳过
                    continue
                    
                bet_value = float(value_text)
                if bet_value <= 0:
                    continue
                    
                # 累加投注总额
                total_bet += bet_value
                
                # 如果开奖设置有效且当前数字是中奖号码，计算奖金
                if can_calculate_winnings and number_str == str(winning_number):
                    winning_amount += bet_value * payout_rate
                    
            except ValueError:
                # 忽略无效输入
                pass
        
        # 更新标签显示
        total_bet_label.setText(f"投注总额: {total_bet:.2f}")
        winning_amount_label.setText(f"中奖金额: {winning_amount:.2f}")
        
        # 为输入框添加信号连接（确保只连接一次或先断开再连接）
        for number_str, input_field in category_inputs.items():
            try:
                # 先尝试断开可能存在的旧连接
                input_field.textChanged.disconnect()
            except TypeError: # 如果没有连接，会抛出TypeError
                pass
            except Exception as e:
                print(f"断开信号时出错 ({number_str}): {e}")
            
            try:
                # 添加新连接
                input_field.textChanged.connect(
                    lambda: self.update_person_total(person_name, category_inputs, total_bet_label, winning_amount_label)
                )
            except Exception as e:
                print(f"连接信号时出错 ({number_str}): {e}")
    
    def return_from_details(self):
        """从详情页面返回到主计算页面"""
        # 获取当前详情页面 widget
        current_widget = self.content_stack.currentWidget()
        current_index = self.content_stack.currentIndex()
        
        # 主计算页面通常在索引 1 (索引 0 是欢迎页)
        main_calc_page_index = 1
        
        # 检查索引是否有效
        if self.content_stack.count() > main_calc_page_index:
            self.content_stack.setCurrentIndex(main_calc_page_index)
        else:
            # 如果主计算页面不存在（异常情况），则返回欢迎页
            self.content_stack.setCurrentIndex(0)
            
        # 移除详情页面 (通常是索引大于1的页面)
        if current_index > main_calc_page_index and current_widget:
            self.content_stack.removeWidget(current_widget)
            current_widget.deleteLater()
            
        # 返回后，再次更新主计算页面的显示以确保反映最新数据
        self.update_all_totals()
    
    def update_all_totals(self):
        """更新所有用户的总投注额、总中奖金额和商家盈亏"""
        try:
            total_bets_all_users = 0.0
            total_winnings_all_users = 0.0
            
            # 获取当前记录的开奖设置
            prize_settings = {}
            if self.current_calculation_id in self.calculations:
                prize_settings = self.calculations[self.current_calculation_id].get("开奖设置", {})
            
            winning_number = prize_settings.get("中奖号码")
            payout_rate = prize_settings.get("赔率")
            can_calculate_winnings = winning_number is not None and payout_rate is not None and payout_rate > 0
            
            # 用于存储每个用户的总投注和中奖金额
            results_by_person = {}
            
            # 获取当前计算的人员列表和干净的投注数据
            current_people = []
            clean_people_data = {}
            if self.current_calculation_id in self.calculations:
                calc_data = self.calculations[self.current_calculation_id]
                current_people = calc_data.get("人员", [])
                # 确保只处理当前记录中应该存在的用户数据
                all_data = calc_data.get("数据", {})
                for person in current_people:
                    if person in all_data and isinstance(all_data[person], dict):
                        # 清理每个用户的投注，只保留数字键
                        user_bets = {k: v for k, v in all_data[person].items() 
                                     if k.isdigit() and isinstance(v, (int, float)) and v > 0}
                        if user_bets: # 只添加有投注的用户
                           clean_people_data[person] = user_bets
            
            # 使用清理后的数据进行计算
            for person, bets_data in clean_people_data.items():
                person_total_bet = 0.0
                person_total_winnings = 0.0
                
                # 计算该用户的总投注和中奖金额
                for number_str, bet_amount in bets_data.items(): 
                    person_total_bet += bet_amount
                    # 如果开奖且该号码中奖
                    if can_calculate_winnings and number_str == str(winning_number):
                        person_total_winnings += bet_amount * payout_rate
                
                # 保存该用户的结果
                results_by_person[person] = {
                    "投注总额": person_total_bet,
                    "中奖金额": person_total_winnings
                }
                
                # 累加全局总计
                total_bets_all_users += person_total_bet
                total_winnings_all_users += person_total_winnings
                
            # 计算商家盈亏
            merchant_profit = total_bets_all_users - total_winnings_all_users
            
            # 更新计算数据中的总览信息和清理后的用户数据
            if self.current_calculation_id in self.calculations:
                summary_data = {
                    "总投注额": total_bets_all_users,
                    "总派彩额": total_winnings_all_users,
                    "商家盈亏": merchant_profit
                }
                # 更新主计算字典
                self.calculations[self.current_calculation_id]["总览"] = summary_data
                self.calculations[self.current_calculation_id]["用户结果"] = results_by_person
                # 将清理后的数据写回 "数据"，确保一致性
                self.calculations[self.current_calculation_id]["数据"] = clean_people_data
                # 更新内存中的 people_data 以便详情页使用
                self.people_data = clean_people_data 
            
            # 更新界面显示
            if self.results_layout is not None and self.content_stack.currentIndex() == 1:
                self.update_results_display(results_by_person, total_bets_all_users, total_winnings_all_users, merchant_profit)
            else:
                print("Skipping results UI update: Layout not ready or page not visible.")
            
        except Exception as e:
            print(f"更新总额时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def save_prize_settings(self):
        """保存开奖设置（中奖号码和赔率）到内存，并更新显示"""
        if not self.current_calculation_id:
            return
            
        try:
            winning_number_text = self.winning_number_input.text().strip()
            payout_rate_text = self.payout_rate_input.text().strip()
            
            winning_number = None
            if winning_number_text.isdigit():
                num = int(winning_number_text)
                if 1 <= num <= 49:
                    winning_number = num
                else:
                    pass # 忽略无效输入
            
            payout_rate = None
            if payout_rate_text:
                try:
                    rate = float(payout_rate_text)
                    if rate > 0:
                        payout_rate = rate
                    else:
                        pass # 赔率必须为正数
                except ValueError:
                    pass # 赔率必须是数字
            
            prize_settings = {
                "中奖号码": winning_number,
                "赔率": payout_rate
            }
            
            # 仅保存到当前计算数据中 (内存)
            if self.current_calculation_id in self.calculations:
                self.calculations[self.current_calculation_id]["开奖设置"] = prize_settings
                
                # 触发总额更新，因为赔率可能影响结果
                self.update_all_totals()
                
        except Exception as e:
            print(f"保存开奖设置时出错: {e}")
    
    def save_current_calculation(self):
        """保存当前计算"""
        if not self.current_calculation_id:
            return
            
        # 获取历史记录的原始文件路径
        file_name = f"{self.current_calculation_id}.json"
        file_path = os.path.join(self.history_dir, file_name)
        
        # 判断是否是在修改历史记录（而不是新建的计算）
        is_existing_record = os.path.exists(file_path)
        
        # 判断是否是刚刚创建的新记录
        is_new_record = False
        if self.current_calculation_id in self.calculations:
            created_time_str = self.calculations[self.current_calculation_id].get("创建时间", "")
            if created_time_str:
                try:
                    created_time = datetime.strptime(created_time_str, "%Y-%m-%d %H:%M:%S")
                    # 如果创建时间在最近两分钟内，认为是新记录
                    is_new_record = (datetime.now() - created_time).total_seconds() < 120
                except Exception as e:
                    print(f"解析创建时间时出错: {e}")
        
        # 如果是修改现有历史记录(且不是新记录)，弹出确认对话框
        if is_existing_record and not is_new_record:
            reply = QMessageBox.question(
                self, "确认保存", 
                "您正在修改历史记录。确定要保存更改吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return # 用户取消保存
        
        # 将旧版本备份到垃圾桶（如果是修改现有记录）
        if is_existing_record:
            try:
                # 创建备份文件名，包含时间戳以避免冲突
                backup_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                backup_file_name = f"{self.current_calculation_id}_{backup_timestamp}.json"
                backup_path = os.path.join(self.trash_dir, backup_file_name)
                
                # 复制原文件到垃圾桶
                shutil.copy2(file_path, backup_path)
                
                # 清理过期的垃圾文件
                self.clean_trash()
            except Exception as e:
                print(f"备份历史记录时出错: {e}")
        
        # 更新人数信息
        if self.current_calculation_id in self.calculations:
            # 确保从人员列表计算人数
            if "人员" in self.calculations[self.current_calculation_id]:
               self.calculations[self.current_calculation_id]["人数"] = len(self.calculations[self.current_calculation_id]["人员"])
            else:
               self.calculations[self.current_calculation_id]["人数"] = 0 # 如果没有人员列表，则为0

        # 保存到文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.calculations[self.current_calculation_id], f, ensure_ascii=False, indent=2)
            
            # 更新历史记录列表
            self.update_history_list()
            
            # 显示保存成功提示（对于新记录或首次创建的记录，不显示提示）
            if not is_new_record:
                QMessageBox.information(self, "保存成功", "计算数据已成功保存。")
                
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"无法保存计算数据: {str(e)}")
    
    def show_restore_notification(self, saved_file):
        """显示撤回保存的通知"""
        msg = QMessageBox(self)
        msg.setWindowTitle("保存成功")
        msg.setText("历史记录已成功更新。")
        msg.setInformativeText("您可以在7天内撤回此更改。")
        
        # 添加撤回按钮
        restore_button = msg.addButton("撤回更改", QMessageBox.ButtonRole.ActionRole)
        close_button = msg.addButton("关闭", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        # 如果点击了撤回按钮
        if msg.clickedButton() == restore_button:
            self.restore_from_trash(saved_file)
    
    def clean_trash(self):
        """清理超过过期时间的垃圾桶文件"""
        try:
            # 计算过期时间
            expiry_date = datetime.now() - timedelta(days=self.trash_expiry_days)
            expiry_timestamp = expiry_date.timestamp()
            
            # 遍历垃圾桶中的所有文件
            if os.path.exists(self.trash_dir):
                for file_name in os.listdir(self.trash_dir):
                    file_path = os.path.join(self.trash_dir, file_name)
                    
                    # 获取文件的最后修改时间
                    file_mod_time = os.path.getmtime(file_path)
                    
                    # 如果文件超过过期时间，则删除
                    if file_mod_time < expiry_timestamp:
                        os.remove(file_path)
                        print(f"删除过期垃圾文件: {file_name}")
        except Exception as e:
            print(f"清理垃圾桶时出错: {e}")
    
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
        """更新历史记录列表"""
        # 清空列表
        self.history_list.clear()
        
        # 历史记录列表
        history_items = []
        
        # 遍历history文件夹
        for file in os.listdir(self.history_dir):
            if file.endswith(".json"):
                # 构建完整路径
                file_path = os.path.join(self.history_dir, file)
                
                # 读取文件内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # 获取计算ID
                    calc_id = file.replace(".json", "")
                    
                    # 获取日期和标题
                    date = data.get("日期", "未知日期")
                    title = data.get("标题", f"计算 {date}")
                    # 移除人数显示
                    # people_count = data.get("人数", len(data.get("人员", [])))
                    
                    # 将数据添加到计算字典
                    self.calculations[calc_id] = data
                    
                    # 创建列表项，只显示标题
                    display_text = title
                    
                    # 添加到历史记录列表
                    history_items.append((date, calc_id, display_text))
                    
                except Exception as e:
                    print(f"读取历史记录文件 {file} 时出错: {e}")
        
        # 按日期排序（最新的在前面）
        history_items.sort(key=lambda x: x[0], reverse=True)
        
        # 将排序后的项添加到列表中
        for _, calc_id, display_text in history_items:
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, calc_id)
            self.history_list.addItem(item)
    
    def load_calculation_from_history(self, item):
        # 获取选中项的数据
        # 如果 item 是 QListWidgetItem，则从中获取数据
        if isinstance(item, QListWidgetItem):
            calculation_id = item.data(Qt.ItemDataRole.UserRole)
        else:
             # 如果传入的是索引或其他，尝试获取当前选中项 (作为后备)
            selected_items = self.history_list.selectedItems()
            if not selected_items:
                 QMessageBox.warning(self, "错误", "没有选中的历史记录项")
                 return
            calculation_id = selected_items[0].data(Qt.ItemDataRole.UserRole)

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
                
                # 每次切换历史记录时，清除旧的内容页面 (除了欢迎页)
                while self.content_stack.count() > 1:
                     widget = self.content_stack.widget(1)
                     self.content_stack.removeWidget(widget)
                     widget.deleteLater()

                # 重新创建计算页面 (这会设置 self.results_layout)
                self.setup_people_calculation()
                
                # 先切换到计算页面
                calc_page_index = 1 # 假设计算页面总是在索引 1
                if self.content_stack.count() > calc_page_index:
                    self.content_stack.setCurrentIndex(calc_page_index)
                    # 强制处理事件，确保页面切换完成
                    QApplication.processEvents()
                else:
                    print("错误：无法切换到计算页面")
                    # 如果无法切换，可能需要回滚或显示错误
                    self.current_calculation_id = old_calculation_id # 恢复ID
                    return # 提前退出
                
                # 页面切换事件处理后，再更新总额和界面显示
                self.update_all_totals()
                
            except Exception as e:
                print(f"加载计算时出错: {e}")
                QMessageBox.warning(self, "错误", f"加载计算时出错: {e}")
                # 恢复之前的计算ID
                self.current_calculation_id = old_calculation_id
        else:
            QMessageBox.warning(self, "错误", "无法找到选中的计算数据")
    
    def load_people_list(self):
        """加载当前计算的人员列表"""
        # 确保people_list已经创建
        if self.people_list is None:
            # 尝试在当前计算页面查找
            current_widget = self.content_stack.widget(1) # 假设计算页面在索引1
            if current_widget:
                self.people_list = current_widget.findChild(QListWidget, "peopleList")
            if self.people_list is None:
                print("错误：无法找到 people_list 控件")
                return
            
        # 清空当前列表
        self.people_list.clear()
        
        try:
            # 从当前计算记录中获取权威的人员列表
            person_names = []
            if self.current_calculation_id and self.current_calculation_id in self.calculations:
                person_names = self.calculations[self.current_calculation_id].get("人员", [])
            else:
                # 如果没有当前计算或人员列表，则不加载
                return
            
            # 添加每个人员到列表
            for name in person_names:
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, name)
                self.people_list.addItem(item)
            
            # 设置右键菜单
            # 先断开旧连接，防止重复连接
            try:
                self.people_list.customContextMenuRequested.disconnect()
            except TypeError:
                pass # 没有连接时会抛出TypeError
            # 连接新信号
            self.people_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.people_list.customContextMenuRequested.connect(self.show_people_list_context_menu)
            
        except Exception as e:
            print(f"加载人员列表时出错: {e}")
    
    def show_people_list_context_menu(self, position):
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
        
        # 如果用户取消或没有输入名称，直接返回
        if not ok or not template_name.strip():
            return
            
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
        result = template_dialog.exec()
        
        # 如果用户取消，直接返回
        if result != QDialog.DialogCode.Accepted:
            return
        
        # 用户确认选择
        selected_items = template_list.selectedItems()
        if selected_items:
            template_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.apply_template(template_name)
        else:
            QMessageBox.information(self, "提示", "请先选择一个模板")
    
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
            QMessageBox.warning(self, "错误", f"找不到模板 '{template_name}'")
            return
            
        # 获取模板数据
        template_data = self.templates[template_name]
        template_person_names = template_data.get("人员", [])
        
        if not template_person_names:
            QMessageBox.information(self, "提示", f"模板 '{template_name}' 不包含人员信息。")
            return

        # 确保有一个当前计算正在进行
        if not self.current_calculation_id or self.current_calculation_id not in self.calculations:
            QMessageBox.warning(self, "错误", "请先创建或加载一个计算记录，然后再应用模板。")
            return
        
        # 获取当前计算记录
        current_calc = self.calculations[self.current_calculation_id]
        current_person_names = current_calc.get("人员", [])
        current_data = current_calc.get("数据", {})
        
        # 合并人员列表，处理重复
        duplicates = []
        added_count = 0
        for name in template_person_names:
            if name not in current_person_names:
                current_person_names.append(name)
                # 为新添加的人员初始化空的投注数据
                if name not in current_data:
                    current_data[name] = {}
                added_count += 1
            else:
                duplicates.append(name)
                
        # 更新计算记录
        current_calc["人员"] = current_person_names
        current_calc["数据"] = current_data # 更新数据字典以包含新人员
        current_calc["人数"] = len(current_person_names)
        
        # 更新内存中的 people_data (以防万一)
        self.people_data = current_data

        # 保存当前计算
        self.save_current_calculation()

        # 刷新主计算页面的人员列表和总览
        self.load_people_list() 
        self.update_all_totals()
        
        # 显示提示信息
        if added_count > 0 and duplicates:
            QMessageBox.information(self, "模板已应用", 
                                    f"成功添加 {added_count} 名人员。以下人员已存在，未重复添加：{', '.join(duplicates)}")
        elif added_count > 0:
             QMessageBox.information(self, "模板已应用", f"成功添加 {added_count} 名人员。")
        elif duplicates:
            QMessageBox.information(self, "提示", f"模板中的所有人员已存在于当前计算中。")
    
    def add_from_template(self):
        """从模板添加人员"""
        # 如果没有当前计算，先创建
        if not self.current_calculation_id:
            # 创建新计算
            new_calc_id = datetime.now().strftime("%Y%m%d%H%M%S")
            calc_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            default_title = f"计算 {calc_date}"
            
            # 弹出对话框让用户命名
            new_title, ok = QInputDialog.getText(
                self, "新建计算", "请输入记录名称:", 
                QLineEdit.EchoMode.Normal, default_title
            )
            
            # 如果用户取消，直接返回
            if not ok:
                return
            
            # 如果输入为空，使用默认标题
            record_title = new_title.strip() if new_title.strip() else default_title
            
            # 创建新计算结构
            self.calculations[new_calc_id] = {
                "日期": calc_date,
                "创建时间": calc_date,
                "标题": record_title,
                "人员": [],
                "人数": 0,
                "数据": {},
                "开奖设置": {"中奖号码": None, "赔率": None},
                "总览": {},
                "用户结果": {}
            }
            
            # 设置当前计算ID
            self.current_calculation_id = new_calc_id
            
            # 保存新记录
            self.save_current_calculation()
            
            # 更新历史记录列表
            self.update_history_list()
            
            # 创建人员计算页面
            self.setup_people_calculation()
            
            # 切换到人员计算页面
            calc_page_index = 1
            if self.content_stack.count() > calc_page_index:
                self.content_stack.setCurrentIndex(calc_page_index)
            
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
        result = template_dialog.exec()
        
        # 如果用户取消模板选择，直接返回
        if result != QDialog.DialogCode.Accepted:
            return
        
        # 用户选择了模板
        selected_items = template_list.selectedItems()
        if selected_items:
            template_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.apply_template(template_name)
        else:
            QMessageBox.information(self, "提示", "请先选择一个模板")
    
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

    def save_person_details(self, person_name, category_inputs):
        # 确保该人员的数据字典已初始化
        if person_name not in self.people_data:
            self.people_data[person_name] = {}
        
        # 保存各个分类的金额
        for category, input_field in category_inputs.items():
            try:
                value = float(input_field.text()) if input_field.text() else 0
                self.people_data[person_name][category] = value
            except ValueError:
                QMessageBox.warning(self, "输入错误", f"请为 {category} 输入有效的数字金额")
                return
        
        # 保存当前计算
        self.save_current_calculation()
        
        # 更新总费用显示
        self.update_all_totals()
        
        # 返回到上一页
        self.return_from_details()

    def restore_from_trash(self, original_file_name):
        """从垃圾桶恢复文件"""
        try:
            # 获取计算ID
            calc_id = original_file_name.replace('.json', '')
            
            # 查找垃圾桶中与这个计算ID相关的最新备份
            latest_backup = None
            latest_time = 0
            
            for file_name in os.listdir(self.trash_dir):
                # 检查文件是否与当前计算ID相关
                if file_name.startswith(f"{calc_id}_") and file_name.endswith('.json'):
                    file_path = os.path.join(self.trash_dir, file_name)
                    file_time = os.path.getmtime(file_path)
                    
                    # 找到最新的备份
                    if file_time > latest_time:
                        latest_time = file_time
                        latest_backup = file_name
            
            # 如果找到备份文件
            if latest_backup:
                # 构建路径
                backup_path = os.path.join(self.trash_dir, latest_backup)
                original_path = os.path.join(self.history_dir, original_file_name)
                
                # 恢复文件
                shutil.copy2(backup_path, original_path)
                
                # 重新加载历史记录
                self.load_history()
                
                # 如果当前正在查看的是被恢复的记录，则重新加载它
                if calc_id == self.current_calculation_id:
                    # 找到对应的列表项
                    for i in range(self.history_list.count()):
                        item = self.history_list.item(i)
                        item_id = item.data(Qt.ItemDataRole.UserRole)
                        if item_id == calc_id:
                            # 重新加载
                            self.load_calculation_from_history(item)
                            break
                
                QMessageBox.information(self, "恢复成功", "已恢复到上一个版本。")
            else:
                QMessageBox.warning(self, "恢复失败", "找不到备份文件。")
                
        except Exception as e:
            QMessageBox.warning(self, "恢复失败", f"恢复文件时出错: {str(e)}")
    
    def show_trash_contents(self):
        """显示垃圾桶内容"""
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("垃圾桶")
        dialog.resize(500, 400)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 添加说明
        info_label = QLabel("垃圾桶中的文件会在7天后自动删除。")
        layout.addWidget(info_label)
        
        # 添加列表
        trash_list = QListWidget()
        layout.addWidget(trash_list)
        
        # 获取垃圾桶中的文件并按修改时间排序
        trash_files = []
        for file_name in os.listdir(self.trash_dir):
            if file_name.endswith('.json'):
                file_path = os.path.join(self.trash_dir, file_name)
                mod_time = os.path.getmtime(file_path)
                
                # 提取计算ID
                parts = file_name.split('_')
                calc_id = parts[0]
                
                # 获取原始计算的标题
                title = "未知记录"
                if calc_id in self.calculations:
                    title = self.calculations[calc_id].get("标题", "未知记录")
                
                # 格式化时间
                backup_time = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
                
                trash_files.append((file_name, title, backup_time, mod_time))
        
        # 按修改时间排序（最新的在前面）
        trash_files.sort(key=lambda x: x[3], reverse=True)
        
        # 填充列表
        for file_name, title, backup_time, _ in trash_files:
            item = QListWidgetItem(f"{title} (备份于 {backup_time})")
            item.setData(Qt.ItemDataRole.UserRole, file_name)
            trash_list.addItem(item)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        
        restore_button = QPushButton("恢复选中项")
        restore_button.clicked.connect(lambda: self.restore_selected_trash(trash_list))
        
        delete_button = QPushButton("删除选中项")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(lambda: self.delete_selected_trash(trash_list))
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(dialog.accept)
        
        button_layout.addWidget(restore_button)
        button_layout.addWidget(delete_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # 显示对话框
        dialog.exec()
    
    def restore_selected_trash(self, trash_list):
        """恢复选中的垃圾文件"""
        selected_items = trash_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要恢复的文件")
            return
            
        file_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        # 提取计算ID
        parts = file_name.split('_')
        if len(parts) >= 2:
            calc_id = parts[0]
            original_file = f"{calc_id}.json"
            
            # 确认恢复
            reply = QMessageBox.question(
                self, "确认恢复", 
                f"确定要恢复此备份吗？当前的数据将被覆盖。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 构建路径
                backup_path = os.path.join(self.trash_dir, file_name)
                original_path = os.path.join(self.history_dir, original_file)
                
                try:
                    # 恢复文件
                    shutil.copy2(backup_path, original_path)
                    
                    # 重新加载历史记录
                    self.load_history()
                    
                    # 如果当前正在查看的是被恢复的记录，则重新加载它
                    if calc_id == self.current_calculation_id:
                        # 找到对应的列表项
                        for i in range(self.history_list.count()):
                            item = self.history_list.item(i)
                            item_id = item.data(Qt.ItemDataRole.UserRole)
                            if item_id == calc_id:
                                # 重新加载
                                self.load_calculation_from_history(item)
                                break
                    
                    QMessageBox.information(self, "恢复成功", "已恢复选中的备份。")
                except Exception as e:
                    QMessageBox.warning(self, "恢复失败", f"恢复文件时出错: {str(e)}")
    
    def delete_selected_trash(self, trash_list):
        """删除选中的垃圾文件"""
        selected_items = trash_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要删除的文件")
            return
            
        file_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除此备份文件吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            file_path = os.path.join(self.trash_dir, file_name)
            try:
                # 删除文件
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
                # 从列表中移除
                row = trash_list.row(selected_items[0])
                trash_list.takeItem(row)
                
                QMessageBox.information(self, "删除成功", "备份文件已成功删除。")
            except Exception as e:
                QMessageBox.warning(self, "删除失败", f"删除文件时出错: {str(e)}")

    def update_results_display(self, results_by_person, total_bets, total_winnings, merchant_profit):
        """更新主页面的结果显示区域"""
        try:
            # 直接使用保存的布局引用，并检查其有效性
            if self.results_layout is None:
                print("错误：results_layout 尚未初始化")
                return
                
            # 安全地清除现有内容
            items_to_remove = []
            while self.results_layout.count() > 0:
                items_to_remove.append(self.results_layout.takeAt(0))

            for item in items_to_remove:
                if item is None: continue
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                else:
                    layout_item = item.layout()
                    if layout_item:
                        # 递归清除子布局（使用相同安全模式）
                        sub_items_to_remove = []
                        while layout_item.count() > 0:
                            sub_items_to_remove.append(layout_item.takeAt(0))
                        for sub_item in sub_items_to_remove:
                            if sub_item is None: continue
                            sub_widget = sub_item.widget()
                            if sub_widget:
                                sub_widget.deleteLater()
                            else:
                                inner_layout = sub_item.layout()
                                if inner_layout:
                                    inner_items_to_remove = []
                                    while inner_layout.count() > 0:
                                        inner_items_to_remove.append(inner_layout.takeAt(0))
                                    for inner_item in inner_items_to_remove:
                                        if inner_item and inner_item.widget():
                                            inner_item.widget().deleteLater()
            
            # --- 后续添加新内容的逻辑保持不变 --- 
            # 添加用户结果区域
            people_results_frame = QFrame()
            people_results_frame.setObjectName("summaryFrame")
            people_results_layout = QVBoxLayout(people_results_frame)
            
            people_title = QLabel("用户投注结果")
            people_title.setObjectName("sectionTitle")
            people_results_layout.addWidget(people_title)
            
            # 按用户名排序显示
            sorted_persons = sorted(results_by_person.keys())

            for person in sorted_persons:
                results = results_by_person[person]
                item_layout = QHBoxLayout()
                
                person_button = QPushButton(person)
                person_button.setObjectName("personButton")
                # 使用 lambda 确保传递正确的 person 值
                person_button.clicked.connect(lambda checked, p=person: self.show_person_details(p))
                
                bet_amount = results.get("投注总额", 0.0)
                win_amount = results.get("中奖金额", 0.0)
                net_result = win_amount - bet_amount # 计算盈亏
                
                # 根据盈亏设置颜色
                if net_result >= 0:
                    result_color = "#4CAF50" # 绿色
                else:
                    result_color = "#f44336" # 红色
                    
                result_text = f"投注: {bet_amount:.2f}, 中奖: {win_amount:.2f}, 盈亏: {net_result:+.2f}"
                result_label = QLabel(result_text)
                result_label.setObjectName("summaryValue")
                result_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                # 应用颜色 (注意: 可能需要调整样式表优先级或使用更具体的选择器)
                result_label.setStyleSheet(f"color: {result_color};") 
                result_label.setMinimumWidth(250) # 增加最小宽度以容纳新字段
                
                item_layout.addWidget(person_button)
                item_layout.addStretch()
                item_layout.addWidget(result_label)
                
                people_results_layout.addLayout(item_layout)
            
            # 将用户结果框架添加到主结果布局
            self.results_layout.addWidget(people_results_frame)
            self.results_layout.addSpacing(15)
            
            # 添加总计区域
            summary_frame = QFrame()
            summary_frame.setObjectName("summaryFrame")
            summary_layout = QVBoxLayout(summary_frame)
            
            summary_title = QLabel("本期总览")
            summary_title.setObjectName("sectionTitle")
            summary_layout.addWidget(summary_title)
            
            # 总投注额
            total_bet_layout = QHBoxLayout()
            total_bet_label = QLabel("总投注额:")
            total_bet_label.setObjectName("summaryLabel")
            total_bet_value = QLabel(f"{total_bets:.2f}")
            total_bet_value.setObjectName("summaryValue")
            total_bet_layout.addWidget(total_bet_label)
            total_bet_layout.addStretch()
            total_bet_layout.addWidget(total_bet_value)
            summary_layout.addLayout(total_bet_layout)
            
            # 总派彩额
            total_win_layout = QHBoxLayout()
            total_win_label = QLabel("总派彩额:")
            total_win_label.setObjectName("summaryLabel")
            total_win_value = QLabel(f"{total_winnings:.2f}")
            total_win_value.setObjectName("summaryValue")
            total_win_layout.addWidget(total_win_label)
            total_win_layout.addStretch()
            total_win_layout.addWidget(total_win_value)
            summary_layout.addLayout(total_win_layout)
            
            # 商家盈亏
            profit_layout = QHBoxLayout()
            profit_label = QLabel("商家盈亏:")
            profit_label.setObjectName("totalLabel") # 使用更醒目的样式
            profit_value = QLabel(f"{merchant_profit:.2f}")
            profit_value.setObjectName("totalValue") # 使用更醒目的样式
            # 根据盈亏设置颜色
            if merchant_profit >= 0:
                profit_value.setStyleSheet("color: #4CAF50;") # 绿色表示盈利或持平
            else:
                profit_value.setStyleSheet("color: #f44336;") # 红色表示亏损
                
            profit_layout.addWidget(profit_label)
            profit_layout.addStretch()
            profit_layout.addWidget(profit_value)
            summary_layout.addLayout(profit_layout)
            
            # 将总计框架添加到主结果布局
            self.results_layout.addWidget(summary_frame)

        except RuntimeError as e:
            # 捕获特定错误，打印提示信息
            print(f"运行时错误 (可能对象已删除) in update_results_display: {e}")
            # 可以选择在这里尝试重新获取 self.results_layout 的引用，
            # 但更简单的做法是忽略这次更新，等待下一次UI交互触发的更新。
            pass 
        except Exception as e:
            print(f"更新结果显示时出错: {e}")
            import traceback
            traceback.print_exc()


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
            color: #e0e0e0;
        }
        
        QLabel#grandTotal {
            font-size: 16px;
            font-weight: bold;
            color: #4fc3f7;
        }
        
        QLabel#categoryLabel {
            font-size: 14px;
            font-weight: bold;
            color: #e0e0e0;
        }
        
        QLabel#categoryLabelReward {
            font-size: 14px;
            font-weight: bold;
            color: #4fc3f7;
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
            color: #e0e0e0;
        }
        
        QListWidget::item:selected {
            background-color: #2979ff;
            color: white;
        }
        
        QListWidget::item:hover {
            background-color: #454545;
        }
        
        QListWidget#historyList::item:alternate {
            background-color: #383838;
            color: #e0e0e0;
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
            background-color: #3a3a3a;
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
            width: 14px;
            margin: 0px;
            border-radius: 0px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #5a5d5f;
            min-height: 30px;
            border-radius: 7px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #6a6d6f;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
            background: none;
        }
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
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
        
        QCheckBox {
            spacing: 5px;
            color: #e0e0e0;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }
        
        QCheckBox::indicator:unchecked {
            background-color: #3c3f41;
            border: 1px solid #5a5d5f;
            border-radius: 3px;
        }
        
        QCheckBox::indicator:checked {
            background-color: #2979ff;
            border: 1px solid #2979ff;
            border-radius: 3px;
        }
        
        QFrame#totalInfoFrame {
            background-color: #3a3a3a;
            border-radius: 4px;
            padding: 10px;
            margin-top: 10px;
        }
        
        QLabel#totalInfoLabel {
            font-size: 14px;
            color: #e0e0e0;
        }
    """
    app.setStyleSheet(dark_stylesheet)
    
    window = ExpenseCalculator()
    window.show()
    sys.exit(app.exec())