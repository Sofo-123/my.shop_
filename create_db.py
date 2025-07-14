from ext import app, db
from models import User

with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="SECURITY").first():
        admin = User(username="SECURITY", password="SECURITY", role="admin", hashed=True)
        db.session.add(admin)
        db.session.commit()
        print("admin წარმატებით შეიქმნა")
