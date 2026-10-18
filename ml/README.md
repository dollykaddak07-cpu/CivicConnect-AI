# CivicConnect Multilingual ML Classifier

## Model
- **Task:** supervised civic complaint category classification
- **Languages:** English, Hindi, Marathi
- **Features:** word-level TF-IDF (1–2 grams) + character-level TF-IDF (2–5 grams)
- **Classifier:** Logistic Regression
- **Dataset:** `complaint_dataset.csv`
- **Records:** 540 (180 per language; 30 examples × 6 categories × 3 languages)
- **Split:** 80% train / 20% test

The dataset is a **curated academic dataset** created for this college project. It is used to train the classifier; new complaint text is passed to the saved model at runtime and is not looked up by exact match.

## Runtime flow
`Complaint → TF-IDF features → Logistic Regression → predicted category + class probabilities`

The same trained model is used for English, Hindi and Marathi text. Character features help the model handle Unicode scripts and spelling/word-form variation.

Run training from the project root:
```bash
python ml/train_model.py
```
