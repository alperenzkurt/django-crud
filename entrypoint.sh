#!/bin/sh

# Wait for postgres
echo "Waiting for PostgreSQL..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

# Make migrations for any model changes
echo "Making migrations for model changes..."
python manage.py makemigrations

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Create default superuser if it doesn't exist
echo "Creating default superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.accounts.models import Team
User = get_user_model()

team, created = Team.objects.get_or_create(
    name='Montaj Takımı',
    defaults={'team_type': 'assembly'}
)
if created:
    print('Team created')

# Create admin user if it doesn't exist
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@example.com', '123456')
    user.first_name = 'Admin'
    user.last_name = 'User'
    user.team = team
    user.save()
    print('Superuser created successfully with name and team')
else:
    # Update existing admin user if it exists
    user = User.objects.get(username='admin')
    if user.team is None:
        user.team = team
        user.save()
        print('Existing admin user updated with team')
    print('Admin user already exists')
"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start server
echo "Starting server..."
exec gunicorn --bind 0.0.0.0:8000 aircraft_production.wsgi 