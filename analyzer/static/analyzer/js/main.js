document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const fileName = document.getElementById('fileName');

    fileInput.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file) return;

        if (!file.name.endsWith('.csv')) {
            fileName.textContent = 'Please select a CSV file';
            return;
        }

        fileName.textContent = file.name;
        
        const maxSize = 5 * 1024 * 1024;
        if (file.size > maxSize) {
            fileName.textContent = 'File size must be less than 5MB';
            return;
        }

        await uploadFile(file);
    });

    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            fileName.textContent = 'Uploading...';
            
            const response = await fetch('/upload/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            });

            const data = await response.json();
            
            if (data.success) {
                window.location.href = '/analyze/';
            } else {
                fileName.textContent = data.error || 'Upload error';
            }
        } catch (error) {
            console.error('Upload error:', error);
            fileName.textContent = 'Network error';
        }
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});