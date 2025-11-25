from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp
from kivy.clock import Clock

from database import clear_all_tasks
from supabase_client import supabase


class LoginScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)

        # -------- EMAIL FIELD ----------
        self.email = MDTextField(
            hint_text="Email",
            pos_hint={"center_x": 0.5, "center_y": 0.7},
            size_hint_x=0.8,
        )
        self.add_widget(self.email)

        # -------- PASSWORD FIELD -------
        self.password = MDTextField(
            hint_text="Password",
            password=True,
            pos_hint={"center_x": 0.5, "center_y": 0.6},
            size_hint_x=0.8,
        )
        self.add_widget(self.password)

        # -------- LOGIN BUTTON ---------
        login_btn = MDRaisedButton(
            text="Login",
            pos_hint={"center_x": 0.5, "center_y": 0.48},
            on_release=self.login_user,
        )
        self.add_widget(login_btn)

        # -------- REGISTER BUTTON ------
        register_btn = MDFlatButton(
            text="Create Account",
            pos_hint={"center_x": 0.5, "center_y": 0.4},
            on_release=self.open_register_dialog,
        )
        self.add_widget(register_btn)

    # =================================================
    # LOGIN
    # =================================================
    def login_user(self, *args):
        email = (self.email.text or "").strip()
        password = (self.password.text or "").strip()

        if not email or not password:
            MDDialog(text="Please enter email and password").open()
            return

        try:
            # Sign in with Supabase
            supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            # 1) Clear local tasks from previous user
            clear_all_tasks()

            # 2) Go to todo screen
            self.manager.current = "todo"

            # 3) After screen switch, trigger full sync for THIS user
            todo_screen = self.manager.get_screen("todo")
            Clock.schedule_once(lambda dt: todo_screen.on_sync())

        except Exception as e:
            MDDialog(text=f"Login failed: {e}").open()

    # =================================================
    # REGISTER
    # =================================================
    def open_register_dialog(self, *args):
        email_field = MDTextField(
            hint_text="Email",
            size_hint_y=None,
            height=dp(48),
        )
        password_field = MDTextField(
            hint_text="Password",
            password=True,
            size_hint_y=None,
            height=dp(48),
        )

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=[dp(12), dp(12), dp(12), dp(12)],
            size_hint_y=None,
        )
        content.add_widget(email_field)
        content.add_widget(password_field)
        content.bind(minimum_height=content.setter("height"))

        dialog = MDDialog(
            title="Create Account",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(
                    text="REGISTER",
                    on_release=lambda x: self.register_user(
                        email_field, password_field, dialog
                    ),
                ),
            ],
        )
        dialog.open()

    def register_user(self, email_field, password_field, dialog):
        email = (email_field.text or "").strip()
        password = (password_field.text or "").strip()

        if not email or not password:
            MDDialog(text="Please enter email and password").open()
            return

        try:
            supabase.auth.sign_up({"email": email, "password": password})
            dialog.dismiss()
            MDDialog(text="Account created! Now login with these details.").open()
        except Exception as e:
            MDDialog(text=f"Register failed: {e}").open()
