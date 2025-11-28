# C:\Users\angad\OneDrive\Desktop\todo_python_app\main.py
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager
from screens.login import LoginScreen
from screens.todo_list import TodoListScreen
from database import create_tables
import traceback
import sys


class WindowManager(ScreenManager):
    pass


class TodoApp(MDApp):
    def build(self):
        create_tables()

        # app theme
        self.theme_cls.theme_style = "Light"          
        self.theme_cls.primary_palette = "Blue"       
        self.theme_cls.primary_hue = "500"

        # screen manager
        self.sm = WindowManager()
        self.sm.add_widget(LoginScreen(name="login"))
        self.sm.add_widget(TodoListScreen(name="todo"))
        self.sm.current = "login"
        return self.sm


if __name__ == "__main__":
    try:
        TodoApp().run()
    except Exception:
        with open("error.log", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        print("An error occurred. Full traceback written to error.log")
        traceback.print_exc(file=sys.stdout)
        raise
