document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('results-modal');
    const closeBtn = document.querySelector('.close');
    const viewButtons = document.querySelectorAll('.view-btn');

    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const analysisId = this.getAttribute('data-id');
            fetchAnalysisDetails(analysisId);
        });
    });

    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});

function fetchAnalysisDetails(id) {
    fetch(`/analyzer/analysis/${id}/`)
        .then(response => response.json())
        .then(data => {
            displayAnalysisDetails(data);
            document.getElementById('results-modal').style.display = 'block';
        })
        .catch(error => {
            console.error('Error fetching analysis details:', error);
        });
}

function displayAnalysisDetails(data) {
    const detailsContainer = document.getElementById('analysis-details');
    let html = '<div class="analysis-details">';
    
    // Format your analysis details here
    for (const [key, value] of Object.entries(data)) {
        html += `<div class="detail-item">
            <strong>${formatKey(key)}:</strong> 
            <span>${formatValue(value)}</span>
        </div>`;
    }
    
    html += '</div>';
    detailsContainer.innerHTML = html;
}

function formatKey(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatValue(value) {
    if (typeof value === 'object') {
        return JSON.stringify(value, null, 2);
    }
    return value;
}