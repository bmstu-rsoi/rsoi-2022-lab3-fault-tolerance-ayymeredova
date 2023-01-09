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
import threading
import time

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



@app.route('/api/v1/cars/', methods=['GET'])
def get_cars():
    """Забронировать автомобиль"""
    # try:
    #     check_car_service = requests.get("http://cars:8070/manage/health")
    # except requests.exceptions.ConnectionError:
    #         return Response(
    #             status=503,
    #             content_type='application/json',
    #             response=json.dumps({
    #                 'errors': ['Car service is unavailable.']
    #             })
    #         )
    page = request.args.get('page', default=0, type=int)
    size = request.args.get('size', default=0, type=int)
    try:
        response = requests.get("http://cars:8070/api/v1/cars", params={'page':page, "size":size})
    except requests.exceptions.ConnectionError:
            return Response(
                status=503,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Car service is unavailable.']
                })
            )
    return make_response(response.json(), 200)


@app.route('/api/v1/rental/<string:rentalUid>', methods=['GET', 'DELETE'])
def get_rental(rentalUid):
    if request.method == 'GET':
        if "X-User-Name" not in request.headers.keys():
            # return make_data_response(400, message="Request has not X-User-Name header! in get in gateway")
            return Response(
                status=400,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Request has not X-User-Name header!']
                })
            )
        # try:
        #     check_rental_service = requests.get("http://rental:8060/manage/health")
        # except requests.exceptions.ConnectionError:
        #      return Response(
        #         status=503,
        #         content_type='application/json',
        #         response=json.dumps({
        #             'errors': ['Rental service is unavailable.']
        #         })
        #     )
        try:
            response = requests.get(f"http://rental:8060/api/v1/rental/{rentalUid}")
        except requests.exceptions.ConnectionError:
             return Response(
                status=503,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Rental service is unavailable.']
                })
            )
        body = response.json()

        # try:
        #    check_car_service = requests.get("http://cars:8070/manage/health")
        # except requests.exceptions.ConnectionError:
        #     return Response(
        #         status=503,
        #         content_type='application/json',
        #         response=json.dumps({
        #             'errors': ['Cars service is unavailable.']
        #         })
        #     )
        try:
            response = requests.get(f"http://cars:8070/api/v1/cars/{body['carUid']}")
        except requests.exceptions.ConnectionError:
             return Response(
                status=503,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['car service is unavailable.']
                })
            )
        body['car'] = response.json()
        # try:
        #     check_payment_service = requests.get("http://payment:8050//manage/health")
        # except requests.exceptions.ConnectionError:
        #     return Response(
        #         status=503,
        #         content_type='application/json',
        #         response=json.dumps({
        #             'errors': ['Payment service is unavailable.']
        #         })
        #     )
        try:
            response = requests.get(f"http://payment:8050/api/v1/payment/{body['paymentUid']}")
        except requests.exceptions.ConnectionError:
            body['payment'] = ""
        else:
            body['payment'] = response.json()

        return make_response(body, response.status_code)

    if request.method == "DELETE":
        try:
            response = requests.delete(f"http://rental:8060/api/v1/rental/{rentalUid}")
        except:
            response = None
        
        if response is None:
            return Response(
                status=503,
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
        try:
            response = requests.delete(f"http://cars:8070/api/v1/cars/{body['carUid']}/order")
        except:
            response = None

        if response is None:
            return Response(
                status=503,
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
        
        def delete_payment(paymentUid):
            while True:
                try:
                    response = requests.delete(f"http://payment:8050/api/v1/payment/{paymentUid}")
                except requests.exceptions.ConnectionError:
                    time.sleep(5)
        t = threading.Thread(target=delete_payment, args=(body['paymentUid'], ))
        t.start()

        # try:
        #     response = requests.delete(f"http://payment:8050/api/v1/payment/{body['paymentUid']}")
        # except:
        #     response = None

        # if response is None:
        #     return Response(
        #         status=503,
        #         content_type='application/json',
        #          response=json.dumps({
        #             'message': "Payment Service unavailable"
        #         })
        #     )
        # elif response.status_code >= 400:
        #     return Response(
        #         status=response.status_code,
        #         content_type='application/json',
        #         response=response.text
        #     )

        return Response(
            status=204
        )

@app.route('/api/v1/rental/', methods=['GET', "POST"])
def get_rentals():
    if request.method == "GET":
        
        if "X-User-Name" not in request.headers:
            return make_data_response(400, message="Request has not X-User-Name header! in get rentals get in gateway")
        username = request.headers.get('X-User-Name')

        # try:
        #     check_rental_service = requests.get("http://rental:8060/manage/health")
        # except requests.exceptions.ConnectionError:
        #     return Response(
        #         status=503,
        #         content_type='application/json',
        #         response=json.dumps({
        #             'errors': ['Rental service is unavailable.']
        #         })
        #     )
        # try:
        #     check_car_service = requests.get("http://cars:8070/manage/health")
        # except requests.exceptions.ConnectionError:
        #     return Response(
        #         status=503,
        #         content_type='application/json',
        #         response=json.dumps({
        #             'errors': ['Car service is unavailable.']
        #         })
        #     )
        # try:
        #     check_payment_service = requests.get("http://payment:8050/manage/health")
        # except requests.exceptions.ConnectionError:
        #     return Response(
        #         status=503,
        #         content_type='application/json',
        #         response=json.dumps({
        #             'errors': ['payment service is unavailable.']
        #         })
        #     )

        try:
            response = requests.get("http://rental:8060/api/v1/rental", headers={ "X-User-Name": username })
        except requests.exceptions.ConnectionError:
            return Response(
                status=503,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Rental service is unavailable.']
                })
            )
        if response.status_code >=400:
            return Response(
                status=response.status_code,
                content_type='application/json',
                response=response.text
            )
        body = response.json()

        for i in range(len(body)):
            try:
                response = requests.get(f"http://cars:8070/api/v1/cars/{body[i]['carUid']}")
            except requests.exceptions.ConnectionError:
                return Response(
                status=503,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Car service is unavailable.']
                })
            )
            body[i]['car'] = response.json()
            try:
                response = requests.get(f"http://payment:8050/api/v1/payment/{body[i]['paymentUid']}")
            except requests.exceptions.ConnectionError:
                return Response(
                    status=503,
                    content_type='application/json',
                    response=json.dumps({
                        'message': "Payment Service unavailable"
                    })
            )
            body[i]['payment'] = response.json()
            try:
                response = requests.get(f"http://rental:8060/api/v1/rental/{body[i]['rentalUid']}")
            except requests.exceptions.ConnectionError:
                return Response(
                status=503,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Rental service is unavailable.']
                })
            )
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
        # try:
        #     check_car_service = requests.get("http://cars:8070/manage/health")
        # except requests.exceptions.ConnectionError:
        #     return Response(
        #         status=503,
        #         content_type='application/json',
        #         response=json.dumps({
        #             'errors': ['Car service is unavailable.']
        #         })
        #     )
        try:
            response = requests.post(f"http://cars:8070/api/v1/cars/{caruid}/order")
        except:
            response = None
        if response is None:
            return Response(
                status=503,
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
        # try:
        #     check_payment_service = requests.get("http://payment:8050/manage/health")
        # except requests.exceptions.ConnectionError:
        #     return Response(
        #         status=503,
        #         content_type='application/json',
        #         response=json.dumps({
        #             'errors': ['Payment service is unavailable.']
        #         })
        #     )
        try:
            response = requests.post(f"http://payment:8050/api/v1/payment/",  json={'price': price})
        except:
            response = None
        if response is None:
            return Response(
                status=503,
                content_type='application/json',
                 response=json.dumps({
                    'message': "Payment Service unavailable"
                })
            )
        if response.status_code >= 400:
            return Response(
                status=response.status_code,
                content_type='application/json',
                response=response.text
            )
        
        # body['paymentUid'] = response.headers["Location"].split('/')[-1]

        payment = response.json()
        body['paymentUid'] = payment['paymentUid']
        # try:
        #     check_rental_service = requests.get("http://rental:8060/manage/health")
        # except requests.exceptions.ConnectionError:
        #     return Response(
        #         status=503,
        #         content_type='application/json',
        #         response=json.dumps({
        #             'errors': ['Rental service is unavailable.']
        #         })
        #     )
        try:
            response = requests.post(f"http://rental:8060/api/v1/rental/", json=body, headers={'X-User-Name': request.headers['X-User-Name']})
        except:
            response = None
        if response is None:
            return Response(
                status=503,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Rental service is unavailable.']
                })
            )
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
            status=response.status_code,
            content_type='application/json',
            response=json.dumps(rental)
        )

