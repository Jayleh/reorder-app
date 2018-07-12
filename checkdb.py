from reorder import db
from reorder.models import User

user = User.query.all()
print(user)
