from rest_framework import permissions

class CanManagePart(permissions.BasePermission):
    """
    Custom permission to only allow appropriate team members to manage parts.
    """
    
    def has_permission(self, request, view):
        # User must be authenticated and have a team
        if not request.user.is_authenticated or not request.user.team:
            return False
            
        # Assembly team members cannot create parts
        if view.action == 'create' and request.user.team.team_type == 'assembly':
            return False
            
        return True
        
    def has_object_permission(self, request, view, obj):
        # User must be authenticated and have a team
        if not request.user.is_authenticated or not request.user.team:
            return False
            
        # Assembly team can view any part but not modify them
        if request.user.team.team_type == 'assembly':
            return request.method in permissions.SAFE_METHODS
            
        # Only the team that created the part can update or delete it
        return obj.team == request.user.team 