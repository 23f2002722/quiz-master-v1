from flask import Flask


app = Flask(__name__)

import config
import models
from controllers import controllers1
from controllers import controllers2



if __name__ == "__main__":
    app.run(debug=True)