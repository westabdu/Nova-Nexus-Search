from sqlmodel import SQLModel, create_engine, Session
import sqlite3
import os

sqlite_file_name = "nova_nexus.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)

def _check_schema_and_reset():
    """
    Mevcut DB'nin User tablosunda yeni kolonlar var mı kontrol eder.
    Yoksa (model değişimi) DB'yi silerek yeniden oluşturur.
    """
    required_columns = {"totp_enabled", "totp_secret", "totp_pending",
                        "failed_login_attempts", "locked_until",
                        "last_login", "password_changed_at",
                        "backup_codes", "token_version",
                        "api_key_last_used", "is_admin",
                        "groq_api_key", "gemini_api_key", "deepseek_api_key"}
    if not os.path.exists(sqlite_file_name):
        return  # DB yok, create_db_and_tables halleder
    try:
        con = sqlite3.connect(sqlite_file_name)
        cur = con.execute("PRAGMA table_info(user)")
        existing = {row[1] for row in cur.fetchall()}
        con.close()
        if not required_columns.issubset(existing):
            print("[⚠️  DB] Şema güncellendi, veritabanı yeniden oluşturuluyor...")
            os.remove(sqlite_file_name)
    except Exception as e:
        print(f"[DB kontrol hatası] {e}")

def create_db_and_tables():
    _check_schema_and_reset()
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
