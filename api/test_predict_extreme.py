from inference import KaavachPredictor
p = KaavachPredictor()
features = {c:0 for c in p.numeric_features}
for c in p.categorical_features:
    features[c] = 'icmp'
# Set extreme values
for k in list(features.keys()):
    if k in p.numeric_features:
        features[k] = 9999
print('sending features keys count:', len(features))
res = p.predict_one(features)
print('result:', res)
# print individual probabilities if using predict_proba
import pandas as pd
X = pd.DataFrame([features])
print('proba direct:', p.model.predict_proba(X)[:,1][0])
