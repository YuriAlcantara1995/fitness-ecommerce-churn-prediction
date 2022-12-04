import numpy as np
import pandas as pd

import pickle

from sklearn import feature_extraction
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

class Model(object):
    def __init__(self) -> None:
        with open('models/best_model.bin', 'rb') as f:
            self.model = pickle.load(f)

    def process_dataframe(self, customers):
        customers = pd.get_dummies(customers, columns=["FirstPlanVariantId"])
        customers = customers[['NumberOfDaysActive', 'AmountTasksPerMonth', 'AmountTasksLastMonth', 'FirstPlanVariantId_Basic_Plan', 'FirstPlanVariantId_Pro_Plan', 'FirstPlanVariantId_WeightBet']]
        return customers

    def predict(self, customers):
        df = self.process_dataframe(customers)
        customers.Churned = self.model.predict(df)
        return customers
