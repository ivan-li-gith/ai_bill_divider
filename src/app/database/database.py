import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    DB_HOST = os.environ.get("DB_HOST")
    DB_USER = os.environ.get("DB_USER")
    DB_PASS = os.environ.get("DB_PASS") 
    DB_NAME = os.environ.get("DB_NAME")
    connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}"
    return create_engine(connection_string)

def init_db():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS profiles (
                user_id VARCHAR(255) PRIMARY KEY,
                display_name VARCHAR(255),
                age INT,
                email VARCHAR(255)
        )"""))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS group_list (
                group_id INT AUTO_INCREMENT PRIMARY KEY,
                group_name VARCHAR(255),
                owner_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS group_members (
                group_member_id INT AUTO_INCREMENT PRIMARY KEY,
                group_id INT,
                member_name VARCHAR(255),
                member_email VARCHAR(255),
                user_id VARCHAR(255) NULL,
                role VARCHAR(50) DEFAULT 'member',
                FOREIGN KEY (group_id) REFERENCES group_list(group_id)
        )"""))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bill_history (
                bill_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255),
                group_id INT,
                `Billing Month` VARCHAR(255),
                `Service Name` VARCHAR(255),
                `Service Period` VARCHAR(255),
                `Total Amount Due` DECIMAL(10, 2)
        )"""))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payment_tracker (
                user_id VARCHAR(255),
                group_id INT,
                `Billing Month` VARCHAR(255),
                `Roommate Name` VARCHAR(255),
                `Current Month Split` DECIMAL(10, 2),
                `Rollover Amount` DECIMAL(10, 2),
                `Total Owed` DECIMAL(10, 2),
                `Paid` BOOLEAN
        )"""))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS recurring_expenses (
                recurring_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255),
                group_id INT,
                expense_name VARCHAR(255),
                amount DECIMAL(10, 2),
                billing_day INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES group_list(group_id)
        )"""))