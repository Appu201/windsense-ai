import pickle, gzip, os
with open('models/windsense_rf_model.pkl', 'rb') as f:
    model = pickle.load(f)
with gzip.open('models/windsense_rf_model.pkl.gz', 'wb', compresslevel=9) as f:
    pickle.dump(model, f, protocol=4)
print('Compressed size:', os.path.getsize('models/windsense_rf_model.pkl.gz')/1e6, 'MB')