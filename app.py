from flask import Flask


app = Flask(__name__)

import config
import models
import api
from controllers import controllers_login
from controllers import controllers_admin
from controllers import controllers_users



if __name__ == "__main__":
    app.run(debug=True)