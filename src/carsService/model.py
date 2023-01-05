from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass
from uuid import uuid4
db = SQLAlchemy()


@dataclass
class CarModel(db.Model):
    id:int
    car_uid:uuid4
    brand:str
    model: str
    registration_number:str
    power: int
    price: int
    type: str
    availability: bool

    __tablename__ = 'cars'
    id = db.Column(db.Integer, primary_key=True)
    car_uid = db.Column(db.String(36), nullable = False, default=lambda: str(uuid4()))
    brand = db.Column(db.String(80), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    power = db.Column(db.Integer, nullable=False)
    availability = db.Column(db.Boolean, nullable=False)
    type = db.Column(db.String(80), nullable=False)
    # date_from = db.Column(db.Date, nullable=False)
    # date_to = db.Column(db.Date, nullable=False)
    # status=db.Column(db.Boolean, nullable=False)
    registration_number=db.Column(db.String(80), nullable=False)


    def to_dict(self):
        return {
            "carUid": str(self.car_uid),
            "brand": str(self.brand),
            "model": str(self.model),
            "registrationNumber": str(self.registration_number),
            "power": self.power,
            "type": str(self.type),
            "price": self.price,
            "available": bool(self.availability)
        }

    class Meta:
        db_table = "cars"