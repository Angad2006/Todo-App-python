from database import create_tables, list_tasks_local, add_task_local

create_tables()
print("Tasks BEFORE adding:", list_tasks_local())

tid = add_task_local("Test title from CLI", "Test description from CLI")
print("New task id:", tid)

print("Tasks AFTER adding:", list_tasks_local())
