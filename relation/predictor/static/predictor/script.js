document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('predictionForm');
    const resultPanel = document.getElementById('resultPanel');
    const resultContent = document.getElementById('resultContent');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const errorBox = document.getElementById('errorBox');
    const predictionValue = document.getElementById('predictionValue');
    const confidenceValue = document.getElementById('confidenceValue');
    const probabilityItems = document.getElementById('probabilityItems');

    // Soumettre le formulaire
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Afficher le spinner de chargement
        resultPanel.style.display = 'none';
        resultContent.style.display = 'none';
        loadingSpinner.style.display = 'flex';
        errorBox.style.display = 'none';

        try {
            // Créer les données du formulaire
            const formData = new FormData(form);

            // Envoyer la requête POST
            const response = await fetch('/predict/', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            // Masquer le spinner
            loadingSpinner.style.display = 'none';

            if (!response.ok || data.error) {
                // Afficher l'erreur
                errorBox.style.display = 'block';
                document.getElementById('errorMessage').textContent = data.error || 'Une erreur s\'est produite';
                resultPanel.style.display = 'flex';
                return;
            }

            // Afficher les résultats
            displayResults(data);
            resultContent.style.display = 'flex';
            resultPanel.style.display = 'none';

        } catch (error) {
            // Afficher l'erreur
            loadingSpinner.style.display = 'none';
            errorBox.style.display = 'block';
            document.getElementById('errorMessage').textContent = 'Erreur réseau: ' + error.message;
            resultPanel.style.display = 'flex';
        }
    });

    function displayResults(data) {
        // Afficher la prédiction
        const relationLabels = {
            'Husband': 'Mari',
            'Wife': 'Épouse',
            'Own-child': 'Enfant propre',
            'Unmarried': 'Non marié(e)',
            'Not-in-family': 'Pas de lien de famille',
            'Other-relative': 'Autre parent'
        };

        const prediction = data.prediction;
        const displayLabel = relationLabels[prediction] || prediction;

        predictionValue.textContent = displayLabel;
        confidenceValue.textContent = data.confidence;

        // Afficher les probabilités
        probabilityItems.innerHTML = '';
        
        const relationOrder = ['Husband', 'Wife', 'Own-child', 'Unmarried', 'Not-in-family', 'Other-relative'];
        
        relationOrder.forEach(rel => {
            const probability = data.probabilities[rel];
            const displayLabelRel = relationLabels[rel];
            
            const item = document.createElement('div');
            item.className = 'probability-item';
            
            // Calculer la largeur de la barre de progression
            const barWidth = probability;
            
            item.innerHTML = `
                <span class="probability-item-label">${displayLabelRel}</span>
                <div class="probability-item-bar">
                    <div class="probability-item-fill" style="width: ${barWidth}%;"></div>
                </div>
                <span class="probability-item-value">${probability.toFixed(1)}%</span>
            `;
            
            probabilityItems.appendChild(item);
        });
    }

    // Format des nombres pour les inputs
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('input', function() {
            // Optionnel: Valider ou formatter les nombres
        });
    });

    // Afficher la prédiction par défaut au chargement
    resultPanel.style.display = 'flex';
    resultContent.style.display = 'none';
    loadingSpinner.style.display = 'none';
});
