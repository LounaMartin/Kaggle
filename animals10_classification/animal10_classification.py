# -*- coding: utf-8 -*-
"""animal10-classification.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1yxiTXq5JIr9Xb67KQlPKa1jphDRECtkr

! mkdir ~/.kaggle
! cp kaggle.json ~/.kaggle/
! chmod 600 ~/.kaggle/kaggle.json
! kaggle datasets download alessiocorrado99/animals10
! unzip animals10.zip

Importing librairies
"""

import tensorflow as tf
import seaborn as sns
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import random
import cv2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers, Sequential
from sklearn.model_selection import train_test_split
from tensorflow.keras.applications.efficientnet_v2 import EfficientNetV2B2
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.metrics import confusion_matrix, accuracy_score

"""Accessing the files and creating a dataframe with the image id and the name of the animal associated"""

directory = '/content/raw-img'
name = []
img_id = []

for dirname, _, filenames in os.walk(directory):
    for filename in filenames:
        img_id.append(os.path.join(os.path.basename(dirname),filename))
        name.append(os.path.basename(dirname))

df = pd.DataFrame({"img_id":img_id, "name":name})
df.head()

"""Visualising the data distribution"""

classes, counts = np.unique(df["name"], return_counts=True)

plt.figure(figsize=(10,5))
plt.bar(classes,counts,color="#55B7BF")
plt.xticks(rotation=45)
plt.title("Distribution of classes in the dataset")
plt.show()

"""Generating a training and testing set."""

df_train, df_test = train_test_split(df,test_size = 0.2)
print("Shape of training set",df_train.shape)
print("Shape of testing set",df_test.shape)

"""Generating normalised and randomly augmented images from the original images, with a training and validation set."""

batch_size = 64
img_size = (224,224)

train_datagen = ImageDataGenerator(
    shear_range=0.2,
    rotation_range=180,
    zoom_range=0.2,
    horizontal_flip=True,
    vertical_flip=True,
    validation_split=0.2)

test_datagen = ImageDataGenerator()

train_generator = train_datagen.flow_from_dataframe(
    directory=directory,
    dataframe=df_train,
    x_col = "img_id",
    y_col = "name",
    shuffle = True,
    target_size=img_size,
    batch_size=batch_size,
    class_mode='categorical',
    subset="training")

val_generator = train_datagen.flow_from_dataframe(
    directory=directory,
    dataframe=df_train,
    x_col = "img_id",
    y_col = "name",
    shuffle = True,
    target_size=img_size,
    batch_size=batch_size,
    class_mode='categorical',
    subset="validation")

test_generator = test_datagen.flow_from_dataframe(
    directory=directory,
    dataframe=df_test,
    x_col = "img_id",
    y_col = "name",
    target_size=img_size,
    batch_size=batch_size,
    shuffle = False,
    class_mode="categorical")

"""Creating arrays with some of the images generated."""

num_batches = 5

images = []
labels = []

for i in range(num_batches):
    batch_data, batch_labels = train_generator.next()
    batch_data /= 255
    images.append(batch_data)

    labels.extend(np.argmax(batch_labels, axis=1))

images = np.concatenate(images, axis=0)

labels = np.array(labels)

"""Displaying some of the images present in the dataset, except for the spiders pictures."""

n_rows = 4
n_cols = 5

fig, axes = plt.subplots(n_rows, n_cols, figsize=(6, 6))

for i in range(n_rows):
    for j in range(n_cols):
        r = random.randint(0, len(labels) - 1)

        while labels[r] == 8:
            r = random.randint(0, len(labels) - 1)

        axes[i, j].imshow(images[r])
        axes[i, j].set_title(classes[labels[r]])
        axes[i, j].axis('off')

plt.tight_layout()
plt.show()

"""Creating a model using EfficientnetB3"""

img_shape = img_size + tuple([3])

efficient_net = EfficientNetV2B2(
    weights='imagenet',
    input_shape=img_shape,
    include_top=False,
    pooling='max')

model = Sequential()
model.add(efficient_net)
model.add(layers.Dense(1024,activation="relu"))
#model.add(layers.Dropout(0.5))
model.add(layers.Dense(10, activation='softmax'))
model.summary()

model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["categorical_accuracy"])
early_stopping = EarlyStopping(monitor="val_categorical_accuracy",patience=2,restore_best_weights=True)

nb_epochs = 10
history = model.fit(
    train_generator,
    steps_per_epoch = train_generator.samples // batch_size,
    validation_data = val_generator,
    validation_steps = val_generator.samples // batch_size,
    epochs = nb_epochs,
    callbacks=[early_stopping])

"""Plotting the loss and accuracy"""

loss = history.history["loss"]
val_loss = history.history["val_loss"]
cat_accuracy = history.history["categorical_accuracy"]
val_cat_accuracy = history.history["val_categorical_accuracy"]
x = np.arange(len(loss))

plt.plot(x,loss,label="loss")
plt.plot(x,val_loss,label="val loss")
plt.legend()
plt.title("Evolution of loss")
plt.show()

plt.plot(x,cat_accuracy,label="categorical accuracy")
plt.plot(x,val_cat_accuracy,label="val categorical accuracy")
plt.legend()
plt.title("Evolution of accuracy")
plt.show()

"""Evaluating the model"""

model.evaluate(test_generator)

"""Visualising the confusion matrix"""

preds_raw = model.predict(test_generator)
preds = np.argmax(preds_raw, axis=1)

cm = confusion_matrix(test_generator.classes,preds)

sns.heatmap(cm, annot=True, fmt="d", cmap="PiYG", xticklabels=classes, yticklabels=classes)

# Add labels and title
plt.xlabel('Predicted')
plt.xticks(rotation=45)
plt.ylabel('True')
plt.title('Confusion Matrix')

# Display the plot
plt.show()

"""Saving the model"""

from google.colab import drive
model.save("animals10_classification_v0")
drive.mount('/content/drive')
!cp -r "animals10_classification_v0" "/content/drive/MyDrive/"

"""Checking some random images and their predicted names."""

N = 500
images = []
names = []
for i in range(N):
    r = random.randint(0,len(df)-1)
    img = cv2.imread(directory+"/"+df["img_id"][r])
    images.append(img)
    names.append(df["name"][r])

n_rows = 4
n_cols = 5

fig, axes = plt.subplots(n_rows, n_cols, figsize=(6, 6))

for i in range(n_rows):
    for j in range(n_cols):

        r = random.randint(0, len(names) - 1)

        while names[r] == "ragno":
            r = random.randint(0, len(names) - 1)


        img = cv2.resize(images[r],(224,224))
        img = np.expand_dims(img, axis=0)
        name_pred = np.argmax(model.predict(img))



        axes[i, j].imshow(images[r]/255)
        axes[i, j].set_title(classes[name_pred])
        axes[i, j].axis('off')

plt.tight_layout()
plt.show()