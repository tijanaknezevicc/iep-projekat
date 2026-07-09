import re

from flask import Flask
from flask import request
from flask import jsonify 

from flask_jwt_extended import JWTManager, verify_jwt_in_request
from flask_jwt_extended import create_access_token
from flask_jwt_extended import create_refresh_token 
from flask_jwt_extended import jwt_required 
from flask_jwt_extended import get_jwt_identity 
from flask_jwt_extended import get_jwt 

from configuration import Configuration

from models import database
from models import User

application = Flask ( __name__ )
application.config.from_object ( Configuration )

database.init_app ( application )

with application.app_context ( ):
    database.drop_all()
    database.create_all ( )

    director = User.query.filter ( User.email == "onlymoney@gmail.com" ).first ( )

    if ( director is None ):
        director = User (
            email    = "onlymoney@gmail.com",
            password = "evenmoremoney",
            forename = "Scrooge",
            surname  = "McDuck",
            role     = "director"
        )
        database.session.add ( director )

    database.session.commit ( )

@application.route ( "/register", methods=["POST"] )
def register ( ):
       
    if ( not "forename" in request.json or len ( request.json["forename"] ) == 0 or len ( request.json["forename"] ) > 256 ):
        return jsonify({"message": "Field forename is missing."}), 400
    if ( not "surname" in request.json or len ( request.json["surname"] ) == 0 or len ( request.json["surname"] ) > 256 ):
        return jsonify({"message": "Field surname is missing."}), 400
    if ( not "email" in request.json or len ( request.json["email"] ) == 0 or len ( request.json["email"] ) > 256 ):
        return jsonify({"message": "Field email is missing."}), 400
    if ( not "password" in request.json or len ( request.json["password"] ) == 0 or len ( request.json["password"] ) > 256 ):
        return jsonify({"message": "Field password is missing."}), 400

    if ( not re.fullmatch(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', request.json["email"]) ):
        return jsonify({"message": "Invalid email."}), 400

    if ( len ( request.json["password"] ) < 8 ):
        return jsonify({"message": "Invalid password."}), 400

    new_user = User (
        email    = request.json["email"],
        password = request.json["password"],
        forename = request.json["forename"],
        surname  = request.json["surname"],
        role     = "employee"
    )
    database.session.add ( new_user )

    try:
        database.session.commit ( )
    except Exception as e:
        database.session.rollback()
        return jsonify({"message": "Email already exists."}), 400

    return "", 200

jwt = JWTManager ( application )

@application.route ( "/login", methods = ["POST"] )
def login ( ):

    if ( not "email" in request.json or len ( request.json["email"] ) == 0 or len ( request.json["email"] ) > 256 ):
        return jsonify({"message": "Field email is missing."}), 400
    if ( not "password" in request.json or len ( request.json["password"] ) == 0 or len ( request.json["password"] ) > 256 ):
        return jsonify({"message": "Field password is missing."}), 400

    if ( not re.fullmatch(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', request.json["email"]) ):
        return jsonify({"message": "Invalid email."}), 400

    user = User.query.filter ( User.email == request.json["email"], User.password == request.json["password"] ).first ( )

    if ( not user ):
        return jsonify({"message": "Invalid credentials."}), 400

    claims = {
            "forename": user.forename,
            "surname": user.surname,
            "role": user.role
    }

    access_token  = create_access_token ( identity = user.email, additional_claims = claims )

    return jsonify ( {"accessToken": access_token} ), 200

@application.route ( "/delete", methods = ["POST"] )
@jwt_required ( )
def delete ( ):

    try:
        verify_jwt_in_request()
    except Exception:
        return jsonify({"msg": "Missing Authorization Header"}), 401

    identity = get_jwt_identity()
    
    user = database.session.query(User).filter_by(email=identity).first()
    if user:
        database.session.delete(user)
        database.session.commit()
        return "", 200
    else:
        return jsonify({"message": "Unknown user."}), 400

if ( __name__ == "__main__" ):
    application.run ( host = "0.0.0.0", debug = True )
