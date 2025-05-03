from .models import ActivityLog

def log_activity(user, activity_type, description, object_id=None, object_type=None):
    """
    Log an activity in the system
    """
    ActivityLog.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        related_object_id=object_id,
        related_object_type=object_type
    )