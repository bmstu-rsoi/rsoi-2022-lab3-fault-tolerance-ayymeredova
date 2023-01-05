from email import message
import os 
import sys
from marshmallow import ValidationError
import psycopg2
from flask import Flask, request, flash, redirect
from flask_migrate import Migrate
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with, url_for
from flask_sqlalchemy import SQLAlchemy
from paymentDB import PaymentDB
# from utils import make_data_response, make_empty
from flask import send_from_directory, jsonify, make_response
from sqlalchemy import exc
from model import PaymentModel, db
from uuid import uuid4
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://program:test@postgres:5432/payments"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

# migrate = Migrate(app)

port = os.environ.get('PORT')
if port is None:
    port = 8050

@app.errorhandler(404)



def make_data_response(status_code, **kwargs):
    response = jsonify({
            **kwargs
        })
    response.status_code = status_code
    return response

def make_empty(status_code):
    response = make_response()
    response.status_code = status_code
    del response.headers["Content-Type"]
    del response.headers["Content-Length"]
    return response

@app.route('/favicon.ico') 
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')

#жив или не жив наш герой?
@app.route('/manage/health', methods=['GET'])
def health():
    return make_response(jsonify({}), 200)

@app.route("/api/v1/payments/<string:payment_uid>", methods = ["GET"])
def get_payment(payment_uid):
        result=PaymentDB.session.query(PaymentModel).filter(PaymentModel.rental_uid==payment_uid).one_or_none()
        if not result:
            abort(404)
        return make_response(jsonify(result), 200)

@app.route("/api/v1/payments/<string:payment_uid>", methods = ["DELETE"])
def delete_payment(payment_uid):
    payment = PaymentDB.session.query(PaymentModel).filter(PaymentModel.rental_uid==payment_uid).one_or_none()
    payment.status = 'CANCELED'

    try:
        db.session.commit()
        return make_empty(204)
    except:
        db.session.rollback()
        return make_data_response(500, message="Database delete error")

@app.route('/api/v1/payments/', methods = ['POST'])
def post_payment():
    try:
        if request.is_json:
            data = request.get_json()
            new_payment = PaymentModel(
                payment_uid=str(uuid4()),
                price=data["price"]
            )
    except ValidationError:
            return make_response(400, message="Bad JSON format")

    try:
        db.session.add(new_payment)
        db.session.commit()


    except:
        db.session.rollback()
        return make_data_response(500,  message="Database delete error")

    response = make_empty(201)
    response.headers["Location"] = f"/api/v1/payment/{new_payment.id}"
    return response


if __name__ == '__main__':
    paymentdb = PaymentDB()
    paymentdb.check_payment_db()
    app.run(host='0.0.0.0', port=8050)

    





