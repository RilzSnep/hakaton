from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from models import Queue, get_db

app = FastAPI()

# Добавление пользователя в очередь
@app.post("/add_to_queue/")
def add_to_queue(user_id: int, username: str, db: Session = Depends(get_db)):
    # Проверяем, существует ли пользователь в очереди
    existing_user = db.query(Queue).filter(Queue.user_id == user_id).first()

    if existing_user:
        return {"message": f"User {username} already in the queue with position {existing_user.position}."}

    # Определяем позицию для нового пользователя
    position = db.query(Queue).count() + 1

    # Добавляем пользователя в очередь
    new_user = Queue(user_id=user_id, username=username, position=position)
    db.add(new_user)
    db.commit()

    return {"message": f"User {username} added to the queue with position {position}."}


# Получение текущей позиции пользователя в очереди
@app.get("/position/{user_id}")
def get_position(user_id: int, db: Session = Depends(get_db)):
    user = db.query(Queue).filter(Queue.user_id == user_id).first()

    if user:
        return {"position": user.position}
    return {"message": "User not found in queue."}


# Удаление первого пользователя из очереди
@app.delete("/next/")
def remove_first_from_queue(db: Session = Depends(get_db)):
    # Получаем первого пользователя в очереди
    first_in_queue = db.query(Queue).order_by(Queue.position.asc()).first()

    if first_in_queue:
        db.delete(first_in_queue)
        db.commit()

        # Пересчитываем позиции для остальных пользователей
        remaining_users = db.query(Queue).filter(Queue.position > first_in_queue.position).all()
        for user in remaining_users:
            user.position -= 1
        db.commit()

        return {"message": "First user removed from queue, remaining positions updated."}
    return {"message": "Queue is empty."}


@app.delete("/remove_from_queue/{user_id}")
def remove_from_queue(user_id: int, db: Session = Depends(get_db)):
    # Ищем пользователя в базе данных по его user_id
    user = db.query(Queue).filter(Queue.user_id == user_id).first()

    if user:
        # Удаляем пользователя из очереди
        db.delete(user)
        db.commit()
        return {"message": f"Пользователь с ID {user_id} был удален из очереди."}
    else:
        # Если пользователя нет в базе
        return {"message": f"Пользователь с ID {user_id} не найден в очереди."}


# Получение всех участников очереди
@app.get("/all_queue/")
def get_all_queue(db: Session = Depends(get_db)):
    # Получаем всех пользователей, отсортированных по позиции в очереди
    users_in_queue = db.query(Queue).order_by(Queue.position.asc()).all()

    # Если очередь пуста
    if not users_in_queue:
        return {"message": "Queue is empty."}

    # Формируем список участников
    queue_list = [
        {"user_id": user.user_id, "username": user.username, "position": user.position}
        for user in users_in_queue
    ]

    return {"queue": queue_list}
