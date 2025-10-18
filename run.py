from nieuwburg import create_app, db
from nieuwburg.models import User, Profile

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Create the database tables if they don't exist
        db.create_all()

        # Create a default admin user if one doesn't exist
        if not User.query.filter_by(email='admin@example.com').first():
            print("Creating default admin user...")
            admin_user = User(
                email='admin@example.com',
                role='admin',
                is_confirmed=True
            )
            admin_user.set_password('password')
            db.session.add(admin_user)

            # Also create a profile for the admin user
            db.session.add(Profile(user=admin_user, full_name='Admin User'))
            db.session.commit()
            print("Default admin user created with email 'admin@example.com' and password 'password'.")

    app.run(debug=True)