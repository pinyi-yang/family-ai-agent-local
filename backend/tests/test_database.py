from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, FamilyMember

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_create_family_member():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    member = FamilyMember(name="Alice", email="alice@example.com")
    db.add(member)
    db.commit()
    db.refresh(member)
    assert member.id is not None
    assert member.name == "Alice"
    db.close()
    Base.metadata.drop_all(bind=engine)
