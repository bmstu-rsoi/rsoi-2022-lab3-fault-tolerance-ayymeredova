import psycopg2
from psycopg2 import Error


class PaymentDB():
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host="postgres",
                database="payments",
                user='program',
                password='test',
                port="5432")

            self.cur = self.conn.cursor()
        except(Error, Exception) as e:
            raise(e)
        

    def check_payment_db(self):
        print("init migration")
        
        # self.cur.execute('DROP TABLE IF EXISTS payments;')
    
        self.cur.execute("""CREATE TABLE IF NOT EXISTS payments
        (
            id          SERIAL PRIMARY KEY,
            payment_uid uuid        NOT NULL,
            status      VARCHAR(20) NOT NULL
                CHECK (status IN ('PAID', 'CANCELED')),
            price       INT         NOT NULL
        );""")

        self.cur.execute(""" INSERT INTO payments
        (
            payment_uid,
            status,
            price
        )
        VALUES(
            '753f5bf8-73d0-11ed-a67e-00155dec5d05',
            'PAID',
            200000
            ) ON CONFLICT DO NOTHING;
        """)

        self.cur.execute(""" INSERT INTO payments
        (
            payment_uid,
            status,
            price
        )
        VALUES(
            '7ffe9644-73d0-11ed-a67f-00155dec5d05',
            'CANCELED',
            400000
            ) ON CONFLICT DO NOTHING;
        """)


        self.conn.commit()

        self.cur.close()
        self.conn.close()
            
        print("finish migration")
        
