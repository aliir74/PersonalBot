from exports import notion_exporter

if __name__ == "__main__":
    tasks = notion_exporter.get_tasks_due()
    print(tasks)
