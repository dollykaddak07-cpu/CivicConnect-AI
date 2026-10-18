# CivicConnect AI — AI/ML Project Documentation

## 1. Project Title
**CivicConnect AI: Multilingual Citizen Complaint & Governance CRM with ML-Based Complaint Classification**

## 2. AI/ML Problem Statement
Citizens submit civic complaints in natural language. Manually reading every complaint and deciding which department/category it belongs to is slow and inconsistent. The ML module automatically predicts the category of a complaint from its text.

## 3. Objective
- Build a labeled civic complaint dataset.
- Preprocess complaint text.
- Convert text into numerical features using TF-IDF.
- Train a supervised Logistic Regression classifier.
- Evaluate the model using accuracy, precision, recall and F1-score.
- Integrate the trained model into the CivicConnect FastAPI application.
- Display the model prediction and confidence to the user.

## 4. Dataset
File: `ml/complaint_dataset.csv`

- 540 complaint records.
- 6 classes.
- 40 records per class.
- Columns: `text`, `category`.

Classes:
1. Infrastructure
2. Water Supply
3. Electricity
4. Sanitation
5. Public Safety
6. Other

The dataset is a curated academic-domain dataset created for this prototype. It is included openly so the training process is reproducible.

## 5. Data Preprocessing
The TF-IDF vectorizer performs text normalization and converts words/phrases into numerical features. The model uses word unigrams and bigrams with sublinear TF scaling.

## 6. Feature Extraction — TF-IDF
TF-IDF gives higher importance to words that are useful for distinguishing complaint categories and lower importance to very common words.

Conceptually:

`TF-IDF(t,d) = TF(t,d) × IDF(t)`

## 7. Machine Learning Algorithm — Logistic Regression
Logistic Regression is a supervised classification algorithm. It learns the relationship between TF-IDF features and the complaint category.

The trained pipeline is:

`Complaint Text → TF-IDF → Logistic Regression → Category + Probability`

## 8. Train/Test Split
- 80% training data: 192 records
- 20% test data: 48 records
- Stratified split
- Random state: 42

## 9. Evaluation
Current evaluation on the included dataset:

| Metric | Result |
|---|---:|
| Accuracy | 100% |
| Weighted Precision | 100% |
| Weighted Recall | 100% |
| Weighted F1 | 100% |

The dataset is small and curated for an academic prototype, so these results should not be presented as production-level generalization.

## 10. Integration With CivicConnect
When the user leaves Category as **AI will automatically classify**, the backend sends the complaint text to the trained classifier.

The application stores:
- ML predicted category
- ML confidence
- model name

The AI result panel displays the classification after submission.

## 11. API
### Model information
`GET /api/ml/info`

### Live prediction
`POST /api/ml/predict`

Example request:

```json
{
  "text": "There is a large pothole on the main road near the market."
}
```

Example response:

```json
{
  "category": "Infrastructure",
  "confidence": 88.73,
  "probabilities": {
    "Electricity": 2.1,
    "Infrastructure": 88.73,
    "Other": 1.5,
    "Public Safety": 4.2,
    "Sanitation": 1.4,
    "Water Supply": 2.07
  },
  "model": "TF-IDF + Logistic Regression"
}
```

## 12. Limitations
- The included dataset is small and curated.
- The current classifier is trained primarily on English complaint text.
- Hindi/Marathi complaints continue through the existing multilingual/rule-based civic pipeline unless an appropriate multilingual training dataset is added.
- Production deployment would require a much larger, diverse, real-world labeled dataset.

## 13. Future Scope
- Expand the dataset with thousands of real anonymized complaints.
- Add multilingual TF-IDF or transformer-based multilingual embeddings.
- Compare Logistic Regression, SVM and Naive Bayes.
- Add cross-validation and hyperparameter tuning.
- Deploy model monitoring and drift detection.
- Add human feedback to continuously improve the classifier.

## 14. Viva Explanation
> “For the AI/ML part of CivicConnect AI, I implemented supervised text classification. I created a labeled civic complaint dataset, converted complaint text into TF-IDF numerical features, and trained a Logistic Regression classifier to predict the complaint category. I evaluated it using a stratified train-test split and integrated the saved model into FastAPI, so a new complaint can be classified automatically in real time.”


## Multilingual ML enhancement

The final version uses one trained supervised classifier for **English, Hindi and Marathi**. The training dataset contains 540 curated labeled records: 180 per language across six categories. The feature extractor combines word-level TF-IDF with character-level TF-IDF, followed by Logistic Regression.

At runtime, a newly submitted complaint is sent to the saved `complaint_classifier.joblib`; the system does not simply search the dataset for a matching sentence. The model returns a predicted category and probabilities for all six classes.

Example predictions:
- `मुख्य बाजार के पास सड़क पर बड़ा गड्ढा है।` → Infrastructure
- `मुख्य बाजाराजवळ रस्त्यावर मोठा खड्डा पडला आहे.` → Infrastructure
- `हमारे क्षेत्र में सुबह से पानी की सप्लाई बंद है।` → Water Supply
- `आपल्या भागात सकाळपासून पाणीपुरवठा बंद आहे.` → Water Supply

**Academic limitation:** the dataset is curated for demonstration and evaluation. A production system should be retrained on a larger, naturally collected, reviewed multilingual complaint dataset.
