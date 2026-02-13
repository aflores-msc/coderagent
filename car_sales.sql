-- Create the tables for the Car Sales Agency

CREATE TABLE cars (
    car_id INT64 OPTIONS(description="Unique identifier for the car"),
    vin STRING OPTIONS(description="Vehicle Identification Number"),
    make STRING OPTIONS(description="Car manufacturer (e.g., Toyota, Ford)"),
    model STRING OPTIONS(description="Car model name"),
    year INT64 OPTIONS(description="Manufacturing year"),
    color STRING OPTIONS(description="Exterior color"),
    price NUMERIC OPTIONS(description="Listing price of the car"),
    status STRING OPTIONS(description="Current status: 'Available', 'Sold', 'Maintenance'")
);

CREATE TABLE clients (
    client_id INT64 OPTIONS(description="Unique identifier for the client"),
    first_name STRING OPTIONS(description="Client's first name"),
    last_name STRING OPTIONS(description="Client's last name"),
    email STRING OPTIONS(description="Contact email address"),
    phone STRING OPTIONS(description="Contact phone number"),
    registration_date TIMESTAMP OPTIONS(description="Date when the client was registered")
);

CREATE TABLE employees (
    employee_id INT64 OPTIONS(description="Unique identifier for the employee"),
    first_name STRING OPTIONS(description="Employee's first name"),
    last_name STRING OPTIONS(description="Employee's last name"),
    role STRING OPTIONS(description="Job title (e.g., 'Sales Manager', 'Junior Salesperson')"),
    hire_date DATE OPTIONS(description="Date the employee was hired")
);

CREATE TABLE sales (
    sale_id INT64 OPTIONS(description="Unique identifier for the sale transaction"),
    car_id INT64 OPTIONS(description="Foreign key referencing cars.car_id"),
    client_id INT64 OPTIONS(description="Foreign key referencing clients.client_id"),
    employee_id INT64 OPTIONS(description="Foreign key referencing employees.employee_id"),
    sale_date TIMESTAMP OPTIONS(description="Date and time when the sale occurred"),
    final_price NUMERIC OPTIONS(description="The actual price the car was sold for"),
    payment_method STRING OPTIONS(description="Method of payment: 'Cash', 'Financing', 'Lease'")
);
