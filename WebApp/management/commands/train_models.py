from django.core.management.base import BaseCommand
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
import joblib

class Command(BaseCommand):
    help = 'Train and save machine learning models'

    def handle(self, *args, **kwargs):
        data = load_iris()
        X_train, X_test, y_train, y_test = train_test_split(data.data, data.target, test_size=0.2, random_state=42)

        decision_tree_clf = DecisionTreeClassifier()
        decision_tree_clf.fit(X_train, y_train)
        joblib.dump(decision_tree_clf, 'decision_tree_model.pkl')
        self.stdout.write(self.style.SUCCESS('DecisionTreeClassifier trained and saved.'))

        random_forest_clf = RandomForestClassifier()
        random_forest_clf.fit(X_train, y_train)
        joblib.dump(random_forest_clf, 'random_forest_model.pkl')
        self.stdout.write(self.style.SUCCESS('RandomForestClassifier trained and saved.'))
