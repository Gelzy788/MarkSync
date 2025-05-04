from flask import Flask, render_template, request, jsonify
import markdown2
import re
import os
import requests
from autorisation import token_required
from data.notes import Notes
from config import *

app = Flask(__name__)


def convert_tasks(text):
    def replace_task(match):
        task_text = match.group(1)
        return f'<input type="checkbox"> {task_text}<br>'

    return re.sub(r'<t>(.*?)</t>', replace_task, text)


def convert_diagrams(text):
    def replace_diagram(match):
        chart_params = match.group(1)
        chart_params = re.sub(r'/\*.*?\*/', '', chart_params, flags=re.DOTALL)
        chart_params = ' '.join(chart_params.split())
        try:
            encoded_params = requests.utils.quote(chart_params)
            chart_url = f"https://quickchart.io/chart?width=400&c={encoded_params}"
            return f'<div class="diagram-container"><pre class="diagram-source" style="display:none;">{chart_params}</pre><div class="chart-container"><img src="{chart_url}" alt="Chart"></div></div>'
        except Exception as e:
            return f'<div class="chart-error">Ошибка в диаграмме: {str(e)}</div>'
    return re.sub(r'<d>([\s\S]*?)</d>', replace_diagram, text)


# @app.route('/', methods=['GET', 'POST'])
# def editor():
#     html = ""
#     text = ""
#     if request.method == 'POST':
#         text = request.form['text']
#         text = convert_tasks(text)
#         text = convert_diagrams(text)
#         html = markdown2.markdown(text, extras=["fenced-code-blocks", "tables", "strike"])
#     return render_template('editor.html', text=text, html=html)


@app.route('/save', methods=['POST'])
def save_file():
    filename = request.form['filename']
    text = request.form['text']
    if not filename.endswith('.md'):
        filename += '.md'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    return jsonify({"message": f"Файл '{filename}' сохранён!"})


@app.route('/load', methods=['POST'])
def load_file():
    filename = request.form['filename']
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            text = f.read()
        return jsonify({"text": text})
    return jsonify({"message": "Файл не найден!"})

@app.route('/save_on_server', methods=['POST'])
@token_required
def save_on_server(user):
    filename = request.form['filename']
    text = request.form['text']
    new_note = Notes(name=filename, text=text, user_id=user.ID)
    db.session.add(new_note)
    try:
        db.session.commit()
        return 200
    except Exception as e:
        print("ERROR", e)
        return 401


if __name__ == '__main__':
    app.run(debug=True)