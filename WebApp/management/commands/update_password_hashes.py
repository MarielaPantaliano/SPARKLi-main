from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Update password hashes for all users with incorrect format'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        users = User.objects.all()
        
        for user in users:
            password = user.password
            if password.count('$') == 1:  # Detecting incorrect format
                new_password = 'new_default_password'  # Or fetch securely
                user.password = make_password(new_password)
                user.save()
                self.stdout.write(f'Updated password hash for user {user.email}')
        
        self.stdout.write('Password hash update completed.')
