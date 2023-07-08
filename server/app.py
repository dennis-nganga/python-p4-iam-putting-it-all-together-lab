#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class ClearSession(Resource):

    def delete(self):
        session['page_views'] = None
        session['user_id'] = None
        return {}, 204

class Signup(Resource):
    
    def post(self):
        json = request.get_json()
        user = User(
            username=json['username'],
            password_hash=json['password'],
            image_url=json['image_url'],
            bio=json['bio']
        )
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {'error': 'Username already exists.'}, 422
        session['user_id'] = user.id
        return user.to_dict(), 201

class CheckSession(Resource):
    
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            return user.to_dict(), 200
        return {}, 401

class Login(Resource):
    
    def post(self):
        json = request.get_json()
        username = json['username']
        password = json['password']
        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            session['user_id'] = user.id
            return user.to_dict(), 200
        return {'error': 'Invalid username or password.'}, 401

class Logout(Resource):
    
    def delete(self):
        user_id = session.get('user_id')
        if user_id:
            session['user_id'] = None
            return {}, 204
        return {'error': 'User is not logged in.'}, 401

class RecipeIndex(Resource):
    
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            recipes = Recipe.query.all()
            return [recipe.to_dict() for recipe in recipes], 200
        return {'error': 'User is not logged in.'}, 401

    def post(self):
        user_id = session.get('user_id')
        if user_id:
            json = request.get_json()
            recipe = Recipe(
                user_id=user_id,
                title=json['title'],
                instructions=json['instructions'],
                minutes_to_complete=json['minutes_to_complete']
            )
            errors = recipe.validate()
            if errors:
                return {'errors': errors}, 422
            db.session.add(recipe)
            db.session.commit()
            return recipe.to_dict(), 201
        return {'error': 'User is not logged in.'}, 401

api.add_resource(ClearSession, '/clear', endpoint='clear')
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)

