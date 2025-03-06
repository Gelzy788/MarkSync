from flask import Flask, render_template, request
import markdown2

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def editor():
    html = ""
    text = ""
    if request.method == 'POST':
        text = request.form['text']
        html = markdown2.markdown(text, extras=["fenced-code-blocks", "tables", "strike"])
    return render_template('editor.html', text=text, html=html)

if __name__ == '__main__':
    app.run(debug=True)