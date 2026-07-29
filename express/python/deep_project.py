#############################################################
# IBM FINAL PROJECT
# DEEP LEARNING USING STRAVA DATASET
#############################################################

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt
import numpy as np

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Dropout
from tensorflow.keras.callbacks import EarlyStopping

#############################################################
# LOAD DATASET
#############################################################

df = pd.read_csv("data/Cleaned_data.csv")

print("="*60)
print("FIRST 5 ROWS")
print("="*60)

print(df.head())

print()

#############################################################

print("="*60)
print("DATASET INFO")
print("="*60)

print(df.info())

print()

#############################################################

print("="*60)
print("DATASET SHAPE")
print("="*60)

print(df.shape)

print()

#############################################################

print("="*60)
print("SUMMARY STATISTICS")
print("="*60)

print(df.describe())

print()

#############################################################

print("="*60)
print("MISSING VALUES")
print("="*60)

print(df.isnull().sum())

#############################################################
# CREATE TARGET VARIABLE
#############################################################

def ride_class(power):

    if power < 90:
        return "Easy"

    elif power < 120:
        return "Moderate"

    else:
        return "Hard"

df["Ride Difficulty"] = df["Average Watts"].apply(ride_class)

#############################################################
# CLASS DISTRIBUTION
#############################################################

print()

print("="*60)
print("CLASS DISTRIBUTION")
print("="*60)

print(df["Ride Difficulty"].value_counts())

plt.figure(figsize=(6,4))

df["Ride Difficulty"].value_counts().plot(kind="bar")

plt.title("Ride Difficulty Distribution")

plt.xlabel("Ride Class")

plt.ylabel("Count")

plt.show()

#############################################################
# SELECT FEATURES
#############################################################

features = [

    "Moving Time",
    "Distance",
    "Max Speed",
    "Average Speed",
    "Elevation Gain",
    "Elevation Loss",
    "Elevation Low",
    "Elevation High",
    "Max Grade",
    "Average Grade"

]

X = df[features]

y = df["Ride Difficulty"]

#############################################################
# LABEL ENCODING
#############################################################

encoder = LabelEncoder()

y = encoder.fit_transform(y)

print()

print("="*60)
print("ENCODED CLASSES")
print("="*60)

for i, name in enumerate(encoder.classes_):
    print(i, "->", name)

#############################################################
# TRAIN TEST SPLIT
#############################################################

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y

)

#############################################################
# STANDARDIZATION
#############################################################

scaler = StandardScaler()

X_train = scaler.fit_transform(X_train)

X_test = scaler.transform(X_test)

#############################################################
# ONE HOT ENCODING
#############################################################

y_train = tf.keras.utils.to_categorical(y_train)

y_test = tf.keras.utils.to_categorical(y_test)

print()

print("="*60)
print("PREPROCESSING COMPLETE")
print("="*60)

print("Training Samples :", X_train.shape[0])

print("Testing Samples :", X_test.shape[0])

print("Input Features :", X_train.shape[1])

print("Number of Classes :", y_train.shape[1])

#############################################################
# MODEL 1
# Simple Neural Network
#############################################################

model1 = Sequential([
    Dense(64, activation="relu", input_shape=(X_train.shape[1],)),
    Dense(32, activation="relu"),
    Dense(3, activation="softmax")
])

model1.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

early_stop = EarlyStopping(
    monitor="val_loss",
    patience=10,
    restore_best_weights=True
)

history1 = model1.fit(
    X_train,
    y_train,
    validation_split=0.2,
    epochs=100,
    batch_size=32,
    callbacks=[early_stop],
    verbose=1
)

loss1, acc1 = model1.evaluate(X_test, y_test, verbose=0)

print("\nModel 1 Accuracy:", round(acc1 * 100, 2), "%")

#############################################################
# MODEL 2
# Deeper Network
#############################################################

model2 = Sequential([
    Dense(128, activation="relu", input_shape=(X_train.shape[1],)),
    Dense(64, activation="relu"),
    Dense(32, activation="relu"),
    Dense(3, activation="softmax")
])

model2.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

history2 = model2.fit(
    X_train,
    y_train,
    validation_split=0.2,
    epochs=100,
    batch_size=32,
    callbacks=[early_stop],
    verbose=1
)

loss2, acc2 = model2.evaluate(X_test, y_test, verbose=0)

print("\nModel 2 Accuracy:", round(acc2 * 100, 2), "%")

#############################################################
# MODEL 3
# Dropout Network
#############################################################

model3 = Sequential([
    Dense(128, activation="relu", input_shape=(X_train.shape[1],)),
    Dropout(0.30),
    Dense(64, activation="relu"),
    Dropout(0.20),
    Dense(32, activation="relu"),
    Dense(3, activation="softmax")
])

model3.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

history3 = model3.fit(
    X_train,
    y_train,
    validation_split=0.2,
    epochs=100,
    batch_size=32,
    callbacks=[early_stop],
    verbose=1
)

loss3, acc3 = model3.evaluate(X_test, y_test, verbose=0)

print("\nModel 3 Accuracy:", round(acc3 * 100, 2), "%")

#############################################################
# MODEL COMPARISON
#############################################################

print("\n" + "="*60)
print("MODEL COMPARISON")
print("="*60)

print(f"Model 1 Accuracy : {acc1*100:.2f}%")
print(f"Model 2 Accuracy : {acc2*100:.2f}%")
print(f"Model 3 Accuracy : {acc3*100:.2f}%")

accuracies = [acc1*100, acc2*100, acc3*100]
labels = ["Model 1", "Model 2", "Model 3"]

plt.figure(figsize=(6,4))
plt.bar(labels, accuracies)
plt.ylabel("Accuracy (%)")
plt.title("Deep Learning Model Comparison")
plt.show()

#############################################################
# ACCURACY CURVES
#############################################################

plt.figure(figsize=(8,5))

plt.plot(history2.history["accuracy"], label="Training Accuracy")
plt.plot(history2.history["val_accuracy"], label="Validation Accuracy")

plt.title("Model 2 Accuracy")
plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.legend()

plt.show()

#############################################################
# LOSS CURVES
#############################################################

plt.figure(figsize=(8,5))

plt.plot(history2.history["loss"], label="Training Loss")
plt.plot(history2.history["val_loss"], label="Validation Loss")

plt.title("Model 2 Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.legend()

plt.show()

#############################################################
# CONFUSION MATRIX
#############################################################

predictions = model2.predict(X_test)

y_pred = np.argmax(predictions, axis=1)
y_true = np.argmax(y_test, axis=1)

cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(6,6))

plt.imshow(cm, interpolation="nearest")

plt.title("Confusion Matrix")

plt.colorbar()

tick_marks = np.arange(len(encoder.classes_))

plt.xticks(tick_marks, encoder.classes_, rotation=45)
plt.yticks(tick_marks, encoder.classes_)

for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        plt.text(j, i, cm[i, j],
                 ha="center",
                 va="center")

plt.xlabel("Predicted")
plt.ylabel("Actual")

plt.show()

#############################################################
# CLASSIFICATION REPORT
#############################################################

print("\n")
print("="*60)
print("CLASSIFICATION REPORT")
print("="*60)

print(classification_report(
    y_true,
    y_pred,
    target_names=encoder.classes_
))