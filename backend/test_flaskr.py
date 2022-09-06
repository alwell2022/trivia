import math
import numbers
import os
import random
import unittest
import json
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from flaskr import create_app
from models import setup_db, Question, Category
import credential as secret


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgresql://{0}:{1}@localhost:5432/{2}".format(
            secret.username, secret.password, self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['categories']))
        self.assertTrue(data['total_categories'])

    def test_404_categories(self):
        res = self.client().get('/categories/23')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)

    def test_get_questions(self):
        res = self.client().get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['questions']))
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['current_category']))
        self.assertTrue(len(data['categories']))

    def test_405_bad_request_for_questions(self):
        res = self.client().get('/questions/13')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['success'], False)

    def test_create_question(self):
        res = self.client().post(
            '/questions', json={'new_question':  {
                "question": 'What is a noun?',
                "answer": 'Name of any person, animal, place or thing.',
                "category": 'Education',
                "difficulty": 1
            }})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

    def test_405_create_not_allowed(self):
        res = self.client().post('/questions/24', json={
            "question": 'What is a noun?',
            "answer": 'Name of any person, animal, place or thing.',
            "category": 'Education',
            "difficulty": 1
        })
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'method not allowed')

    def test_search_with_result(self):
        res = self.client().post(
            '/questions', json={'searchTerm': 'Noun'})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['questions']))
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['current_category']))

    def test_search_without_result(self):
        res = self.client().post(
            '/questions', json={'searchTerm': 'Internal combustion'})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['questions']), 0)
        self.assertEqual(data['total_questions'], 0)

    def test_retrieve_questions_by_category(self):
        item_id = 7
        res = self.client().get(f'/categories/{item_id}/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['questions']))
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['current_category']))

    def test_404_get_category_questions(self):
        res = self.client().get(f'/categories/897/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_delete_question_endpoint(self):
        number = random.randint(1, 200)
        res = self.client().delete(f'/questions/{number}')
        data = json.loads(res.data)

        question = Question.query.filter(
            Question.id == 16).one_or_none()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["deleted"], number)
        self.assertTrue(data["total_questions"])
        self.assertTrue(len(data["questions"]))
        self.assertEqual(question, None)

    def test_422_question_not_exit_for_delete(self):
        res = self.client().delete(f'/questions/2300')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "unprocessable")

    def test_400_quizzes(self):
        res = self.client().post('/quizzes')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'bad request')

    def test_quizzes(self):
        res = self.client().post('/quizzes', json={
            "quiz_category": {
                "type": "History",
                "id": "7"
            },
            "previous_questions": []
        })
        print(res)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['previous_questions']))
        self.assertTrue(len(data['quiz_category']))

    def test_405_quizzes(self):
        res = self.client().get('/quizzes')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'method not allowed')


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
