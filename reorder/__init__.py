import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '')
app.config['MONGO_DBNAME'] = os.environ['MONGO_DBNAME']
app.config['MONGO_URI'] = os.environ['MONGODB_URI']

api_id = os.environ['api_id']
api_key = (os.environ['api_key']).encode('utf-8')

# app.config['SECRET_KEY'] = "708494114a3a195011bdbb857946b7f9"
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '') or "sqlite:///site.sqlite"
# # app.config['MONGO_DBNAME'] = "heroku_wf3r0q2l"
# # app.config['MONGO_URI'] = "mongodb://heroku_wf3r0q2l:qlv8jt2rf8jf268rs33h3bul62@ds117691.mlab.com:17691/heroku_wf3r0q2l"
# app.config["MONGO_URI"] = "mongodb://localhost:27017/app"

# api_id = "25aa6352-595d-483b-9478-2e6d124d4533"
# api_key = ("hcecFO7GB8owmGelKKUUvs4jc4Gr4PoVm54EMFQSHdaNJE8lpC1ezk4LuOmshwtACb4QToI4mcKW3JLVh15w==").encode('utf-8')

db = SQLAlchemy(app)
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = None


from reorder import routes
