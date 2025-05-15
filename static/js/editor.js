document.addEventListener('DOMContentLoaded', () => {
    const editorElement = CodeMirror.fromTextArea(document.getElementById('markdownEditor'), {
        mode: 'markdown',
        lineNumbers: true,
        theme: 'default',
        lineWrapping: true,
        autofocus: true,
        fixedGutter: true,
        viewportMargin: Infinity,
        styleActiveLine: true,
        height: "400px",
        maxHeight: "400px",
        scrollHorizontally: false
    });
    window.editor = editorElement;

    // Инициализация текущей заметки
    currentNoteId = document.getElementById('noteId').value;

    restoreNoteFromStorage();
    renderNotesList();
});

// Глобальные переменные
let currentNoteId = null;

// Функции для работы с заметками
function loadNote(title, content, noteId = '') {
    console.log("Загрузка заметки:", title, content, noteId);
    document.getElementById('filename').value = title;
    editor.setValue(content);
    document.getElementById('noteId').value = noteId;
    currentNoteId = noteId;
    
    // Сохраняем данные заметки в localStorage
    localStorage.setItem('currentNote', JSON.stringify({
        id: noteId,
        title: title,
        content: content
    }));
}

function createNewNote() {
    document.getElementById('filename').value = '';
    editor.setValue('');
    document.getElementById('noteId').value = '';
    currentNoteId = null;
    
    // Очищаем сохранённую заметку
    localStorage.removeItem('currentNote');
}

function restoreNoteFromStorage() {
    const savedNote = localStorage.getItem('currentNote');
    if (savedNote) {
        try {
            const note = JSON.parse(savedNote);
            if (note.title && note.content) {
                loadNote(note.title, note.content, note.id);
                return true;
            }
        } catch (e) {
            console.error("Ошибка при восстановлении заметки:", e);
        }
    }
    return false;
}

function renderNotesList() {
    fetch('/api/notes')
        .then(res => res.json())
        .then(data => {
            const list = document.getElementById('noteList');
            list.innerHTML = '';
            data.notes.forEach(note => {
                const li = document.createElement('li');
                li.className = 'list-group-item bg-transparent text-white';
                li.textContent = note.name;
                li.onclick = () => loadNote(note.name, note.text, note.id);
                list.appendChild(li);
            });

            const savedNote = localStorage.getItem('currentNote');
            if (savedNote) {
                try {
                    const note = JSON.parse(savedNote);
                    const exists = [...list.children].some(item => item.textContent === note.title);
                    if (!exists && note.id) {
                        const li = document.createElement('li');
                        li.className = 'list-group-item bg-transparent text-white';
                        li.textContent = note.title;
                        li.onclick = () => loadNote(note.title, note.content, note.id);
                        list.appendChild(li);
                    }
                } catch (e) {
                    console.error("Ошибка при обработке сохранённой заметки:", e);
                }
            }
        })
        .catch(error => {
            console.error('Ошибка при загрузке списка заметок:', error);
        });
}

// Функции для работы с задачами и диаграммами
function insertTaskTemplate() {
    const template = '<t>Новая задача</t>';
    const cursor = editor.getCursor();
    editor.replaceRange(template, cursor);
    editor.focus();
}

function openDiagramModal() {
    document.getElementById('modalOverlay').style.display = 'block';
    document.getElementById('diagramModal').style.display = 'block';
}

function closeDiagramModal() {
    document.getElementById('modalOverlay').style.display = 'none';
    document.getElementById('diagramModal').style.display = 'none';
    document.getElementById('diagramForm').reset();
}

document.getElementById('diagramForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const type = document.getElementById('diagramType').value;
    const labels = document.getElementById('labels').value.trim().split(',').map(s => s.trim());
    const datasetLabel = document.getElementById('datasetLabel').value.trim();
    const dataValues = document.getElementById('dataValues').value.trim().split(',').map(Number);
    const template = `<d>
{
  type: '${type}',
  data: {
    labels: [${labels.map(l => `'${l}'`).join(', ')}],
    datasets: [{
      label: '${datasetLabel}',
      data: [${dataValues.join(',')}]
    }]
  }
}
</d>`;
    const cursor = editor.getCursor();
    editor.replaceRange(template, cursor);
    editor.setCursor({ line: cursor.line + 2, ch: 4 });
    editor.focus();
    closeDiagramModal();
});

function insertDiagramTemplate() {
    openDiagramModal();
}

// Функции для предпросмотра и сохранения
function toggleEditor() {
    document.getElementById('edit-tab').classList.add('active');
    document.getElementById('preview-tab').classList.remove('active');
    document.getElementById('editor-section').style.display = 'block';
    document.getElementById('preview-section').style.display = 'none';
}

function togglePreview() {
    document.getElementById('edit-tab').classList.remove('active');
    document.getElementById('preview-tab').classList.add('active');
    document.getElementById('editor-section').style.display = 'none';
    document.getElementById('preview-section').style.display = 'block';
    previewMarkdown();
}

function previewMarkdown() {
    const text = editor.getValue();
    if (!text) {
        alert("Введите текст для предпросмотра");
        return;
    }
    fetch('/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('previewContent').innerHTML = data.html;
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Не удалось получить предпросмотр');
    });
}

