from flask import Flask, request
from flask_restful import Api, Resource
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
api = Api(app)

class user_msg_Api(Resource):
    def post(self):
        data = request.get_json()
        user_msg = data.get("message", "")
        print("msg received:", user_msg)
        return {"Api": "posted"}
    

api.add_resource(user_msg_Api, "/user_msg_Api")

if __name__ == "__main__":
    app.run(debug=True)
