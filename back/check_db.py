import sqlite3

def check_database():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    
    # 检查总任务数
    cursor.execute('SELECT COUNT(*) FROM tasks')
    total_tasks = cursor.fetchone()[0]
    print(f'总任务数: {total_tasks}')
    
    # 检查已完成任务数
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "completed"')
    completed_tasks = cursor.fetchone()[0]
    print(f'已完成任务数: {completed_tasks}')
    
    # 显示最近10条任务
    cursor.execute('SELECT id, description, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 10')
    tasks = cursor.fetchall()
    print('\n最近10条任务:')
    for task in tasks:
        task_id = task[0][:8] + '...' if len(task[0]) > 8 else task[0]
        description = task[1][:30] + '...' if len(task[1]) > 30 else task[1]
        print(f'{task_id} | {description} | {task[2]} | {task[3]}')
    
    conn.close()

if __name__ == '__main__':
    check_database()