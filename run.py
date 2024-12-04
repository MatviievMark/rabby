from app import create_app, db
from app.models import User
import os

app = create_app()

def init_db():
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Check if we need to create a test user
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password='admin123'  # In production, use a secure password
            )
            db.session.add(admin_user)
            db.session.commit()
            print('Created admin user - Username: admin, Password: admin123')

if __name__ == '__main__':
    # Initialize the database if it doesn't exist
    if not os.path.exists('equipment.db'):
        print('Initializing database...')
        init_db()
        print('Database initialized successfully!')
    
    # Run the application
    app.run(debug=True)