import os 
import sys
from marshmallow import ValidationError
from flask import Flask, request, flash, redirect
from flask_migrate import Migrate
from flask_restful import abort, url_for
from flask_sqlalchemy import SQLAlchemy
from carsDB import CarDB
from flask import send_from_directory, jsonify, make_response, Response, request
from sqlalchemy import exc
from model import CarModel, db
import json


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://program:test@postgres:5432/cars"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

migrate = Migrate(app)

port = os.environ.get('PORT')
if port is None:
    port = 8070

@app.errorhandler(404)



def make_data_response(status_code, **kwargs):
    response = jsonify({**kwargs})
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


def args_valid(args):
    errors = []
    if 'page' in args.keys():
        try:
            page = int(args['page'])
            if page <=0:
                errors.append("Page must be positive")
        except ValueError:
            errors.append("Page is not a number")
            page=None

    else:
        errors.append("page must be define")
        page=None



    if "size" in args.keys():
        try:
            size = int(args['size'])
            if size <= 0:
                errors.append('Size must be positive.')
        except ValueError:
            size = None
            errors.append('Size is not a number')
    else:
        errors.append('Size must be define')
        size = None

    
    if "showAll" in args.keys():
        if args['showAll'].lower() == 'true':
            show_all = True
        elif args['showAll'].lower() == 'false':
            show_all = False
        else:
            errors.append('showAll must be true or false')
            show_all = None
    else:
        show_all = False

    return page, size, show_all, errors



#жив или не жив наш герой?
@app.route('/manage/health', methods=['GET'])
def health():
    return make_response(jsonify({}), 200)

@app.route("/api/v1/cars/<string:carUid>", methods = ["GET"])
def get_car(carUid):
    if request.method == "GET":
        result=db.session.query(CarModel).filter(CarModel.car_uid==carUid).one_or_none()
        if not result:
            abort(404)
        return make_response(jsonify(result.to_dict()), 200)

@app.route("/api/v1/cars/<string:carUid>/order", methods = ["POST"])
def post_car(carUid):
    try:
        car = db.session.query(CarModel).filter(CarModel.car_uid==carUid).one_or_none()
        if not car:
            return Response(status=404,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Uid not found in DB.']
            }))
        car.availability = False
        db.session.commit()

        return Response(
            status=200,
            content_type='application/json',
            response=json.dumps(car.to_dict())
        )
    except Exception as e:
        db.session.rollback()
        return make_data_response(500, message="Database create order error")

@app.route("/api/v1/cars/<string:carUid>/order", methods = ["DELETE"])
def delete_car_order(carUid):
    try:
        car = db.session.query(CarModel).filter(CarModel.car_uid==carUid).one_or_none()
        if car.availability is True:
            return Response(
                status=403,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Car isn\'t ordered.']
                })
            )
        car.availability = True
        
        db.session.commit()
        return Response(
            status=204
        )

    except Exception as e:
        print(e)
        app.logger.error(e)
        
        db.session.rollback()
        return make_data_response(500, message="Database delete error")


@app.route("/api/v1/cars/", methods = ["GET"])
def get_all_cars():
    """Получить список всех доступных для бронирования автомобилей"""
    page, size, show_all, errors = args_valid(request.args)
    if len(errors) > 0:
        return Response(
            status=400,
            content_type="application/json",
            response=json.dumps({
                "errors":errors
            })
        )

    

    if not show_all:
        query = db.session.query(CarModel).filter(CarModel.availability==True)
        count_total = query.count()
        cars = [car.to_dict() for car in query.paginate(page=page, per_page=size)]


    else:
        count_total = CarModel.select().count()
        cars =  [car.to_dict() for car in CarModel.paginate(page=page, per_page=size)]
        
    return Response(
        status=200, 
        content_type="application/json", 
        response=json.dumps({
            "page": page,
            "pageSize": size,
            "totalElements": count_total,
            "items":cars
        })
    )



if __name__ == '__main__':
    carsDb = CarDB()
    carsDb.check_cars_db()
    app.run(host='0.0.0.0', port=8070)