from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def hash_password(password):
    return bcrypt.generate_password_hash(password).decode('utf-8')

if __name__ == "__main__":
    password = input("Enter the password to hash: ")
    hashed = hash_password(password)
    print("Hashed Password:", hashed)