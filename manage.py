import click
from flask.cli import with_appcontext
from app import create_app
from app.models import User, Role
from getpass import getpass
import uuid

app = create_app()

@click.group()
def cli():
    """Management commands for the application."""
    pass

@click.command("create-admin")
@with_appcontext
def create_admin():
    """Creates the initial admin user and role."""
    from flask_security.utils import hash_password

    print("--- Creating Initial Admin User ---")
    
    # Check for existing admin role/user
    admin_role = Role.objects(name="admin").first()
    if not admin_role:
        admin_role = Role(name="admin", description="Administrator").save()
        print("'admin' role created.")

    email = input("Enter admin email: ")
    if User.objects(email=email).first():
        print(f"Error: User with email {email} already exists.")
        return

    password = getpass("Enter admin password: ")
    password_confirm = getpass("Confirm admin password: ")

    if password != password_confirm:
        print("Error: Passwords do not match.")
        return

    user = User(
        email=email,
        password=hash_password(password),
        fs_uniquifier=str(uuid.uuid4()),
        active=True,
        approved=True, # Admins are pre-approved
        roles=[admin_role]
    ).save()

    print(f"\nAdmin user '{email}' created successfully!")

cli.add_command(create_admin)

@click.command("create-test-users")
@with_appcontext
def create_test_users():
    """Creates a set of test users with different roles."""
    from flask_security.utils import hash_password
    from app import security # Import the security object

    print("--- Creating Test Users ---")

    # Define roles
    roles = {
        "admin": "Administrator with full access",
        "editor": "Can edit documents and playbooks",
        "viewer": "Can only view documents"
    }
    for role_name, role_desc in roles.items():
        if not security.datastore.find_role(role_name):
            security.datastore.create_role(name=role_name, description=role_desc)
            print(f"Role '{role_name}' created.")

    # Define users
    users = [
        {"email": "admin@example.com", "password": "password", "roles": ["admin"]},
        {"email": "editor@example.com", "password": "password", "roles": ["editor"]},
        {"email": "viewer@example.com", "password": "password", "roles": ["viewer"]}
    ]

    for user_data in users:
        if not security.datastore.find_user(email=user_data["email"]):
            security.datastore.create_user(
                email=user_data["email"],
                password=hash_password(user_data["password"]),
                roles=user_data["roles"]
            )
            print(f"User '{user_data['email']}' created.")
        else:
            print(f"User '{user_data['email']}' already exists.")

    print("\nTest user creation complete!")

cli.add_command(create_test_users)

if __name__ == "__main__":
    with app.app_context():
        cli()
