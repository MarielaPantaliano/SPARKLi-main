from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.shortcuts import redirect
import json

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the last activity time from the session and convert it back to datetime
        last_activity_str = request.session.get('last_activity')
        
        if last_activity_str:
            try:
                last_activity = timezone.datetime.fromisoformat(last_activity_str)
            except ValueError:
                # Handle the case where the last_activity is not a valid ISO format
                last_activity = None

            if last_activity:
                now = timezone.now()
                inactivity_period = now - last_activity

                # Check if the inactivity period exceeds the timeout limit
                if inactivity_period > timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES):
                    # Clear the session if it has expired
                    request.session.flush()
                    # Redirect to login page or show timeout message
                    return redirect('login_page')
        
        # Update the last activity time and convert it to ISO format
        request.session['last_activity'] = timezone.now().isoformat()
        response = self.get_response(request)
        return response
