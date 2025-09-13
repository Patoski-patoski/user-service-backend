# User Service

This is the user service for a scalable e-commerce platform. It handles user registration, authentication, and profile management.

## Table of Contents

- [User Service](#user-service)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
  - [Usage](#usage)
    - [Running the Service](#running-the-service)
    - [API Endpoints](#api-endpoints)
      - [Authentication](#authentication)
      - [Profile](#profile)
  - [Technology Stack](#technology-stack)
  - [Contributing](#contributing)
  - [License](#license)

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/patoski-patoski/user-service.git
   ```

2. Navigate to the project directory:

   ```bash
   cd user-service
   ```

3. Create a `.env` file in the root of the project and add the following environment variables:

   ```bash
   SECRET_KEY=your-secret-key
   DATABASE_URL=psql://user_service_user:user_service_password@user-db:5432/user_service_db
   DEBUG=True
   ```

## Usage

### Running the Service

To run the service, use the following command:

```bash
docker-compose up -d --build
```

The service will be available at `http://localhost:8000`.

### API Endpoints

#### Authentication

- `POST /api/users/register/`: Register a new user.
- `GET /api/users/activate/<uuid:token>/`: Activate a user account.
- `POST /api/users/login/`: Log in to get a JWT token.
- `POST /api/users/password/change/`: Change user password.
- `DELETE /api/users/`: Delete user account.
- `POST /api/users/password/reset/`: Reset user password.
- `POST /api/users/social/auth/`: Social authentication.
- `GET /api/users/roles/`: Get user roles.

#### Profile

- `GET /api/users/profile/`: Retrieve user profile (requires authentication).
- `PUT /api/users/profile/`: Update user profile (requires authentication).

## Technology Stack

- [Django](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [Docker](https://www.docker.com/)
- [Celery](https://docs.celeryq.dev/en/stable/)
- [RabbitMQ](https://www.rabbitmq.com/)

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
