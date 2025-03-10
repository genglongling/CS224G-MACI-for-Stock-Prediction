import auth

print("Testing auth module:")
print("Available functions:", dir(auth))

print("\nTesting sso_login function:")
success, user = auth.sso_login("Google", "test@example.com")
print("Success:", success)
print("User:", user)