CREATE TABLE public.customers (
    id serial PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL,
    contact_info VARCHAR(255),
    is_disabled BOOLEAN NOT NULL,
    medical_conditions TEXT
);

CREATE TABLE public.rentals (
    id serial PRIMARY KEY,
    customer_id INTEGER REFERENCES public.customers(id),
    rental_date TIMESTAMP NOT NULL,
    shoe_size FLOAT NOT NULL,
    rental_fee FLOAT NOT NULL,
    discount FLOAT NOT NULL,
    total_fee FLOAT NOT NULL
);
