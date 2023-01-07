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
import logging

app = Flask(__name__)
app.logger.debug("This is DEBUG log level")

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
    print("validate_body: ", body)
    # try:
    #     body = json.loads(body)
    # except:
    #     return None, ['Can\'t deserialize body!']

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


# @app.route("/api/v1/rental/<string:rentalUid>", methods = ["DELETE"])
# def delete_rental(rentalUid):
#     response = requests.delete(f"http://rental:8060/api/v1/rental/{rentalUid}")
#     if response is None:
#         return Response(
#             status=500,
#             content_type='application/json',
#             response=json.dumps({
#                 'errors': ['Rental service is unavailable.']
#             })
#         )
#     elif response.status_code != 200:
#         return Response(
#             status=response.status_code,
#             content_type='application/json',
#             response=response.text
#         )
#     return Response(
#         status=204
#     )


@app.route('/api/v1/cars/', methods=['GET'])
def get_cars():
    """Забронировать автомобиль"""
    page = request.args.get('page', default=0, type=int)
    size = request.args.get('size', default=0, type=int)
    response = requests.get("http://cars:8070/api/v1/cars", params={'page':page, "size":size})
    return make_response(response.json(), 200)


@app.route('/api/v1/rental/<string:rentalUid>', methods=['GET', 'DELETE'])
def get_rental(rentalUid):
    if request.method == 'GET':
        if "X-User-Name" not in request.headers.keys():
            return make_data_response(400, message="Request has not X-User-Name header! in get in gateway")

        response = requests.get(f"http://rental:8060/api/v1/rental/{rentalUid}")
        body = response.json()
        # print(body)
        # app.logger.info(body)
        
        response = requests.get(f"http://cars:8070/api/v1/cars/{body['carUid']}")
        body['car'] = response.json()

        response = requests.get(f"http://payment:8050/api/v1/payment/{body['paymentUid']}")
        body['payment'] = response.json()

        return make_response(body, response.status_code)

    if request.method == "DELETE":
        response = requests.delete(f"http://rental:8060/api/v1/rental/{rentalUid}")
        if response is None:
            return Response(
                status=500,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Rental service is unavailable.']
                })
            )
        elif response.status_code >= 400:
            return Response(
                status=response.status_code,
                content_type='application/json',
                response=response.text
            )
        body = response.json()
        response = requests.delete(f"http://cars:8070/api/v1/cars/{body['carUid']}/order")
        if response is None:
            return Response(
                status=500,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Rental service is unavailable.']
                })
            )
        elif response.status_code >= 400:
            return Response(
                status=response.status_code,
                content_type='application/json',
                response=response.text
            )

        response = requests.delete(f"http://payment:8050/api/v1/payment/{body['paymentUid']}")
        if response is None:
            return Response(
                status=500,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Rental service is unavailable.']
                })
            )
        elif response.status_code >= 400:
            return Response(
                status=response.status_code,
                content_type='application/json',
                response=response.text
            )

        return Response(
            status=204
        )

@app.route('/api/v1/rental/', methods=['GET', "POST"])
def get_rentals():

    
    if request.method == "GET":
        
        if "X-User-Name" not in request.headers:
            return make_data_response(400, message="Request has not X-User-Name header! in get rentals get in gateway")
        username = request.headers.get('X-User-Name')
        response = requests.get("http://rental:8060/api/v1/rental", headers={ "X-User-Name": username })
        
        body = response.json()

        for i in range(len(body)):
            response = requests.get(f"http://cars:8070/api/v1/cars/{body[i]['carUid']}")
            body[i]['car'] = response.json()

            response = requests.get(f"http://payment:8050/api/v1/payment/{body[i]['paymentUid']}")
            body[i]['payment'] = response.json()

            response = requests.get(f"http://rental:8060/api/v1/rental/{body[i]['rentalUid']}")
            body[i]["rental"] = response.json()

        return make_response(body, response.status_code)
        # return make_response(response.json(), 200)

    if request.method == "POST":
        
        if "X-User-Name" not in request.headers:
            return make_data_response(400, message="Request has not X-User-Name header! in get rentals post in gateway")
        
        body, errors = validate_body(request.get_json()) #get_data
        print("validate_errors: ", errors)
        if len(errors) > 0:
            return Response(
                status=400,
                content_type='application/json',
                response=json.dumps(errors)
            )
        username = request.headers.get('X-User-Name')
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
        if response.status_code >= 400:
            return Response(
                status=response.status_code,
                content_type='application/json',
                response=response.text
            )

        car = response.json()
        price = (datetime.datetime.strptime(body['dateTo'], "%Y-%m-%d").date() - \
            datetime.datetime.strptime(body['dateFrom'], "%Y-%m-%d").date()).days * car['price']

        response = requests.post(f"http://payment:8050/api/v1/payment/",  json={'price': price})

        if response.status_code >= 400:
            return Response(
                status=response.status_code,
                content_type='application/json',
                response=response.text
            )
        
        # body['paymentUid'] = response.headers["Location"].split('/')[-1]

        payment = response.json()
        body['paymentUid'] = payment['paymentUid']

        response = requests.post(f"http://rental:8060/api/v1/rental/", json=body, headers={'X-User-Name': request.headers['X-User-Name']})
        if response.status_code >= 400:
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
def post_finish(rentalUid):
    response = requests.post(f"http://rental:8060/api/v1/rental/{rentalUid}/finish")

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

    
    rental = response.json()

    response = requests.delete(f'http://cars:8070/api/v1/cars/{rental["carUid"]}/order')

    if response is None:
        return Response(
            status=500,
            content_type='application/json',
            response=json.dumps({
                'errors': ['Cars service is unavailable.']
            })
        )


    return Response(
        status=204
    )


if __name__=="__main__":
    app.run(host="0.0.0.0", port=port, debug=True)