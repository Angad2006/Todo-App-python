from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, TwoLineAvatarIconListItem, IconLeftWidget
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.floatlayout import MDFloatLayout

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView

from database import (
    list_tasks_local,
    add_task_local,
    delete_task_local,
    update_task_local,
    get_connection,
)
from supabase_client import supabase, get_current_user

import threading


class TodoListScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)

        # Root as float layout so we can place top / center / bottom
        root = MDFloatLayout()
        self.add_widget(root)

        # -------- TOP BAR (title + refresh at far right) ----------
        top_bar = MDBoxLayout(
            orientation="horizontal",
            padding=[dp(12), dp(12), dp(12), 0],
            spacing=dp(8),
            size_hint=(1, None),
            height=dp(56),
            pos_hint={"top": 1},
        )

        lbl_title = MDLabel(
           text="My Tasks",
           font_style="H5",
           halign="left",
           size_hint_x=1,      # let it expand horizontally
        )

        
        spacer_top = MDBoxLayout()  # will expand to push refresh to the right
        btn_refresh = MDIconButton(
            icon="refresh",
            on_release=self.on_sync,
        )

        top_bar.add_widget(lbl_title)
        top_bar.add_widget(spacer_top)
        top_bar.add_widget(btn_refresh)
        root.add_widget(top_bar)

        # -------- CENTER AREA (task list) ------------------------
        center_box = MDBoxLayout(
            orientation="vertical",
            padding=[dp(8), dp(4), dp(8), dp(4)],
            size_hint=(1, 0.75),
            pos_hint={"top": 0.9},
        )

        scroll = ScrollView()
        self.task_list = MDList()
        scroll.add_widget(self.task_list)
        center_box.add_widget(scroll)
        root.add_widget(center_box)

        # -------- BOTTOM BAR (Add left, Logout right) ------------
        bottom_bar = MDBoxLayout(
            orientation="horizontal",
            padding=[dp(12), 0, dp(12), dp(12)],
            spacing=dp(8),
            size_hint=(1, None),
            height=dp(52),
            pos_hint={"y": 0},
        )

        btn_add = MDRaisedButton(
            text="Add Task",
            on_release=self.add_task,
            size_hint_x=None,
        )
        spacer_bottom = MDBoxLayout()  # pushes logout to the right
        btn_logout = MDRaisedButton(
            text="Logout",
            on_release=self.logout,
            size_hint_x=None,
        )

        bottom_bar.add_widget(btn_add)       # left
        bottom_bar.add_widget(spacer_bottom) # middle (flex)
        bottom_bar.add_widget(btn_logout)    # right
        root.add_widget(bottom_bar)

        # Load tasks from local DB
        self.refresh_tasks()

    # -------------------------------------------------
    # LIST + DISPLAY
    # -------------------------------------------------
    def refresh_tasks(self):
        """Reload tasks from local DB into the list widget."""
        self.task_list.clear_widgets()
        tasks = list_tasks_local()

        for t in tasks:
            title = t.get("title", "Untitled")
            desc = t.get("description") or ""

            if t.get("completed"):
                item = TwoLineAvatarIconListItem(
                    text=title,
                    secondary_text=desc,
                )
                item.add_widget(IconLeftWidget(icon="check"))
            else:
                item = TwoLineAvatarIconListItem(
                    text=title,
                    secondary_text=desc,
                )

            item.bind(on_release=lambda inst, tid=t["id"]: self.on_item_click(tid))
            self.task_list.add_widget(item)

    # -------------------------------------------------
    # ADD + SAVE
    # -------------------------------------------------
    def add_task(self, *args):
        """Open dialog with Title + Description fields."""
        title_field = MDTextField(
            hint_text="Task title",
            size_hint_y=None,
            height=dp(48),
        )
        desc_field = MDTextField(
            hint_text="Description",
            size_hint_y=None,
            height=dp(80),
            multiline=True,
        )

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=[dp(12), dp(12), dp(12), dp(12)],
            size_hint_y=None,
        )
        content.add_widget(title_field)
        content.add_widget(desc_field)
        content.bind(minimum_height=content.setter("height"))

        dialog = MDDialog(
            title="New Task",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda btn: dialog.dismiss()),
                MDFlatButton(
                    text="SAVE",
                    on_release=lambda btn: self._save_from_dialog(
                        title_field, desc_field, dialog
                    ),
                ),
            ],
        )
        dialog.open()

    def _save_from_dialog(self, title_field, desc_field, dialog):
        title = title_field.text
        description = desc_field.text
        dialog.dismiss()
        self.save_task(title, description)

    def save_task(self, title, description=""):
        title = (title or "").strip()
        description = (description or "").strip()

        if not title:
            MDDialog(text="Please enter a task title").open()
            return

        task_id = add_task_local(title, description)
        self.refresh_tasks()

        # Sync in background
        threading.Thread(
            target=self.sync_task, args=(task_id, title, description), daemon=True
        ).start()

    def sync_task(self, task_id, title, description):
        try:
            user = get_current_user()
            if not user or not user.get("id"):
                print("No user found during sync_task; skipping server insert.")
                return

            supabase.table("tasks").insert(
                {
                    "id": task_id,
                    "title": title,
                    "description": description,
                    "user_id": user["id"],
                }
            ).execute()
        except Exception as e:
            print("Sync failed:", e)

    # -------------------------------------------------
    # TAP ON TASK: EDIT / DONE / DELETE
    # -------------------------------------------------
    def on_item_click(self, task_id):
        dialog = MDDialog(
            title="Task options",
            text="Choose an action for this task",
            buttons=[
                MDFlatButton(
                    text="EDIT",
                    on_release=lambda btn: (
                        dialog.dismiss(),
                        self.edit_task(task_id),
                    ),
                ),
                MDFlatButton(
                    text="DONE",
                    on_release=lambda btn: (
                        dialog.dismiss(),
                        self.complete_task(task_id),
                    ),
                ),
                MDFlatButton(
                    text="DELETE",
                    on_release=lambda btn: (
                        dialog.dismiss(),
                        self.delete_task(task_id),
                    ),
                ),
                MDFlatButton(text="CLOSE", on_release=lambda btn: dialog.dismiss()),
            ],
        )
        dialog.open()

    def edit_task(self, task_id):
        """Open dialog to edit existing task."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT title, description FROM tasks WHERE id = ?",
            (task_id,),
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            MDDialog(text="Task not found.").open()
            return

        current_title = row[0] or ""
        current_desc = row[1] or ""

        title_field = MDTextField(
            hint_text="Task title",
            text=current_title,
            size_hint_y=None,
            height=dp(48),
        )
        desc_field = MDTextField(
            hint_text="Description",
            text=current_desc,
            size_hint_y=None,
            height=dp(80),
            multiline=True,
        )

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=[dp(12), dp(12), dp(12), dp(12)],
            size_hint_y=None,
        )
        content.add_widget(title_field)
        content.add_widget(desc_field)
        content.bind(minimum_height=content.setter("height"))

        dialog = MDDialog(
            title="Edit Task",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda btn: dialog.dismiss()),
                MDFlatButton(
                    text="SAVE",
                    on_release=lambda btn: self._save_edit_dialog(
                        task_id, title_field, desc_field, dialog
                    ),
                ),
            ],
        )
        dialog.open()

    def _save_edit_dialog(self, task_id, title_field, desc_field, dialog):
        new_title = (title_field.text or "").strip()
        new_desc = (desc_field.text or "").strip()
        dialog.dismiss()

        if not new_title:
            MDDialog(text="Title cannot be empty").open()
            return

        update_task_local(task_id, title=new_title, description=new_desc)
        self.refresh_tasks()

        threading.Thread(
            target=self.sync_update_server,
            args=(task_id, new_title, new_desc),
            daemon=True,
        ).start()

    def sync_update_server(self, task_id, title, description):
        try:
            user = get_current_user()
            if not user or not user.get("id"):
                return
            supabase.table("tasks").update(
                {"title": title, "description": description}
            ).eq("id", task_id).eq("user_id", user["id"]).execute()
        except Exception as e:
            print("Sync update error:", e)

    def delete_task(self, task_id):
        delete_task_local(task_id)
        self.refresh_tasks()
        threading.Thread(
            target=self._delete_server, args=(task_id,), daemon=True
        ).start()

    def _delete_server(self, task_id):
        try:
            user = get_current_user()
            if not user or not user.get("id"):
                return
            supabase.table("tasks").delete().eq("id", task_id).eq(
                "user_id", user["id"]
            ).execute()
        except Exception as e:
            print("Server delete error:", e)

    def complete_task(self, task_id):
        update_task_local(task_id, completed=True)
        self.refresh_tasks()
        threading.Thread(
            target=self.sync_complete_server, args=(task_id,), daemon=True
        ).start()

    def sync_complete_server(self, task_id):
        try:
            user = get_current_user()
            if not user or not user.get("id"):
                return
            supabase.table("tasks").update({"completed": True}).eq("id", task_id).eq(
                "user_id", user["id"]
            ).execute()
        except Exception as e:
            print("Sync complete error:", e)

    # -------------------------------------------------
    # SYNC ALL FROM SERVER
    # -------------------------------------------------
    def on_sync(self, *args):
        threading.Thread(target=self.full_sync, daemon=True).start()

    def full_sync(self):
        try:
            user = get_current_user()
            if not user or not user.get("id"):
                print("No user found during full_sync; skipping server fetch.")
                return

            res = supabase.table("tasks").select("*").eq(
                "user_id", user["id"]
            ).execute()
            server_tasks = (
                res.get("data", [])
                if isinstance(res, dict)
                else getattr(res, "data", []) or []
            )

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM tasks")
            for t in server_tasks:
                cur.execute(
                    """
                    INSERT INTO tasks (id, title, description, completed, synced)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        t.get("id"),
                        t.get("title"),
                        t.get("description") or "",
                        1 if t.get("completed") else 0,
                        1,
                    ),
                )
            conn.commit()
            conn.close()

            Clock.schedule_once(lambda dt: self.refresh_tasks())
        except Exception as e:
            print("Full sync error:", e)

    # -------------------------------------------------
    # LOGOUT
    # -------------------------------------------------
    def logout(self, *args):
        try:
            supabase.auth.sign_out()
        except Exception as e:
            print("sign_out error:", e)
            MDDialog(text=f"Logout error: {e}").open()
            return
        self.manager.current = "login"
