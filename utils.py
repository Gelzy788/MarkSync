import re
import requests
from io import BytesIO
import base64
import markdown2

def markdown_to_html(text):
    return markdown2.markdown(text, extras=["fenced-code-blocks", "tables", "strike"])

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
            response = requests.get(chart_url)
            if response.status_code == 200:
                image_data = BytesIO(response.content)
                return f'<img src="data:image/png;base64,{base64.b64encode(image_data.getvalue()).decode("utf-8")}" alt="Chart">'
            else:
                return f'<div class="chart-error">Ошибка в диаграмме: Невозможно загрузить изображение.</div>'
        except Exception as e:
            return f'<div class="chart-error">Ошибка в диаграмме: {str(e)}</div>'
    return re.sub(r'<d>([\s\S]*?)</d>', replace_diagram, text)
