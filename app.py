from flask import Flask
from flask_restful import Api, Resource, reqparse
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv
import os, jwt

load_dotenv(find_dotenv())
password = os.environ.get('MONGODB_PWD')
client = MongoClient(f"mongodb+srv://hyperprogrammer800:flaskapi123@cluster0.0mrqopb.mongodb.net/?retryWrites=true&w=majority")

app = Flask(__name__)
app.config['SECRET_KEY'] = "830a57373a264573fa2435a83841d31d"
api = Api(app)



class Register(Resource):
    def post(self):
        user_args = reqparse.RequestParser()
        req_args = ['first_name', 'last_name', 'email', 'password']
        for arg in req_args:
            user_args.add_argument(f'{arg}', type=str, location = 'json')
        args = user_args.parse_args()
        production = client.production
        user = production.user
        if not user.find_one({"email" : args.email}):
            doc = {"first_name" : args.first_name, "last_name" : args.last_name, "email" : args.email, "password" : args.password}
            new_obj_id = user.insert_one(doc).inserted_id
            return str(new_obj_id)
        return "try new email"

class Login(Resource):
    def post(self):
        user_args = reqparse.RequestParser()
        req_args = ['email', 'password']
        for arg in req_args:
            user_args.add_argument(f'{arg}', type=str, location = 'json')
        args = user_args.parse_args()
        production = client.production
        user = production.user
        try:
            if user.find_one({"email" : args.email}).get('_id') == user.find_one({"email" : args.email, "password" : args.password}).get('_id'):
                encoded = jwt.encode({"email": args.email, "password" : args.password}, app.config['SECRET_KEY'], algorithm="HS256")
                token = production.token
                if not token.find_one({"Authorization" : str(encoded)[2:-1]}):
                    owner_id = user.find_one({"email" : args.email}).get('_id')
                    doc = {"Authorization" : str(encoded)[2:-1], "owner_id" : owner_id}
                    new_tok = token.insert_one(doc)
                    return str(encoded)[2:-1]
                else:
                    return str(token.find_one({"Authorization" : str(encoded)[2:-1]}))
        except:
            return "invalid creds"


class Template(Resource):
    def get(self,template_id=None):
        production = client.production
        token = production.token
        template = production.template
        user_args = reqparse.RequestParser()
        user_args.add_argument('Authorization', type=str, location = 'headers')
        args = user_args.parse_args()
        try:
            owner_id = token.find_one({"Authorization" : args.Authorization.split(" ")[1]}).get('owner_id')
            query = {"owner_id" : owner_id}
            if template_id:
                query['template_id'] = template_id
            data = template.find(query)
            return str(list(data))
        except:
            return "not authorised"

    def post(self):
        user_args = reqparse.RequestParser()
        req_args = ['template_name', 'subject','body']
        for arg in req_args:
            user_args.add_argument(f'{arg}', type=str, location = 'json')
        user_args.add_argument('Authorization', type=str, location = 'headers')
        args = user_args.parse_args()
        production = client.production
        user = production.user
        token = production.token
        try:
            decoded = jwt.decode(args.Authorization.split(" ")[1], app.config['SECRET_KEY'], algorithms=["HS256"])
            owner_id = token.find_one({"Authorization" : args.Authorization.split(" ")[1]}).get('owner_id')
            user_id = user.find_one({"email" : decoded['email'], "password" : decoded['password']}).get('_id')
            try:
                if owner_id == user_id:
                    template = production.template
                    count = template.count_documents(filter={"owner_id" : owner_id})
                    template_id = 1
                    if count:
                        template_id = count
                        template_id +=1
                    doc = {"template_id" : template_id, "template_name" : args.template_name, "subject" : args.subject, "body" : args.body, "owner_id" : owner_id}
                    temp = template.insert_one(doc)
                    data = template.find({"owner_id" : owner_id})
                    return str(list(data))
                else:
                    return f'{str(owner_id)},{str(user_id)}'
            except:
                return "invalid creds"
        except:
            return "invalid auth"
    def put(self,template_id):
        user_args = reqparse.RequestParser()
        req_args = ['template_name', 'subject','body']
        for arg in req_args:
            user_args.add_argument(f'{arg}', type=str, location = 'json')
        user_args.add_argument('Authorization', type=str, location = 'headers')
        args = user_args.parse_args()
        production = client.production
        token = production.token
        try:
            owner_id = token.find_one({"Authorization" : args.Authorization.split(" ")[1]}).get('owner_id')
            template = production.template
            new_doc = {
                "template_id" : template_id,
                "template_name" : args.template_name,
                "subject" : args.subject,
                "body" : args.body,
                "owner_id" : owner_id
                }
            try:
                updated = template.replace_one({"owner_id" : owner_id,"template_id" : template_id},new_doc)
                return str(list(template.find({"owner_id" : owner_id})))
            except:
                return "update failed"
        except:
            return "invalid creds"

    def delete(self,template_id):
        user_args = reqparse.RequestParser()
        user_args.add_argument('Authorization', type=str, location = 'headers')
        args = user_args.parse_args()
        production = client.production
        token = production.token
        try:
            owner_id = token.find_one({"Authorization" : args.Authorization.split(" ")[1]}).get('owner_id')
            template = production.template
            template.delete_one({"owner_id" : owner_id,"template_id" : template_id})
            return str(list(template.find({"owner_id" : owner_id})))
        except:
            return "invalid auth"
        
class Home(Resource):
    def get(self):
        return "Home"
    
    
api.add_resource(Home, "/")
api.add_resource(Register, "/register/")
api.add_resource(Login, "/login/")
api.add_resource(Template, "/template/", "/template/<int:template_id>")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