@app.route('/api/v1/rental/<string:rentalUid>/finish', methods=["POST"])
def post_finish(rentalUid):
    # try:
    #     check_rental_service = requests.get("http://rental:8060/manage/health")
       
    # except requests.exceptions.ConnectionError:
    #         return Response(
    #             status=503,
    #             content_type='application/json',
    #             response=json.dumps({
    #                 'errors': ['rental service is unavailable.']
    #             })
    #         )
    try:
        response = requests.post(f"http://rental:8060/api/v1/rental/{rentalUid}/finish")
    except:
        response = None
    if response is None:
        return Response(
            status=503,
            content_type='application/json',
            response=json.dumps({
                'errors': ['Rental service is unavailable.']
            })
        )
    if response.status_code >= 400:
        return Response(
            status=response.status_code,
            content_type='application/json',
            response=response.text
        )

    
    rental = response.json()
    # try:
    #     check_car_service = requests.get("http://cars:8070/manage/health")
    # except requests.exceptions.ConnectionError:
    #         return Response(
    #             status=503,
    #             content_type='application/json',
    #             response=json.dumps({
    #                 'errors': ['Car service is unavailable.']
    #             })
    #         )
    try:
        response = requests.delete(f'http://cars:8070/api/v1/cars/{rental["carUid"]}/order')
    except:
        response = None

    if response is None:
        return Response(
            status=503,
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