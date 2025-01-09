document.addEventListener('DOMContentLoaded', async function() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const plotType = document.getElementById('plotType');
    const checkboxes = document.querySelectorAll('input[name="columns"]');
    const plotContainer = document.getElementById('plotContainer');
    const statsContent = document.getElementById('statsContent');
    const dataPreview = document.getElementById('dataPreview');
    const exportBtn = document.getElementById('exportBtn');
    let currentGraphImage = null;
    let allStats = null;

    function validateColumnSelection() {
        const selectedColumns = Array.from(checkboxes)
            .filter(checkbox => checkbox.checked)
            .map(checkbox => checkbox.value);

        if (selectedColumns.length === 0) {
            alert('Veuillez sélectionner au moins une colonne');
            return null;
        }

        const type = plotType.value;
        if (document.getElementById('graph').classList.contains('active')) {
            if (type === 'bar' && selectedColumns.length > 2) {
                alert('Veuillez sélectionner 1 ou 2 colonnes pour un graphique à barres');
                return null;
            } else if (type === 'pie' && selectedColumns.length !== 1) {
                alert('Veuillez sélectionner exactement 1 colonne pour un diagramme circulaire');
                return null;
            } else if (type === 'line' && selectedColumns.length !== 2) {
                alert('Veuillez sélectionner exactement 2 colonnes pour un graphique linéaire');
                return null;
            } else if (type === 'histogram' && selectedColumns.length !== 1) {
                alert('Veuillez sélectionner exactement 1 colonne pour un histogramme');
                return null;
            }
        }

        return selectedColumns;
    }

    function addStatsFilter() {
        const filterContainer = document.createElement('div');
        filterContainer.className = 'stats-filter';
        filterContainer.innerHTML = `
            <label class="control-label">Filtrer les statistiques par colonne:</label>
            <select class="control-select" id="statsFilter">
                <option value="all">Toutes les colonnes</option>
                ${Array.from(checkboxes).map(checkbox => 
                    `<option value="${checkbox.value}">${checkbox.value}</option>`
                ).join('')}
            </select>
        `;
        
        statsContent.insertAdjacentElement('beforebegin', filterContainer);
        
        document.getElementById('statsFilter').addEventListener('change', function(e) {
            const selectedColumn = e.target.value;
            displayStats({
                column_stats: selectedColumn === 'all' ? allStats.column_stats : 
                    { [selectedColumn]: allStats.column_stats[selectedColumn] },
                dataset_info: allStats.dataset_info
            });
        });
    }

    function showLoading() {
        plotContainer.innerHTML = '<div class="loading">Chargement...</div>';
    }

    function handleGraphClick(event) {
        if (event.target.tagName === 'IMG' && currentGraphImage) {
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <img src="data:image/png;base64,${currentGraphImage}" alt="Graph visualization">
                    <button class="close-btn">&times;</button>
                </div>
            `;
            
            document.body.appendChild(modal);
            document.body.style.overflow = 'hidden';
            
            modal.querySelector('.close-btn').onclick = () => {
                document.body.removeChild(modal);
                document.body.style.overflow = 'auto';
            };
            
            modal.onclick = (e) => {
                if (e.target === modal) {
                    document.body.removeChild(modal);
                    document.body.style.overflow = 'auto';
                }
            };
        }
    }

    function formatStatValue(value) {
        if (typeof value === 'number') {
            return Number.isInteger(value) ? value : value.toFixed(2);
        }
        return value;
    }

    function displayStats(stats) {
        const { column_stats, dataset_info } = stats;
        
        let html = '<div class="stats-container">';
        
        html += `
            <div class="stats-section">
                <h3>Vue d'ensemble du Dataset</h3>
                <div class="dataset-info">
                    <div class="info-item">
                        <span class="info-label">Nombre total de lignes:</span>
                        <span class="info-value">${dataset_info.total_rows}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Nombre de colonnes:</span>
                        <span class="info-value">${dataset_info.total_columns}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Utilisation mémoire:</span>
                        <span class="info-value">${dataset_info.memory_usage} MB</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Lignes dupliquées:</span>
                        <span class="info-value">${dataset_info.duplicated_rows}</span>
                    </div>
                </div>
            </div>`;

        html += '<div class="stats-section"><h3>Statistiques par Colonne</h3>';
        
        for (const [columnName, columnStats] of Object.entries(column_stats)) {
            html += `
                <div class="column-stats">
                    <h4>${columnName}</h4>
                    <div class="stats-grid">`;
            
            if (columnStats.type === 'numeric') {
                html += `
                    <div class="stat-item"><span>Moyenne:</span> <span>${formatStatValue(columnStats.mean)}</span></div>
                    <div class="stat-item"><span>Médiane:</span> <span>${formatStatValue(columnStats.median)}</span></div>
                    <div class="stat-item"><span>Écart-type:</span> <span>${formatStatValue(columnStats.std)}</span></div>
                    <div class="stat-item"><span>Minimum:</span> <span>${formatStatValue(columnStats.min)}</span></div>
                    <div class="stat-item"><span>Maximum:</span> <span>${formatStatValue(columnStats.max)}</span></div>
                    <div class="stat-item"><span>Q1:</span> <span>${formatStatValue(columnStats.q1)}</span></div>
                    <div class="stat-item"><span>Q3:</span> <span>${formatStatValue(columnStats.q3)}</span></div>
                    <div class="stat-item"><span>Asymétrie:</span> <span>${formatStatValue(columnStats.skewness)}</span></div>
                    <div class="stat-item"><span>Aplatissement:</span> <span>${formatStatValue(columnStats.kurtosis)}</span></div>`;
            } else {
                html += `
                    <div class="stat-item"><span>Valeurs uniques:</span> <span>${columnStats.unique_count}</span></div>
                    <div class="stat-item"><span>Valeurs les plus fréquentes:</span>
                        <ul class="most-common-list">
                            ${columnStats.most_common.map(item => 
                                `<li>${item.value}: ${item.count} (${item.percentage}%)</li>`
                            ).join('')}
                        </ul>
                    </div>`;
            }

            html += `
                    <div class="stat-item"><span>Valeurs manquantes:</span> <span>${columnStats.missing_values} (${columnStats.missing_percentage}%)</span></div>
                </div>
            </div>`;
        }

        html += '</div></div>';
        statsContent.innerHTML = html;
    }

    analyzeBtn.addEventListener('click', async function() {
        const selectedColumns = validateColumnSelection();
        if (!selectedColumns) return;

        try {
            showLoading();
            
            if (document.getElementById('graph').classList.contains('active')) {
                const response = await fetch(`/plot/?columns=${selectedColumns.join(',')}&type=${plotType.value}`);
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Erreur lors de la génération du graphique');
                }
                
                if (data.error) {
                    alert(data.error);
                    return;
                }
                
                currentGraphImage = data.image;
                plotContainer.innerHTML = `<img src="data:image/png;base64,${data.image}" alt="Plot" class="plot-image" style="cursor: pointer;"/>`;
            }
            
        } catch (error) {
            alert(error.message);
            plotContainer.innerHTML = '';
        }
    });

    exportBtn.addEventListener('click', async () => {
        try {
            showLoading();
            
            const response = await fetch('/generate_pdf/', {
                method: 'GET',
                headers: {
                    'Accept': 'application/pdf',
                }
            });
            
            if (!response.ok) {
                throw new Error('Erreur lors de la génération du PDF');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = 'analyse.pdf';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            plotContainer.innerHTML = 'PDF généré avec succès!';
        } catch (error) {
            alert(error.message);
        }
    });

    // Initial data load
    try {
        const previewResponse = await fetch('/preview/');
        const previewData = await previewResponse.json();
        
        if (previewData.error) {
            alert(previewData.error);
            return;
        }
        
        dataPreview.innerHTML = `
            <div class="data-info">Nombre total de lignes: ${previewData.total_rows}</div>
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>${previewData.columns.map(col => `<th>${col}</th>`).join('')}</tr>
                    </thead>
                    <tbody>
                        ${previewData.data.map(row => `
                            <tr>${previewData.columns.map(col => `<td>${row[col]}</td>`).join('')}</tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        if (previewData.stats) {
            allStats = previewData.stats;
            displayStats(previewData.stats);
            addStatsFilter();
        }
    } catch (error) {
        console.error('Error:', error);
        alert(`Error loading data: ${error.message}`);
    }

    plotContainer.addEventListener('click', handleGraphClick);
    
    document.querySelectorAll('.tab-btn').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
            
            button.classList.add('active');
            document.getElementById(button.dataset.tab).classList.add('active');
        });
    });
});