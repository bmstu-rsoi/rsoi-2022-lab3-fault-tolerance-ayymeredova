from email import message
import os 
import sys
from marshmallow import ValidationError
# import psycopg2
from flask import Flask, flash, redirect
import requests

# from flask_migrate import Migrate
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with, url_for
# from flask_sqlalchemy import SQLAlchemy
# from carsDB import CarDB
# from utils import make_data_response, make_empty
from flask import send_from_directory, jsonify, make_response, json, Response, request
# from sqlalchemy import exc
# from model import CarModel, db
import uuid
import datetime


app = Flask(__name__)

# db.init_app(app)

# migrate = Migrate(app)

port = os.environ.get('PORT')
if port is None:
    port = 8080

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


def validate_body(body):
    try:
        body = json.loads(body)
    except:
        return None, ['Can\'t deserialize body!']

    errors = []
    if 'carUid' not in body or type(body['carUid']) is not str or \
            'dateFrom' not in body or type(body['dateFrom']) is not str or \
            'dateTo' not in body or type(body['dateTo']) is not str:
        return None, ['Bad structure body!']

    return body, errors


@app.route('/favicon.ico') 
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')

#жив или не жив наш герой?
@app.route('/manage/health', methods=['GET'])
def health():
    return make_response(jsonify({}), 200)


@app.route("/api/v1/rental/<string:rentalUid>", methods = ["DELETE"])
def delete_rental(rental_uid):
    pass


@app.route('/api/v1/cars/', methods=['GET'])
def get_cars():
    page = request.args.get('page', default=0, type=int)
    size = request.args.get('size', default=0, type=int)
    response = requests.get("http://cars:8070/api/v1/cars", params={'page':page, "size":size})
    return make_response(response.json(), 200)


@app.route('/api/v1/rental/<string:rentalUid>', methods=['GET'])
def get_rental(rental_uid):
    if "X-User-Name" not in request.headers.keys():
        return make_data_response(400, message="Request has not X-User-Name header!")


    page = request.args.get('page', default=0, type=int)
    size = request.args.get('size', default=0, type=int)
    response = requests.get(f"http://rental:8060/api/v1/rental/{rental_uid}", params={'page':page, "size":size})
    return make_response(response.json(), 200)

@app.route('/api/v1/rental/', methods=['GET', "POST"])
def get_rentals():

    if "X-User-Name" not in request.headers.keys():
        return make_data_response(400, message="Request has not X-User-Name header!")
    
    if request.method == "GET":

        username = request.headers['X-User-Name']
        response = requests.get("http://rental:8060/api/v1/rental", headers={ "X-User-Name": username })
        return make_response(response.json(), 200)

    if request.method == "POST":
        body, errors = validate_body(request.get_json) #get_data
        if len(errors) > 0:
            return Response(
                status=200,
                content_type='application/json',
                response=json.dumps(errors)
            )
        username = request.headers['X-User-Name']
        caruid = body['carUid']
        response = requests.post(f"http://cars:8070/api/v1/cars/{caruid}/order")

        
        if response is None:
            return Response(
                status=500,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Car service is unavailable.']
                })
            )
        if response.status_code == 404 or response.status_code == 403:
            return Response(
                status=response.status_code,
                content_type='application/json',
                response=response.text
            )

        car = response.json()
        price = (datetime.datetime.strptime(body['dateTo'], "%Y-%m-%d").date() - \
            datetime.datetime.strptime(body['dateFrom'], "%Y-%m-%d").date()).days * car['price']

        response = requests.post(f"http://payments:8050/api/v1/payment/",  data={'price': price})


        payment = response.json()
        body['paymentUid'] = payment['paymentUid']
        response = requests.post(f"http://rentals:8060/api/v1/rental", data=body, headers={'X-User-Name': request.headers['X-User-Name']})

        if response.status_code != 200:
            return Response(
                status=response.status_code,
                content_type='application/json',
                response=response.text
            )

        rental = response.json()

        rental['payment'] = payment
        del rental['paymentUid']

        return Response(
            status=200,
            content_type='application/json',
            response=json.dumps(rental)
        )

@app.route('/api/v1/rental/<string:rentalUid>/finish', methods=["POST"])
def post_finish(rentaluid):
    response = requests.post(f"http://rental:8060/api/v1/rental/{rentaluid}/finish")

    if response is None:
        return Response(
            status=500,
            content_type='application/json',
            response=json.dumps({
                'errors': ['Rental service is unavailable.']
            })
        )
    elif response.status_code != 200:
        return Response(
            status=response.status_code,
            content_type='application/json',
            response=response.text
        )


    return Response(
        status=204
    )


if __name__=="__main__":
    app.run(host="0.0.0.0", port=port, debug=True)