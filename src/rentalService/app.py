from email import message
import os 
import sys
from marshmallow import ValidationError
import psycopg2
from flask import Flask, request, flash, redirect
from flask_migrate import Migrate
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with, url_for
from flask_sqlalchemy import SQLAlchemy
from rentalDB import RentalDB
# from utils import make_data_response, make_empty
from flask import send_from_directory, jsonify, make_response, Response
from sqlalchemy import exc
from model import RentalModel, db
import uuid
import datetime
import json

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://program:test@postgres:5432/rentals"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

migrate = Migrate(app)

port = os.environ.get('PORT')
if port is None:
    port = 8060

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

@app.route("/api/v1/rental/<string:rentalUid>", methods = ["GET"])
def get_all_rentals_user(rental_uid):
    result=db.session.query(RentalModel).filter(RentalModel.rental_uid==rental_uid).one_or_none()
    if not result:
        abort(404)
    return make_response(jsonify(result), 200)


@app.route("/api/v1/rental/<string:rentalUid>", methods = ["DELETE"])
def delete_one_rental(rentalUid):
    rental = db.session.query(RentalModel).filter(RentalModel.rental_uid==rentalUid).one_or_none()
    if rental.status != "IN_PROGRESS":
        return Response(
            status=403,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Rental not in progres.']
                })
        )
    rental.status = 'CANCELED'

    rental.save()

    try:
        db.session.commit()
        return make_empty(204)
    except:
        db.session.rollback()
        return make_data_response(500, message="Database delete error")
    # return make_empty(204)



@app.route("/api/v1/rental/", methods = ["GET", "POST"])
def get_all_rental():
    if request.method == 'GET':
        if 'X-User-Name' not in request.headers.keys():
            return Response(
                status=400,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Request has not X-User-Name header!']
                })
            )
        user = request.headers['X-User-Name']
        rental_list = db.session.query(RentalModel).filter(RentalModel.username==user).all()
        # rentals = [rental.to_dict() for rental in RentalModel.select().where(RentalModel.username == user)]
        rentals = [rental.to_dict() for rental in rental_list]
        # result=RentalModel.query.all()
        # if not result:
        #     abort(404)
        return make_response(jsonify(rentals), 200)

    if request.method == "POST":
        try:
            if 'X-User-Name' not in request.headers.keys():
                return Response(
                    status=400,
                    content_type='application/json',
                    response=json.dumps({
                        'errors': ['Request has not X-User-Name header!']
                    })
                )
            if request.is_json:
                user = request.headers['X-User-Name']
                data = request.get_json()
                new_rental = RentalModel(
                    rental_uid = str(uuid.uuid4),
                    username = user,
                    car_uid = uuid.UUID(data["car_uid"]),
                    date_from = datetime.datetime.strptime(data['dateFrom'], "%Y-%m-%d").date(),
                    date_to = datetime.datetime.strptime(data['dateTo'], "%Y-%m-%d").date(),
                    status = "IN_PROGRESS",
                )
            
        except ValidationError as error:
            return make_response(400, message="Bad JSON format")
    
        try:
            db.session.add(new_rental)
            db.session.commit()
            # return make_data_response(200, message="Successfully added new person: name: {}, address: {}, work: {}, age: {} ".format(new_person.name, 
            # new_person.address, new_person.work, new_person.age))
        except:
            db.session.rollback()
            return make_data_response(500, message="Database add error!")

    response = make_empty(201)
    response.headers["Location"] = f"/api/v1/rental/{new_rental.id}"
    return response

@app.route('/api/v1/rental/<string:rentalUid>/finish', methods=["POST"])
def post_rental_finish(rentaluid):
    try:
        rental = db.session.query(RentalModel).filter(RentalModel.rental_uid==rentaluid).one_or_none()
        if rental.status != "IN_PROGRESS":
            return Response(
                status=403,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Rental not in progres.']
                })
            )
        rental.status = "FINISHED"
        try:
            db.session.commit()
            # return make_empty(204)
            
            return Response(
                    status=204,
                    content_type='application/json',
                    response=json.dumps(rental.to_dict())
                )
        except:
            db.session.rollback()
            return make_data_response(500, message="Database delete error")

        # return Response(
        #         status=204,
        #         content_type='application/json',
        #         response=json.dumps(rental.to_dict())
        #     )
    except Exception as e:
        return Response(
            status=404,
            content_type='application/json',
            response=json.dumps({
                'errors': ['Uid not found in base.']
            })
        )




if __name__ == '__main__':
    rentalDb = RentalDB()
    rentalDb.check_rental_db()
    app.run(host='0.0.0.0', port=8060)

