# Bowling Shoes Rental Service with LLM Integration and Prompt Engineering

## Project Overview

This project is a minimal backend service for managing a bowling shoe rental operation. The service handles basic customer registrations, shoe rentals, and fee calculations, including discounts based on customer age and other criteria. An LLM model (Lamini) is used to determine applicable discounts based on customer information. Supabase is used as the database and Docker is used for containerization.

## Features

- **Customer Management**: Add and retrieve customer records.
- **Shoe Rental Management**: Manage shoe rentals, record rental dates, calculate rental fees, and apply discounts.
- **Discount Calculation**: Use Lamini LLM to determine discounts based on age, disability status, and pre-existing medical conditions.
- **Database Setup with Supabase**: Create and manage necessary database tables.
- **Containerization with Docker**: Ensure the application can be easily built and run using Docker.

## Discount Model

The discount model for the bowling shoe rental service is based on the following criteria:

- **Age**:
    - Age 0-12: 20% discount
    - Age 13-18: 10% discount
    - Age 65 and above: 15% discount
- **Disability Status**:
    - Disabled: 25% discount
- **Pre-existing Medical Conditions**:
    - Diabetes: 10% discount
    - Hypertension: 10% discount
    - Chronic Condition: 10% discount

## Getting Started

### Prerequisites

- Docker
- Docker Compose
- Supabase account and API key
- Lamini API key

### Environment Variables

Create a `.env` file in the root directory and add the following:

```
SUPABASE_URL=your_supabase_url
SUPABASE_API_KEY=your_supabase_api_key
LLM_API_KEY=your_lamini_api_key
```

### Directory Structure

```markdown
markdownCopy code
project-root/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── crud.py
│   ├── database.py
│   ├── schemas.py
│   └── endpoints/
│       ├── __init__.py
│       ├── customers.py
│       └── rentals.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env

```

### Installation

1. **Clone the repository**:
    
    ```bash
    bashCopy code
    git clone https://github.com/Rajiv-Rago/Bowling-Shoes-Rental-Service.git
    cd bowling-shoes-rental
    
    ```
    
2. **Run the application with Docker**:
    
    ```bash
    bashCopy code
    docker-compose up --build
    
    ```
    

### Accessing the Application

- **Local Access**: Open your web browser and navigate to `http://localhost:8000`.
- **API Documentation**:
    - Swagger UI: `http://localhost:8000/docs`
    - ReDoc: `http://localhost:8000/redoc`

### Example Endpoints

- **Create Customer**:
    
    ```bash
    bashCopy code
    curl -X POST "http://localhost:8000/customers/add?name=John%20Doe&age=30&contact_info=john@example.com&is_disabled=n&medical_conditions=none" -H "accept: application/json"
    
    ```
    
- **Get Customers**:
    
    ```bash
    bashCopy code
    curl -X POST "http://localhost:8000/customers/get?name=John%20Doe" -H "accept: application/json"

    
    ```
    

### Connecting to Supabase

Ensure your Supabase database URL and API key are correctly set in the `.env` file. The application uses these credentials to connect to the Supabase database.

Once set up, go to supabase and open its SQL Editor on the navigation bar. Copy the contents of script.sql, which can be found in the root directory. And, finally, run the script.

### Using Lamini for LLM Integration

The Lamini API key is also set in the `.env` file. The application uses this key to interact with Lamini for discount calculation based on customer data.

## Contributing

1. **Fork the repository**.
2. **Create a new branch**: `git checkout -b feature/your-feature`.
3. **Commit your changes**: `git commit -m 'Add some feature'`.
4. **Push to the branch**: `git push origin feature/your-feature`.
5. **Create a new Pull Request**.

## Contact

For any questions or suggestions, please contact:

- **Email**: ragorajiv2@gmail.com