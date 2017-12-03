from flask import Flask, render_template, jsonify, make_response, request
from flask_sqlalchemy import SQLAlchemy
from constants import *
from marshmallow import Schema, fields
import os

# Configure Flask app
app = Flask(__name__, static_url_path='/static')
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# Database
db = SQLAlchemy(app)

# Import + Register Blueprints
# Workflow is as follows:
# from app.blue import blue as blue
# app.register_blueprint(blue)


##### MODELS #####
class Base(db.Model):
  """
  Base database model
  """
  __abstract__ = True
  created_at = db.Column(db.DateTime, default = db.func.current_timestamp())
  updated_at = db.Column(db.DateTime, default = db.func.current_timestamp())

class Board(Base):
  __tablename__ = "boards"
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(80))

class Element(Base):
  __tablename__ = "elements"
  id = db.Column(db.Integer, primary_key=True)
  board_id = db.Column(db.Integer, db.ForeignKey("boards.id"))
  board = db.relationship("Board",
                      backref=db.backref("elements", lazy="dynamic"))
  description = db.Column(db.String(512))
  category = db.Column(db.String(50)) #STATUS_TODO, STATUS_IN_PROGRESS, STATUS_DONE

##### SCHEMAS #####
class ElementSchema(Schema):
  id = fields.Int(dump_only=True)
  board_id=fields.Int()
  description = fields.Str()
  category = fields.Str()
  created_at = fields.DateTime()
  updated_at = fields.DateTime()

# for post return board: POST /kanban/boards?title={board_title}
class BoardSchema(Schema):
  id = fields.Int(dump_only=True)
  title = fields.Str()
  created_at = fields.DateTime()
  updated_at = fields.DateTime()
  board_elements = fields.Nested(ElementSchema, many=True)

class BoardAllSchema(Schema):
  id = fields.Int(dump_only=True)
  title = fields.Str()
  created_at = fields.DateTime()
  updated_at = fields.DateTime()
  todo_count = fields.Int()
  inprogress_count = fields.Int()
  done_count = fields.Int()

# for get return board: GET /kanban/boards/{board_id}
class BoardGetSchema(Schema):
  id = fields.Int(dump_only=True)
  title = fields.Str()
  created_at = fields.DateTime()
  updated_at = fields.DateTime()
  todo = fields.Nested(ElementSchema, many=True)
  inprogress = fields.Nested(ElementSchema, many=True)
  done = fields.Nested(ElementSchema, many=True)


board_schema = BoardSchema()
board_get_schema = BoardGetSchema()
boards_schema = BoardAllSchema(many=True)
element_schema = ElementSchema()
elements_schema = ElementSchema(many=True)

# Default functionality of rendering index.html
def render_page():
  return render_template('index.html')

# React Catch All Paths
@app.route('/', methods=['GET'])
def index():
  return render_page()
@app.route('/<path:path>', methods=['GET'])
def any_root_path(path):
  return render_page()

# HTTP error handling
@app.errorhandler(404)
def not_found(error):
  return render_template('404.html'), 404

@app.route("/kanban/boards", methods=["GET", "POST", "DELETE"])
def new_board_get_all_boards_delete_board():
  # get all boards
  if request.method == "GET":
    boards = Board.query.all()
    for board in boards:
      board.todo_count = len(Element.query.filter_by(board_id=board.id, category='todo').all())
      board.inprogress_count = len(Element.query.filter_by(board_id=board.id, category='inprogress').all())
      board.done_count = len(Element.query.filter_by(board_id=board.id, category='done').all())
    result = boards_schema.dump(boards)
    return jsonify({'success': True,
                    'data': {'boards': result.data}})
  # new a board
  elif request.method == 'POST':
    title = request.args.get('title')
    board = Board(
      title=title
    )
    db.session.add(board)
    db.session.commit()
    board.board_elements = Element.query.filter_by(board_id=board.id).all()
    result = board_schema.dump(Board.query.get(board.id))
    return jsonify({'success': 'true',
                    'data': {'board': result.data}})

  # delete a board
  elif request.method == 'DELETE':
    id = request.args.get("id")
    Board.query.filter_by(id=int(id)).delete()
    db.session.commit()
    return jsonify({'success': True})
  else:
    pass

# get a single board by id
@app.route("/kanban/boards/<int:id>", methods=["GET"])
def get_board(id):
  board = Board.query.get(id)
  board.todo = Element.query.filter_by(board_id=board.id, category='todo').all()
  board.inprogress = Element.query.filter_by(board_id=board.id, category='inprogress').all()
  board.done = Element.query.filter_by(board_id=board.id, category='done').all()
  result = board_get_schema.dump(board)
  return jsonify({'success': True,
                  'data': {'board': result.data}})

@app.route("/kanban/board_elements", methods=["GET","DELETE","POST"])
def new_board_element():
  if request.method == 'POST':
    board_element = Element(
      board_id=request.args.get('board_id'),
      description=request.args.get('description'),
      category=request.args.get('category')
    )
    db.session.add(board_element)
    db.session.commit()
    result = element_schema.dump(Element.query.get(board_element.id))
    return jsonify({'success': True,
                    'data': {'board_element': result.data}})
  elif request.method == 'DELETE':
    id = request.args.get("board_element_id")
    Element.query.filter_by(id=int(id)).delete()
    db.session.commit()
    return jsonify({'success': True})


@app.route("/kanban/board_elements/<int:id>", methods=["GET","DELETE"])
def delete_element(id):
  if request.method == 'GET':
    pass
  elif request.method == 'DELETE':
    Element.query.filter_by(id=int(id)).delete()
    db.session.commit()
    return jsonify({'success': 'true'})
  else:
    pass

@app.route("/kanban/board_elements/advance", methods=["POST"])
def advance_element():
  id = request.args.get("id")
  element = Element.query.filter_by(id=int(id)).first()
  if element.category == STATUS_TODO:
    element.category = STATUS_IN_PROGRESS
  elif element.category == STATUS_IN_PROGRESS:
    element.category = STATUS_DONE
  else:
    pass
  db.session.commit()
  return jsonify({'success': True})







