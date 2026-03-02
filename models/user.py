# models/user.py
from .baseObject import baseObject
from werkzeug.security import generate_password_hash, check_password_hash
import re

class user(baseObject):
    def __init__(self):
        super().__init__()

    def verify_new(self):
        """Validate new user data before insert/update."""
        self.errors = []
        if not self.data or len(self.data) == 0:
            self.errors.append("No data provided")
            return False

        d = self.data[0]

        # Required fields
        if not d.get('Email'):
            self.errors.append("Email is required")
        if not d.get('Name'):
            self.errors.append("Name is required")
        if not d.get('Password'):
            self.errors.append("Password is required")

        # Email format check
        if d.get('Email') and not re.match(r"[^@]+@[^@]+\.[^@]+", d['Email']):
            self.errors.append("Invalid email format")

        # Password length
        if d.get('Password') and len(d['Password']) < 6:
            self.errors.append("Password must be at least 6 characters")

        # Role validation
        if d.get('Role') not in ['admin', 'professor']:
            self.errors.append("Role must be 'admin' or 'professor'")

        # Email uniqueness (skip if this is an update of existing user)
        if 'UserID' not in d or not d.get('UserID'):
            test = user()
            test.getByField('Email', d['Email'])
            if len(test.data) > 0:
                self.errors.append("Email already in use")

        return len(self.errors) == 0

    def hash_password(self):
        """Hash the password if it's plain text."""
        if not self.data or len(self.data) == 0:
            return

        d = self.data[0]
        if 'Password' in d and d['Password']:
            pw = d['Password']
            # Only hash if it doesn't already look like a bcrypt/argon2 hash
            if not (pw.startswith('$2b$') or pw.startswith('$argon2')):
                d['Password'] = generate_password_hash(pw)

    def create(self):
        """Verify data, hash password, and insert new user."""
        if self.verify_new():
            self.hash_password()
            self.insert()
            return True
        return False

    def tryLogin(self, email, password):
        """Attempt login. Returns True and loads user data if successful."""
        self.data = []
        sql = "SELECT * FROM `users` WHERE `Email` = %s"
        self.cur.execute(sql, (email,))
        row = self.cur.fetchone()

        if not row:
            return False

        stored_pw = row['Password']

        # Support both plain-text (legacy/test) and hashed passwords
        if stored_pw.startswith('$2b$') or stored_pw.startswith('$argon2'):
            # Hashed password
            if check_password_hash(stored_pw, password):
                self.data.append(row)
                return True
        else:
            # Plain text (temporary - for your existing test users)
            if stored_pw == password:
                self.data.append(row)
                return True

        return False

    def update_password(self, new_password):
        """Change password for the current loaded user (hashed)."""
        if not self.data or len(self.data) == 0:
            self.errors.append("No user loaded")
            return False

        hashed = generate_password_hash(new_password)
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