function saveNote() {
    const filename = document.getElementById('filename').value.trim();
    const text = editor.getValue();
    const noteId = document.getElementById('noteId').value;

    if (!filename || !text) {
        alert("Имя файла и текст обязательны.");
        return;
    }

    const formData = new URLSearchParams();
    formData.append('filename', filename);
    formData.append('text', text);
    if (noteId) {
        formData.append('note_id', noteId);
    }

    fetch('/save_on_server', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert("Заметка сохранена!");
            
            // Обновляем ID заметки (особенно важно для новых заметок)
            const savedNoteId = data.id || noteId;
            document.getElementById('noteId').value = savedNoteId;
            currentNoteId = savedNoteId;
            
            // Обновляем данные в localStorage
            localStorage.setItem('currentNote', JSON.stringify({
                id: savedNoteId,
                title: filename,
                content: text
            }));
            
            renderNotesList();
        } else {
            alert("Ошибка при сохранении: " + (data.message || ''));
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Ошибка при сохранении');
    });
}

// Функции для работы с доступом к заметкам
function openAccessModal() {
    if (!currentNoteId) {
        alert("Сначала загрузите или создайте заметку");
        return;
    }
    
    document.getElementById('modalOverlay').style.display = 'block';
    document.getElementById('accessModal').style.display = 'block';
    loadAccessList();
}

function closeAccessModal() {
    document.getElementById('modalOverlay').style.display = 'none';
    document.getElementById('accessModal').style.display = 'none';
}

function loadAccessList() {
    fetch(`/api/notes/${currentNoteId}/access`)
        .then(res => res.json())
        .then(data => {
            const accessList = document.getElementById('accessList');
            accessList.innerHTML = '';
            
            if (data.users && data.users.length > 0) {
                data.users.forEach(user => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item bg-transparent text-white access-user-item';
                    li.innerHTML = `
                        <span>${user.username} (ID: ${user.id})</span>
                        <button class="remove-access-btn" onclick="removeUserAccess(${user.id}, event)">Удалить</button>
                    `;
                    accessList.appendChild(li);
                });
            } else {
                accessList.innerHTML = '<li class="list-group-item bg-transparent text-white">Нет пользователей с доступом</li>';
            }
        })
        .catch(error => {
            console.error('Ошибка при загрузке списка доступа:', error);
            alert('Не удалось загрузить список доступа');
        });
}

function addUserAccess() {
    const userId = document.getElementById('userIdInput').value.trim();
    if (!userId) {
        alert("Введите ID пользователя");
        return;
    }

    fetch(`/api/notes/${currentNoteId}/access`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            user_id: userId,
            access_level: 'admin' // Пока не имеет веса
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('userIdInput').value = '';
            loadAccessList();
        } else {
            alert(data.message || 'Ошибка при добавлении доступа');
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Ошибка при добавлении доступа');
    });
}

function removeUserAccess(userId, event) {
    event.stopPropagation();  // Предотвращаем всплытие события
    
    if (!confirm("Вы уверены, что хотите удалить доступ у этого пользователя?")) {
        return;
    }

    fetch(`/api/notes/${currentNoteId}/access/${userId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            loadAccessList();
        } else {
            alert(data.message || 'Ошибка при удалении доступа');
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert(error.message || 'Ошибка при удалении доступа');
    });
}

// Функции для экспорта и скачивания
async function exportToPDF() {
    const filename = document.getElementById('filename').value.trim();
    const text = editor.getValue();
    if (!filename || !text) {
        alert("Введите имя файла и текст.");
        return;
    }

    const pdf = new jspdf.jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4'
    });

    const A4_WIDTH = 210;
    const A4_HEIGHT = 297;
    const MARGIN = 20;
    let currentY = MARGIN;

    const blocks = text.split(/(<d>[\s\S]*?<\/d>)/);
    for (let block of blocks) {
        if (block.startsWith('<d>') && block.endsWith('</d>')) {
            const chartCode = block.substring(3, block.length - 4).trim();
            try {
                const url = `https://quickchart.io/chart?width=600&c=${encodeURIComponent(chartCode)}`;
                const img = await loadImage(url);
                if (currentY > A4_HEIGHT - MARGIN) {
                    pdf.addPage();
                    currentY = MARGIN;
                }
                const widthRatio = (A4_WIDTH - 2 * MARGIN) / img.width;
                const imgHeight = img.height * widthRatio;
                pdf.addImage(img.src, 'PNG', MARGIN, currentY, A4_WIDTH - 2 * MARGIN, imgHeight);
                currentY += imgHeight + 10;
            } catch (e) {
                console.error("Ошибка при загрузке диаграммы:", e);
            }
        } else {
            const lines = pdf.splitTextToSize(block, A4_WIDTH - 2 * MARGIN);
            pdf.setFontSize(12);
            pdf.text(lines, MARGIN, currentY);
            currentY += lines.length * 6;
            if (currentY > A4_HEIGHT - MARGIN) {
                pdf.addPage();
                currentY = MARGIN;
            }
        }
    }

    pdf.save(filename + '.pdf');
}

function loadImage(url) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = url;
    });
}

function downloadFile() {
    const format = document.getElementById('downloadFormat').value;
    const text = editor.getValue();
    const filename = document.getElementById('filename').value.trim() || 'untitled';

    if (format === 'pdf') {
        exportToPDF();
        return;
    }

    let blob;
    let mime = 'text/plain';
    let ext = format;

    if (format === 'html') {
        mime = 'text/html';
        blob = new Blob([`<html><body><pre>${text}</pre></body></html>`], { type: mime });
    } else {
        blob = new Blob([text], { type: mime });
    }

    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename + '.' + ext;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}