from inference import KaavachPredictor
p = KaavachPredictor()
print('model_name=', p.model_name)
print('threshold=', p.threshold)
print('has_predict_proba=', hasattr(p.model, 'predict_proba'))
print('numeric_count=', len(p.numeric_features))
print('categorical=', p.categorical_features)
print('numeric_features_sample=', p.numeric_features[:10])
print('categorical_features=', p.categorical_features)
try:
    print('model.classes_ =', getattr(p.model, 'classes_'))
except Exception as e:
    print('classes_ error', e)
try:
    import numpy as np
    sample = {k:0 for k in p.numeric_features}
    for c in p.categorical_features:
        sample[c] = 'tcp'
    print('sample normalized keys:', list(sample.keys())[:20])
    import pandas as pd
    X = pd.DataFrame([sample])
    proba = p.model.predict_proba(X)[:,1][0]
    print('sample predict_proba=', proba)
except Exception as e:
    print('predict_proba error', e)
