#!/bin/bash

# Variables (modify as needed)
DB_NAME=$PGDATABASE
DB_USER=$PGUSER
DB_PASSWORD=$PGPASSWORD

# Ensure the script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root or use sudo."
    exit 1
fi

# Initialize PostgreSQL (only if not already initialized)
if [ ! -d "/var/lib/postgresql/data" ]; then
    echo "Initializing PostgreSQL..."
    sudo -u postgres initdb -D /var/lib/postgresql/data
fi

# Start PostgreSQL service
echo "Starting PostgreSQL service..."
systemctl start postgresql

# Create the user with password
#sudo useradd -m -s /bin/bash $DB_USER
sudo -u postgres psql -c "CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';"

# Create a New Database Owned by the User:
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Grant privileges to the user
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Configure Schema Permissions:
sudo -u postgres psql -d $DB_NAME -c "GRANT USAGE ON SCHEMA public TO $DB_USER;"
sudo -u postgres psql -d $DB_NAME -c "GRANT CREATE ON SCHEMA public TO $DB_USER;"

# Verify the database and user creation
echo "Listing databases:"
sudo -u postgres psql -c "\l"

# Verify the Setup:
psql -U $DB_USER -d $DB_NAME -h localhost -W

echo "PostgreSQL setup complete!"

