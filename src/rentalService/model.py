from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass
from uuid import uuid4
db = SQLAlchemy()


@dataclass
class RentalModel(db.Model):
    id:int
    rental_uid:uuid4
    username:str
    payment_uid: uuid4
    car_uid: uuid4
    date_from:str
    date_to: str 
    status: bool

    __tablename__ = 'rentals'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rental_uid = db.Column(db.String(36), nullable = False, default=lambda: str(uuid4()))
    username = db.Column(db.String(80), nullable=False)
    payment_uid = db.Column(db.String(36),nullable = False)
    car_uid = db.Column(db.String(36), nullable = False)
    date_from = db.Column(db.Date, nullable=False)
    date_to = db.Column(db.Date, nullable=False)
    status=db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {
            "rentalUid": str(self.rental_uid),
            "username": str(self.username),
            "paymentUid": str(self.payment_uid),
            "carUid": str(self.car_uid),
            "dateFrom": self.date_from.strftime("%Y-%m-%d"),
            "dateTo": self.date_to.strftime("%Y-%m-%d"),
            "status": str(self.status)
        }

    class Meta:
        db_table = "rentals"