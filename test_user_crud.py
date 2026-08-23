from backend.database.database import SessionLocal
from backend.database.models import User, UserToken
from backend.main import hash_password, verify_password
import secrets

db = SessionLocal()

username = "temp_test_user_999"
password = "password123"

# 1. Create User
print("Creating User...")
existing = db.query(User).filter(User.username == username).first()
if existing:
    db.delete(existing)
    db.commit()

pw_hash, salt = hash_password(password)
user = User(username=username, password_hash=pw_hash, password_salt=salt)
db.add(user)
db.commit()
db.refresh(user)

print("Created User ID:", user.user_id)

# 2. Verify Password
print("Verifying Password...")
assert verify_password(password, user.password_hash, user.password_salt)
print("Password verified successfully!")

# 3. Create Token
print("Creating User Token...")
token_str = secrets.token_hex(32)
user_token = UserToken(token=token_str, user_id=user.user_id)
db.add(user_token)
db.commit()

print("Created Token:", token_str[:10] + "...")

# 4. Fetch Token
print("Fetching Token...")
fetched_token = db.query(UserToken).filter(UserToken.token == token_str).first()
assert fetched_token is not None
assert fetched_token.user_id == user.user_id
print("Token fetched and validated successfully!")

# Clean up
print("Cleaning up user and token...")
db.delete(fetched_token)
db.delete(user)
db.commit()
print("Cleanup complete.")

db.close()
