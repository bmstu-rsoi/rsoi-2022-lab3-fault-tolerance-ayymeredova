from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass
from uuid import uuid4

db = SQLAlchemy()


@dataclass
class PaymentModel(db.Model):
    id:int
    payment_uid:uuid4
    status:str
    price:int

    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    payment_uid = db.Column(db.String(36),nullable = False, default=lambda: str(uuid4()))
    status= db.Column(db.String(20), nullable=False)
    price= db.Column(db.Integer, nullable = False)

    def to_dict(self):
        return {
            "paymentUid": str(self.payment_uid),
            "status": str(self.status),
            "price": self.price,
        }

    class Meta:
        db_table = "payments"

