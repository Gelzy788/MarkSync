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
    currentUserId = null;

    // Получаем ID текущего пользователя
    fetch('/api/current_user')
        .then(res => res.json())
        .then(data => {
            currentUserId = data.id;
            restoreNoteFromStorage();
            renderNotesList();
        })
        .catch(error => {
            console.error('Ошибка при получении текущего пользователя:', error);
            restoreNoteFromStorage();
            renderNotesList();
        });
});

// Глобальные переменные
let currentNoteId = null;
let currentUserId = null;

// Функции для работы с заметками
function loadNote(title, content, noteId = '') {
    // Проверяем доступ перед загрузкой
    fetch('/api/notes')
        .then(res => res.json())
        .then(data => {
            const hasAccess = noteId ? data.notes.some(note => note.id.toString() === noteId.toString()) : true;
            
            if (!hasAccess && noteId) {
                alert('У вас больше нет доступа к этой заметке');
                removeNoteFromList(noteId);
                createNewNote();
                return;
            }
            
            // Загружаем заметку
            document.getElementById('filename').value = title;
            editor.setValue(content);
            document.getElementById('noteId').value = noteId;
            currentNoteId = noteId;
            
            // Сохраняем в localStorage
            localStorage.setItem('currentNote', JSON.stringify({
                id: noteId,
                title: title,
                content: content
            }));
        })
        .catch(error => {
            console.error('Ошибка при проверке доступа:', error);
        });
}

function removeNoteFromList(noteId) {
    const noteList = document.getElementById('noteList');
    const noteItems = noteList.getElementsByTagName('li');
    
    for (let i = 0; i < noteItems.length; i++) {
        if (noteItems[i].getAttribute('data-note-id') === noteId.toString()) {
            noteList.removeChild(noteItems[i]);
            break;
        }
    }
}

function createNewNote() {
    document.getElementById('filename').value = '';
    editor.setValue('');
    document.getElementById('noteId').value = '';
    currentNoteId = null;
    localStorage.removeItem('currentNote');
}

function restoreNoteFromStorage() {
    const savedNote = localStorage.getItem('currentNote');
    if (savedNote) {
        try {
            const note = JSON.parse(savedNote);
            if (note.title && note.content) {
                // Проверяем доступ перед восстановлением
                fetch('/api/notes')
                    .then(res => res.json())
                    .then(data => {
                        const hasAccess = note.id ? data.notes.some(n => n.id.toString() === note.id.toString()) : true;
                        
                        if (hasAccess) {
                            loadNote(note.title, note.content, note.id);
                        } else {
                            localStorage.removeItem('currentNote');
                        }
                    });
            }
        } catch (e) {
            console.error("Ошибка при восстановлении заметки:", e);
        }
    }
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
                li.setAttribute('data-note-id', note.id);
                li.onclick = () => loadNote(note.name, note.text, note.id);
                list.appendChild(li);
            });
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

    // Проверяем права перед сохранением
    fetch('/api/notes')
        .then(res => res.json())
        .then(data => {
            if (noteId) {
                const hasAccess = data.notes.some(note => note.id.toString() === noteId.toString());
                if (!hasAccess) {
                    alert('У вас нет прав для сохранения этой заметки');
                    removeNoteFromList(noteId);
                    createNewNote();
                    renderNotesList();
                    return Promise.reject('No access rights');
                }
            }

            const formData = new URLSearchParams();
            formData.append('filename', filename);
            formData.append('text', text);
            if (noteId) {
                formData.append('note_id', noteId);
            }

            return fetch('/save_on_server', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData
            });
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                alert("Заметка сохранена!");
                const savedNoteId = data.id || noteId;
                document.getElementById('noteId').value = savedNoteId;
                currentNoteId = savedNoteId;
                
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
            if (error !== 'No access rights') {
                console.error('Ошибка:', error);
                alert('Ошибка при сохранении');
            }
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
            access_level: 'admin'
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
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
        alert(error.message || 'Ошибка при добавлении доступа');
    });
}

function removeUserAccess(userId, event) {
    event.stopPropagation();
    
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
            // Если пользователь удаляет доступ сам себе
            if (userId.toString() === currentUserId.toString()) {
                removeNoteFromList(currentNoteId);
                if (document.getElementById('noteId').value === currentNoteId) {
                    createNewNote();
                }
            }
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