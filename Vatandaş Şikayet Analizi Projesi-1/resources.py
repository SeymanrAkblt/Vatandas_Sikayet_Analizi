# resources.py
from typing import List

PASTEL_41: List[str] = [
    "#A5C8E1","#F7C5CC","#BFD8B8","#FFF1B5","#C7CEEA","#FFDAC1","#E2F0CB",
    "#B5EAD7","#FFDFD3","#E0BBE4","#F1D1B5","#C2F0FC","#FDE2E4","#CDE7BE",
    "#F8E1F4","#E3F2FD","#F4E1D2","#D0E1F9","#E6E6FA","#D5E8D4","#FBE7C6",
    "#D7E3FC","#F2E2D2","#CCE2CB","#F6D1C1","#D8E2DC","#EAE4E9","#B8E0D2",
    "#EFD3D7","#F9E2AE","#C9E4DE","#E2ECE9","#F7D6E0","#C6DEF1","#FDE2E1",
    "#D3F8E2","#F2C6DE","#C4FCEF","#F9F1F0","#D9E4DD","#F6F0ED"
]

APP_QSS = """
QMainWindow { background: #f7f7fb; }
QTabWidget::pane { border: 1px solid #e3e7ee; border-radius: 8px; background: #ffffff; }
QTabBar::tab { padding: 8px 14px; margin: 4px; border: 1px solid #e3e7ee; border-radius: 16px; background: #fafbff; color: #334155; }
QTabBar::tab:selected { background: #e8f0fe; color: #1e40af; border-color: #d0d7f0; }
QLineEdit, QComboBox, QDateEdit { padding: 8px; border-radius: 10px; border: 1px solid #e3e7ee; background: #ffffff; }
QPushButton { padding: 8px 14px; border-radius: 10px; background: #1e40af; color: white; }
QPushButton:hover { background: #233fa0; }
QTreeWidget, QListWidget, QTableWidget { background: #ffffff; border: 1px solid #e3e7ee; border-radius: 10px; }
QHeaderView::section { background: #f0f4ff; border: none; padding: 6px; border-radius: 10px; }
QMessageBox { background: #ffffff; }
"""

def color_for_index(i: int) -> str:
    return PASTEL_41[i % len(PASTEL_41)]
