import json

import cv2
import npm as npm
import numpy
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os
from datetime import datetime
from sqlalchemy import ForeignKey
from maskdetection.face import face_match
from maskdetection.face import train
from maskdetection.yolov5.main import out
from sqlalchemy.orm import relationship
import maskdetection.yolov5

# import maskdetection.yolov5.face
import maskdetection
import maskdetection.yolov5
import maskdetection.face

# init app
from sqlalchemy.sql.functions import current_timestamp

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# init db
db = SQLAlchemy(app)
# init ma
ma = Marshmallow(app)


# user model
class User(db.Model):
    __tablename__ = 'user'
    mob = db.Column(db.String(15), primary_key=True)
    eid = db.Column(db.String(15), unique=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(30))
    rel = db.relationship("Log", backref="user")

    def __init__(self, mob, eid, name, email):
        self.mob = mob
        self.eid = eid
        self.name = name
        self.email = email


# Log Model
class Log(db.Model):
    __tablename__ = 'log'
    log_time = db.Column(db.DateTime, primary_key=True, default=datetime.utcnow)
    mob = db.Column(db.String(15), ForeignKey(User.mob))
    mask = db.Column(db.Boolean)
    temp = db.Column(db.Float)
    access = db.Column(db.Boolean)

    def __init__(self, log_time, mob, mask, temp, access):
        self.log_time = log_time
        self.mob = mob
        self.mask = mask
        self.temp = temp
        self.access = access


# user schema
class UserSchema(ma.Schema):
    class Meta:
        fields = ('mob', 'eid', 'name', 'email')


# init user schema
user_schema = UserSchema()
user_schema = UserSchema(many=True)


# Log schema
class LogSchema(ma.Schema):
    class Meta:
        fields = ('log_time', 'mob', 'mask', 'temp', 'access')


# init log schema
log_schema = LogSchema()
log_schema = LogSchema(many=True)


# validation
@app.route('/validate', methods=['POST'])
def valid():
    data = request.get_json()

    eid = data.get("eid")
    phone = data.get("phone")

    if eid:
        # query for id

        existing_user = User.query.filter_by(eid=eid).first()
        if existing_user is None:
            return jsonify(userExist=False)
        else:
            return jsonify(userExist=True)
    elif phone:

        # query for mob

        existing_user = User.query.filter_by(mob=phone).first()
        if existing_user is None:
            return jsonify(userExist=False)
        else:
            return jsonify(userExist=True)
    else:
        return f"Wrong Input"


# registration
@app.route('/register', methods=['POST'])
def insert():
    if request.method == 'POST':
        data = request.form.get('data')
        json_data=json.loads(data)
        mob=json_data['mob']
        eid = json_data['eid']
        name = json_data['name']
        email = json_data['email']
        image_request = request.files.to_dict(flat=False)
        image_file = image_request.get('images')
        print(image_file)
        filedest = os.path.join(basedir, 'Images/')
        try:
            new_dir = os.path.join(filedest, mob)
            os.mkdir(new_dir)
            image_file[0].save(os.path.join(new_dir, "Face.jpg"))
            image_file[1].save(os.path.join(new_dir, "Mask.jpg"))
            train(new_dir)
            new_user = User(mob, eid, name, email)
            db.session.add(new_user)
            db.session.commit()
            return jsonify(registrationsucess=True)
        except:
            print("folder for this ID already exists")
            return jsonify(registrationsucess=False)
# logging
@app.route('/logging', methods=['POST'])
def log():
    mob = request.json['mob']
    mask = request.json['mask']
    temp = request.json['temp']
    access = request.json['access']
    date = request.json["date"]
    log_time = datetime.strptime(date, '%d/%m/%Y %H:%M:%S')

    new_log = Log(log_time, mob, mask, temp, access)

    db.session.add(new_log)

    db.session.commit()

    return jsonify(transactionSuccess=True)


# face iding
@app.route('/face', methods=["POST"])
def getIdentity():
    imagefile = request.files.get('')
    filedest = os.path.join(basedir, 'temp/tempimg.jpg')
    imagefile.save(filedest)
    facei = face_match("temp/tempimg.jpg", "maskdetection/data.pt")
    # mask = request.json["mask"]
    print(facei[0])
    user = db.session.query.get(facei[0])
    return user_schema.jsonify(user)

# run server
if __name__ == '__main__':
    app.run(debug=True)
