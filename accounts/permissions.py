
def user_has_permission(user, permission):
    """
    Check whether a user has a hospital permission.

    Django superusers and users assigned the Administrator
    hospital role automatically have all hospital permissions.
    Other users must have the individual permission enabled
    on their hospital role.
    """

    if not user.is_authenticated:
        return False

    # Django superusers have full access to the hospital EMR.
    if user.is_superuser:
        return True

    try:
        user_role = user.hospital_role
        role = user_role.role
    except Exception:
        # No hospital role is assigned to this user.
        return False

    # The hospital Administrator role has full EMR access.
    role_name = role.name.strip().casefold()

    if role_name in {"administrator", "admin"}:
        return True

    # All other roles must have the requested permission enabled.
    return bool(getattr(role, permission, False))
