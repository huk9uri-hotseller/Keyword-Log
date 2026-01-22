from app.db import SessionLocal
from app.models import User
from sqlalchemy import text

def test_connection():
    db = SessionLocal()
    try:
        # 1. DB 연결 테스트
        result = db.execute(text("SELECT 1"))
        print(f"DB Connection Test: {result.scalar()} (Success)")

        # 2. 모델 매핑 테스트 (User 테이블 조회)
        user_count = db.query(User).count()
        print(f"User Table Count: {user_count} (Model Mapping Success)")
        
        print("All tests passed successfully!")
    except Exception as e:
        print(f"Test Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_connection()
