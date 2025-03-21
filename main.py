from flask import Flask, render_template, request
import markdown2
import re

app = Flask(__name__)

def convert_tasks(text):
    def replace_task(match):
        task_text = match.group(1)
        return f'<input type="checkbox"> {task_text}<br>'
    
    return re.sub(r'<t>(.*?)</t>', replace_task, text)

@app.route('/', methods=['GET', 'POST'])
def editor():
    html = ""
    text = ""
    if request.method == 'POST':
        text = request.form['text']
        text = convert_tasks(text)
        html = markdown2.markdown(text, extras=["fenced-code-blocks", "tables", "strike"])
    return render_template('editor.html', text=text, html=html)

if __name__ == '__main__':
    app.run(debug=True)