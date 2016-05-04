from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('main.html', title='FOO')

@app.route('/events')
@app.route('/events/<datacenter>')
def events(datacenter=None):
    events = [
        (datacenter, 'somehost', 'some-check', 'Output', 5, 'a minute ago'),
        (datacenter, 'someotherhost', 'some-check2', 'Output2', 6, 'an hour ago'),
        (datacenter, 'anotherhost', 'some-check3', 'Output3', 7, 'a day ago'),
        (datacenter, 'yetanotherhost', 'some-check4', 'Output4', 8, 'a second ago'),
    ]
    return render_template('events.html', title='Events', events=events)

if __name__ == "__main__":
    app.run(debug=True)
