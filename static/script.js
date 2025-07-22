// Load all files from backend API and render them
fetch('/api/files')
  .then(res => res.json())
  .then(files => {
    const container = document.querySelector('#file-cards');
    container.innerHTML = '';

    files.forEach(file => {
      const div = document.createElement('div');
      div.className = 'card';
      div.innerHTML = `
        <span>📁 ${file.category}</span>
        <h3>${file.name}</h3>
        <p>Country: ${file.country}</p>
        <p>File: ${file.filename}</p>
        <div class="price">₹${file.price}</div>

        <button onclick="previewFile('${file.filename}', this