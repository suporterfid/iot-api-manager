# Django RFID Reader Management and Tag Event Application

This Django application is designed to manage R700 RFID readers and process tag events received from those readers. The application provides a user interface (UI) to create, list, update, and delete records for R700 RFID readers. It also allows the user to manage inventory presets on the readers, start and stop these presets, and handle incoming tag events via webhooks. Additionally, the application includes authentication features, ensuring that only authorized users can access the system. This software was not developed with the intention of being used in production environments; it is only an example of how to communicate with reader APIs and receive events.

## Features

- **Reader Management**: Create, list, update, and delete RFID reader records, including serial number, name, IP address, port, username, and password.
- **Preset Management**: Query, create, update, delete, and manage multiple presets per reader. Only one preset can be active at a time. The presets can be configured and sent to the readers via the API.
- **Preset Control**: Start and stop inventory presets on RFID readers directly from the UI.
- **Tag Event Handling**: Receive, store, and display tag events via webhooks, with filtering options by reader and date range.
- **Authentication**: Secure the application using Django's built-in authentication system, requiring users to log in before accessing the application.
- **UI Enhancements**: Responsive design using Bootstrap, with features like tooltips, icons, sortable columns, and modals for detailed event views.

## Technologies Used

- **Python**: The core language for the application.
- **Django**: The web framework used to build the application.
- **Bootstrap**: Used for the responsive UI design.
- **SQLite**: Default database used for storing reader and tag event records (can be replaced with other databases like PostgreSQL).
- **Docker**: Containerization for easy deployment.
- **Docker Compose**: Tool for defining and running multi-container Docker applications.

## Prerequisites

- **Docker**: Ensure Docker is installed on your system. You can download it from [Docker's official site](https://www.docker.com/get-started).
- **Docker Compose**: Ensure Docker Compose is installed. It usually comes with Docker Desktop.

## Setup and Running the Application

### 1. Clone the Repository

```bash
git clone https://github.com/suporterfid/iot-api-manager.git
cd iot-api-manager
```

### 2. Environment Configuration

The application uses environment variables to configure database settings, secret keys, and more. Ensure you have a ``.env`` file configured in the project root with necessary environment variables.

### 3. Running the Application with Docker Compose

To build and run the application with Docker Compose:
```bash
docker-compose up --build
```

This command will:

- Build the Docker image for the Django application.
- Start the Django application along with a PostgreSQL database (or any other services you define in docker-compose.yml).
The application will be accessible at ``http://localhost:8000``.

### 4. Running Database Migrations

After the application is up, you need to run the database migrations:
```bash
docker-compose exec web python manage.py migrate
```

### 5. Creating a Superuser (for Admin Access)

To create an admin user:
```bash
docker-compose exec web python manage.py createsuperuser --username=admin --email=admin@example.com --noinput
```
Follow the prompts to create your superuser account.

### 6. Accessing the Admin Interface
You can access the Django admin interface at ``http://localhost:8000/admin`` using the superuser credentials.

### 7. Accessing the Application
Readers: Manage readers at ``http://localhost:8000/readers/``.
Tag Events: View and filter tag events at ``http://localhost:8000/tags/``.
Presets: Manage presets associated with readers at ``http://localhost:8000/reader/<reader_id>/presets/``.


## Docker Compose Configuration

``docker-compose.yml``

The Docker Compose file is configured to run the Django application and the PostgreSQL database. Here’s a basic overview:
```yaml
version: '3.8'

services:
  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - rabbitmq

  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: django_db
      POSTGRES_USER: django_user
      POSTGRES_PASSWORD: django_password
    ports:
      - "5432:5432"

  rabbitmq:
    image: rabbitmq:3-management
    environment:
      RABBITMQ_DEFAULT_USER: user
      RABBITMQ_DEFAULT_PASS: password
    ports:
      - "5672:5672"  # Default RabbitMQ port
      - "15672:15672"  # RabbitMQ Management UI

  worker:
    build: .
    command: celery -A config worker -l info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - rabbitmq
      - db

volumes:
  postgres_data:
```

### Customization

- Database: You can customize the database service in the docker-compose.yml file. Replace PostgreSQL with MySQL or any other supported database if needed.
- Environment Variables: Modify the .env file to set environment variables specific to your setup (e.g., secret keys, database credentials).

### Debugging

If you encounter any issues, you can access the logs for the web and database services using:
```bash
docker-compose logs web
docker-compose logs db
```

### Stopping the Application

To stop the application, run:
```bash
docker-compose down
```
This will stop and remove the containers but will preserve the database volume.

### Cleaning Up
To remove the containers, networks, and volumes associated with the project:
```bash
docker-compose down -v
```

## Contributing
If you would like to contribute to this project, please fork the repository and submit a pull request. Your contributions are welcome!

## WARRANTY DISCLAIMER

This software is provided “as is” without quality check, and there is no warranty that the software will operate without error or interruption or meet any performance standard or other expectation. All warranties, express or implied, including the implied warranties of merchantability, non-infringement, quality, accuracy, and fitness for a particular purpose are expressly disclaimed. The developers of this software are not obligated in any way to provide support or other maintenance with respect to this software.

## LIMITATION OF LIABILITY

The total liability arising out of or related to the use of this software will not exceed the total amount paid by the user for this software, which in this case is zero as the software is provided free of charge. In no event will the developers have liability for any indirect, incidental, special, or consequential damages, even if advised of the possibility of these damages. These limitations will apply notwithstanding any failure of essential purpose of any limited remedy provided.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.