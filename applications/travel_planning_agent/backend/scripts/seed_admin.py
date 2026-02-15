from app.db.database import SessionLocal
from app.db.models import User
from app.security.jwt import hash_password


def main() -> None:
    db = SessionLocal()
    try:
        username = "admin@example.com"
        password = "admin123"
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print("Admin user already exists.")
            return
        user = User(username=username, hashed_password=hash_password(password))
        db.add(user)
        db.commit()
        print("Admin user created.")
    finally:
        db.close()


if __name__ == "__main__":
    main()