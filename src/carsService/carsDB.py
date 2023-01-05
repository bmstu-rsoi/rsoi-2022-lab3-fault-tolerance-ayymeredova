import psycopg2
from psycopg2 import Error

class CarDB():
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host="postgres",
                database="cars",
                user='program',
                password='test',
                port="5432")

            self.cur = self.conn.cursor()
        except(Error, Exception) as e:
            raise(e)
        

    def check_cars_db(self):
        print("init migration")
        
        self.cur.execute('DROP TABLE IF EXISTS cars;')
    
        self.cur.execute("""CREATE TABLE cars
        (
            id                  SERIAL PRIMARY KEY,
            car_uid             uuid UNIQUE NOT NULL,
            brand               VARCHAR(80) NOT NULL,
            model               VARCHAR(80) NOT NULL,
            registration_number VARCHAR(20) NOT NULL,
            power               INT,
            price               INT         NOT NULL,
            type                VARCHAR(20)
                CHECK (type IN ('SEDAN', 'SUV', 'MINIVAN', 'ROADSTER')),
            availability        BOOLEAN     NOT NULL
        );""")

        self.cur.execute(""" INSERT INTO cars
        (
            id,
            car_uid,
            brand,
            model,
            registration_number,
            power,
            price, 
            type,
            availability
        )
        VALUES(
            1,
            'd0ad8de2-73d6-11ed-a680-00155dec5d05',
            'AUDI',
            'M5',
            0001,
            100, 
            3000000,
            'ROADSTER',
            true
            );
        """)

        self.cur.execute(""" INSERT INTO cars
        (
            id,
            car_uid,
            brand,
            model,
            registration_number,
            power,
            price, 
            type,
            availability
        )
        VALUES(
            2,
            '2581d076-73d7-11ed-a681-00155dec5d05',
            'BMW',
            'G6',
            0002,
            400, 
            6000000,
            'SEDAN',
            false
            );
        """)
        

        self.conn.commit()

        self.cur.close()
        self.conn.close()

    