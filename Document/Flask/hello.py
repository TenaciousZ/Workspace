#coding:utf8
from flask import Flask, url_for
app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>Index page</h1>"

@app.route("/user/<name>")
def user(name):
    return "<h1>hello %s !</h1>" %name

@app.route('/post/<int:post_id>')#只接受整型参数
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return '<h1>Post %d</h1>' % post_id

@app.route('/projects/')
def projects():
    return 'The project page'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        do_the_login()
    else:
        show_the_login_form()

# @app.route('/')
# def index(): 
# 	pass

# @app.route('/login')
# def login(): 
# 	pass

# @app.route('/user/<username>')
# def profile(username): 
# 	pass

# with app.test_request_context():
# 	print url_for('index')
# 	print url_for('login')
# 	print url_for('login', next='/')
# 	print url_for('profile', username='John Doe')

if __name__ == '__main__':
    app.run(debug=True)
