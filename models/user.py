# models/user.py
from .baseObject import baseObject
from werkzeug.security import generate_password_hash, check_password_hash  # Keep for when you re-enable
import re

class user(baseObject):
    def __init__(self):
        super().__init__()

    def verify_new(self):
        """Validate new user data before insert."""
        self.errors = []
        if not self.data or len(self.data) == 0:
            self.errors.append("No data provided")
            return False

        d = self.data[0]

        # Required fields (using actual DB column names)
        if not d.get('Email'):
            self.errors.append("Email is required")
        if not d.get('Name'):
            self.errors.append("Name is required")
        if not d.get('Password'):
            self.errors.append("Password is required")
        if not d.get('Role'):
            self.errors.append("Role is required")

        # Email format
        if d.get('Email') and not re.match(r"[^@]+@[^@]+\.[^@]+", d['Email']):
            self.errors.append("Invalid email format")

        # Password length
        if d.get('Password') and len(d['Password']) < 6:
            self.errors.append("Password must be at least 6 characters")

        # Role validation
        if d.get('Role') not in ['admin', 'professor']:
            self.errors.append("Invalid role - must be 'admin' or 'professor'")

        # Check if email in use
        temp_u = user()
        temp_u.getByField('Email', d['Email'])
        if len(temp_u.data) > 0:
            self.errors.append("Email already in use")

        return len(self.errors) == 0

    def insert(self):
        if not self.verify_new():
            return False

        d = self.data[0]
        # d['Password'] = generate_password_hash(d['Password'], method='pbkdf2:sha256')  # Disabled for plain text
        return super().insert()

    def verify_update(self):
        self.errors = []
        if not self.data or len(self.data) == 0:
            self.errors.append("No data provided")
            return False

        d = self.data[0]

        # Required for update
        if 'UserID' not in d:
            self.errors.append("UserID required for update")

        # Email format if updating
        if d.get('Email') and not re.match(r"[^@]+@[^@]+\.[^@]+", d['Email']):
            self.errors.append("Invalid email format")

        # Password if updating
        if d.get('Password') and len(d['Password']) < 6:
            self.errors.append("Password must be at least 6 characters")

        # Role if updating
        if d.get('Role') and d['Role'] not in ['admin', 'professor']:
            self.errors.append("Invalid role")

        # Check email uniqueness if changing
        if d.get('Email'):
            temp_u = user()
            temp_u.getByField('Email', d['Email'])
            if len(temp_u.data) > 0 and temp_u.data[0]['UserID'] != d['UserID']:
                self.errors.append("Email already in use")

        return len(self.errors) == 0

    def update(self):
        if not self.verify_update():
            return False

        d = self.data[0]
        # if 'Password' in d:
        #     d['Password'] = generate_password_hash(d['Password'], method='pbkdf2:sha256')  # Disabled for plain text
        return super().update()

    def tryLogin(self, email, pw):
        self.getByField('Email', email)
        if len(self.data) == 0:
            return False
        # return check_password_hash(self.data[0]['Password'], pw)  # Disabled; use plain text compare
        return self.data[0]['Password'] == pw  # Plain text comparison (insecure for prod!)

    def changePassword(self, new_password):
        if not self.data or len(self.data) == 0:
            self.errors.append("No user loaded")
            return False

        if len(new_password) < 6:
            self.errors.append("New password must be at least 6 characters")
            return False

        # hashed = generate_password_hash(new_password, method='pbkdf2:sha256')  # Disabled
        hashed = new_password  # Plain text
        user_id = self.data[0]['UserID']
        sql = "UPDATE `users` SET `Password` = %s WHERE `UserID` = %s"
        self.cur.execute(sql, (hashed, user_id))
        self.conn.commit()
        self.data[0]['Password'] = hashed
        return True

# Quick test when running file directly
if __name__ == '__main__':
    print("Testing user model...")
    u = user()

    # Test login with one of your existing accounts
    if u.tryLogin('admin@far-system.edu', 'admin123'):
        print("LOGIN SUCCESS (admin)")
        print("User data:", u.data[0])
    else:
        print("Login failed - check email/password or config")

    # Show config status
    print("Config table name:", u.tn)