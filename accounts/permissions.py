def user_has_permission(user, permission):
    if not user.is_authenticated:
        return False

    try:
        user_role = user.hospital_role
    except Exception:
        return False

    return getattr(user_role.role, permission, False)
