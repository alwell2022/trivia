import collections
import json
import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r'/api/*': {'origins': '*'}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def afterRequest(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    @app.route('/categories')
    def retrieve_categories():
        """
        @TODO:
        Create an endpoint to handle GET requests
        for all available categories.
        """
        try:
            collection = Category.query.order_by(Category.id).all()
            if len(collection) == 0:
                abort(404)
            categories = [category.format()['type'] for category in collection]
            # print(categories)
            return jsonify({
                'success': True,
                'categories': categories,
                'total_categories': len(categories)
            })
        except:
            abort(400)

    def paginate_question(request, item):
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        collection = [i.format() for i in item]

        return collection[start:end]

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        """
        @TODO:
        Create an endpoint to DELETE question using a question ID.

        TEST: When you click the trash icon next to a question, the question will be removed.
        This removal will persist in the database and when you refresh the page.
        """
        try:
            question = Question.query.filter(
                Question.id == question_id).first()
            if question is None:
                abort(404)
            # delete the selected question
            question.delete()
            # check if the question has been deleted
            questions = Question.query.order_by(Question.id).all()
            current_questions = paginate_question(request, questions)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(questions)
            })
        except:
            # else unprocessable
            abort(422)

    @app.route('/questions', methods=['GET', 'POST'])
    def retrieve_or_search_questions():
        """
        @TODO:
        Create an endpoint to POST a new question,
        which will require the question and answer text,
        category, and difficulty score.

        TEST: When you submit a question on the "Add" tab,
        the form will clear and the question will appear at the end of the last page
        of the questions list in the "List" tab.
        """
        """
        @TODO:
        Create a POST endpoint to get questions based on a search term.
        It should return any questions for whom the search term
        is a substring of the question.

        TEST: Search by any phrase. The questions list will update to include
        only question that include that string within their question.
        Try using the word "title" to start.
        """
        try:

            if request.method == 'POST':
                body = request.get_json()
                # Gets the json's body members
                searchTerm = body.get('searchTerm', None)
                newQuestion = body.get('question', None)
                newAnswer = body.get('answer', None)
                newDifficulty = body.get('difficulty', None)
                newCategory = body.get('category', None)

                if searchTerm:
                    questions = Question.query.filter(Question.question.ilike(
                        f'%{searchTerm}%')).order_by(Question.id).all()

                    if questions is None:
                        return jsonify({
                            'success': True
                        })

                    current_questions = paginate_question(request, questions)
                    current_category = Category.query.filter(
                        Category.id == current_questions[0]['category'])\
                        .one_or_none().format()['type'] if questions else ''

                    return jsonify({
                        'success': True,
                        'questions': current_questions,
                        'total_questions': len(questions),
                        'current_category': current_category
                    })
                else:
                    new_question = Question(
                        newQuestion, newAnswer, newCategory,
                        newDifficulty)

                    new_question.insert()
                    return jsonify({
                        'success': True
                    })
            else:
                selection = db.session.query(
                    Question, Category).join(
                    Category, Category.id == Question.category).order_by(
                    Category.id).all()
                if len(selection) == 0:
                    abort(404)
                questions = {'questions': [], 'categories': []}
                # iterate query result
                for question in selection:
                    questions['questions'].append(question[0])
                    questions['categories'].append(
                        question[1].format()['type'])
                categories = [category.format()['type'] for category in Category
                              .query.order_by(Category.id).all()]
                data = {
                    'success': True,
                    'questions': paginate_question(request, questions['questions']),
                    'total_questions': len(selection),
                    'current_category': questions['categories'][0],
                    'categories': categories
                }
                return jsonify(data)
        except:
            abort(400)

    @app.route('/categories/<int:category_id>/questions')
    def getCategoryQuestions(category_id):
        """
        @TODO:
        Create a GET endpoint to get questions based on category.

        TEST: In the "List" tab / main screen, clicking on one of the
        categories in the left column will cause only questions of that
        category to be shown.
        """
        try:
            # get questions for a specific category
            questions = db.session.query(Question).join(
                Category, Category.id == Question.category).filter(
                Category.id == category_id).order_by(Question.id).all()

            return jsonify({
                'success': True,
                'questions': paginate_question(request, questions),
                'total_questions': len(Question.query.all()),
                'current_category': Category.query.filter(
                    Category.id == category_id).first().format()['type']
            })
        except:
            # abort with error code 404
            abort(404)

    @app.route('/quizzes', methods=['POST'])
    def play():
        """
        @TODO:
        Create a POST endpoint to get questions to play the quiz.
        This endpoint should take category and previous question parameters
        and return a random questions within the given category,
        if provided, and that is not one of the previous questions.

        TEST: In the "Play" tab, after a user selects "All" or a category,
        one question at a time is displayed, the user is allowed to answer
        and shown whether they were correct or not.
        """
        try:
            # get value from the user
            quiz_category = request.get_json().get(
                'quiz_category', None)['type']
            previous_questions = request.get_json().get('previous_questions')
            if len(previous_questions) == 5:
                return jsonify({
                    'success': True,
                    'question': False
                })
            questions = []
            if quiz_category == 'click' or quiz_category is None:
                questions = Question.query.order_by(Question.id).all()
            else:
                collection = Category.query.order_by(Category.id).all()
                categories = [category.format() for category in collection]
                for category in categories:
                    if (category['type'] == quiz_category):
                        category_id = category['id']
                questions = Question.query.filter(
                    Question.category == category_id)\
                    .order_by(Question.id).all()

                if len(questions) == False:
                    data = {
                        'success': True,
                        'question': False
                    }
            questions = [question.format() for question in questions]

            randomIndex = random.randint(0, len(questions))

            if len(questions) <= randomIndex:
                return jsonify({
                    'success':True,
                    'question':False
                })

            if len(previous_questions) != 0:
                if len(previous_questions) == 5:
                    return False
                question = questions[randomIndex]
                while question['id'] in previous_questions:
                    randomIndex = random.randint(0, len(questions))
            if randomIndex != -1:
                q = questions[randomIndex]
                quiz_id = q['id']
                previous_questions.append(quiz_id)
                question = questions[randomIndex]
            else:
                question = False
            data = {
                'success': True,
                'quiz_category': quiz_category,
                'previous_questions': previous_questions,
                'question': question
            }
            try:
                return jsonify(data)
            except TypeError:
                abort(500)
        except:
            abort(400)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'resource not found'
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'method not allowed'
        }), 405

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'bad request'
        }), 400

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'unprocessable'
        }), 422

    return app
