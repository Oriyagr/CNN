# -*- coding: utf-8 -*-
"""finalCnn_q1.py

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1XV17LcL6nQCLN64NDdDFk4J-xQUvCdNS
"""

import tensorflow as tf
from tensorflow.keras import datasets, layers, models, preprocessing, optimizers, regularizers
import matplotlib.pyplot as plt
from google.colab import drive
import numpy as np


# Mount Google Drive
drive.mount('/content/drive')
def modelBuild(trynum=1, img_size = 64, batch_sz = 16, num_epochs = 30, steps_per_ep = 230,
               validation_steps = 41, learning_rate=0.0001, train_path = "/content/drive/MyDrive/train1/", img_gen=None,
               model_layers=None, optimizer=None):

    if img_size is None:
        img_size = 64
    if batch_sz is None:
        batch_sz = 16
    if num_epochs is None:
        num_epochs = 30
    if steps_per_ep is None:#Training Set/Batch Size
        steps_per_ep = 230
    if validation_steps is None:#Testing Set/Batch Size
        validation_steps = 41
    if learning_rate is None:
        learning_rate = 0.0001
    if train_path is None:
        train_path = "/content/drive/MyDrive/train1/"

    print(f"try number: {trynum}")
    test_path = "/content/drive/MyDrive/test1/"
    class_names = ['daisy', 'dandelion', 'rose', 'sunflower', 'tulip']
    target_dims = (img_size, img_size)

    if img_gen is None:
        img_gen = preprocessing.image.ImageDataGenerator(
            rescale=1./255,
            shear_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True,
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2
        )

    train_gen = img_gen.flow_from_directory(
        train_path,
        target_size=target_dims,
        batch_size=batch_sz,
        classes=class_names,
        class_mode='categorical',
        shuffle=True
    )

    test_gen = img_gen.flow_from_directory(
        test_path,
        target_size=target_dims,
        batch_size=batch_sz,
        classes=class_names,
        class_mode='categorical',
        shuffle=False
    )

    def data_generator(generator):
        while True:
            x, y = generator.__next__()
            yield x, y

    train_dataset = data_generator(train_gen)
    test_dataset = data_generator(test_gen)

    if model_layers is None:
        model_layers = [
            layers.Conv2D(64, (3, 3), activation='relu', input_shape=(img_size, img_size, 3), kernel_regularizer=regularizers.l2(0.001)),
            layers.BatchNormalization(),
            layers.MaxPooling2D(pool_size=(2, 2), strides=2),

            layers.Conv2D(128, (3, 3), activation='relu', kernel_regularizer=regularizers.l2(0.001)),
            layers.BatchNormalization(),
            layers.MaxPooling2D(pool_size=(2, 2), strides=2),

            layers.Conv2D(256, (3, 3), activation='relu', kernel_regularizer=regularizers.l2(0.001)),
            layers.BatchNormalization(),
            layers.MaxPooling2D(pool_size=(2, 2), strides=2),

            layers.GlobalAveragePooling2D(),  #n for reducing overfitting

            layers.Dense(128, activation='relu', kernel_regularizer=regularizers.l2(0.001)),
            layers.Dropout(0.55),
            layers.Dense(5, activation='softmax', kernel_regularizer=regularizers.l2(0.001))
        ]

    model = models.Sequential(model_layers)
    model.summary()

    if optimizer is None:
        optimizer = optimizers.Adam(learning_rate=learning_rate)

    model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])

    batch_sample = next(train_dataset)
    x_sample, y_sample = batch_sample
    initial_preds = model.predict(x_sample)
    initial_loss = tf.keras.losses.categorical_crossentropy(y_sample, initial_preds).numpy().mean()
    regularization_loss = tf.reduce_sum(model.losses).numpy()

    print("Sanity checks")
    total_initial_loss = initial_loss + regularization_loss
    print(f"Initial Loss: {initial_loss}")
    print(f"Loss+Regularization: {total_initial_loss}")

    return model, train_dataset, test_dataset, test_gen, steps_per_ep, num_epochs, validation_steps

from sklearn.metrics import confusion_matrix
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf

def trainModel(model, train_dataset, test_dataset, steps_per_ep, num_epochs, validation_steps, test_gen):
    print("Starting training...")
    history = model.fit(
        train_dataset,
        steps_per_epoch=steps_per_ep,
        epochs=num_epochs,
        validation_data=test_dataset,
        validation_steps=validation_steps
    )
    print("Training complete.")

    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history.history['accuracy'], label='accuracy')
    plt.plot(history.history['val_accuracy'], label='val_accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend(loc='lower right')

    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'], label='loss')
    plt.plot(history.history['val_loss'], label='val_loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend(loc='lower right')

    plt.show()

    # Confusion Matrix
    print("Generating confusion matrix...")


    test_steps_per_epoch = np.math.ceil(test_gen.samples / test_gen.batch_size)
    predictions = model.predict(test_gen, steps=test_steps_per_epoch)


    predicted_classes = np.argmax(predictions, axis=1)

    # Get the true class indices
    true_classes = test_gen.classes

    # Generate the confusion matrix
    confusion_mtx = confusion_matrix(true_classes, predicted_classes)

    # Plot the confusion matrix
    plt.figure(figsize=(10, 8))
    sns.heatmap(confusion_mtx, annot=True, fmt='g', cmap='Blues',
                xticklabels=list(test_gen.class_indices.keys()),
                yticklabels=list(test_gen.class_indices.keys()))
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.show()

def evaluate_model(model, test_gen, class_names, validation_steps):
    test_gen.reset()
    errors = {class_name: None for class_name in class_names}
    corrects = {class_name: None for class_name in class_names}


    for i in range(validation_steps):
        x_batch, y_batch = next(test_gen)
        predictions = model.predict(x_batch)
        predicted_classes = np.argmax(predictions, axis=1)
        true_classes = np.argmax(y_batch, axis=1)

        for j in range(len(predicted_classes)):
            file_idx = i * 16 + j  # 16 is the batch size
            if file_idx >= len(test_gen.filenames):
                break

            true_class = class_names[true_classes[j]]
            predicted_class = class_names[predicted_classes[j]]

            # Check if both correct and incorrect examples have been found for this class
            if corrects[true_class] is None or errors[true_class] is None:
                if predicted_classes[j] == true_classes[j] and corrects[true_class] is None:
                    corrects[true_class] = (x_batch[j], predicted_classes[j], true_classes[j], test_gen.filenames[file_idx])
                elif predicted_classes[j] != true_classes[j] and errors[true_class] is None:
                    errors[true_class] = (x_batch[j], predicted_classes[j], true_classes[j], test_gen.filenames[file_idx])

        # Stop if we found both correct and incorrect for all classes
        if all(corrects.values()) and all(errors.values()):
            break

    return errors, corrects

model, train_dataset, test_dataset, test_gen, steps_per_ep, num_epochs, validation_steps = modelBuild(1)
trainModel(model, train_dataset, test_dataset, steps_per_ep, num_epochs, validation_steps, test_gen)

class_names = ['daisy', 'dandelion', 'rose', 'sunflower', 'tulip']
errors, corrects = evaluate_model(model, test_gen, class_names, validation_steps)

# show true prediction for each class
for class_name in class_names:
    if corrects[class_name] is not None:
        correct_img, correct_pred_class, correct_true_class, correct_file_name = corrects[class_name]
        plt.imshow(correct_img)
        plt.title(f"Correctly Predicted: {class_names[correct_pred_class]}, True: {class_names[correct_true_class]}, File: {correct_file_name}")
        plt.show()

#show false prediction for each class
for class_name in class_names:
    if errors[class_name] is not None:
        incorrect_img, incorrect_pred_class, incorrect_true_class, incorrect_file_name = errors[class_name]
        plt.imshow(incorrect_img)
        plt.title(f"Incorrectly Predicted: {class_names[incorrect_pred_class]}, True: {class_names[incorrect_true_class]}, File: {incorrect_file_name}")
        plt.show()

#overfit Overfit over few images
model, train_dataset, test_dataset, test_gen, steps_per_ep, num_epochs, validation_steps = modelBuild(2, None,None,None,None,3,None,"/content/drive/MyDrive/small_train1/",None,None,None)
trainModel(model, train_dataset, test_dataset, steps_per_ep, num_epochs, validation_steps, test_gen)

#Increasing the learning rate 10 times
model, train_dataset, test_dataset, test_gen, steps_per_ep, num_epochs, validation_steps = modelBuild(trynum=1, img_size = 64, batch_sz = 16, num_epochs = 30, steps_per_ep = 230,
               validation_steps = 41, learning_rate=0.001, train_path = "/content/drive/MyDrive/train1/", img_gen=None,
               model_layers=None, optimizer=None)
trainModel(model, train_dataset, test_dataset, steps_per_ep, num_epochs, validation_steps, test_gen)

#Increasing the batch size to 32 which affects steps_per_ep and validation_steps
model, train_dataset, test_dataset, test_gen, steps_per_ep, num_epochs, validation_steps = modelBuild(trynum=1, img_size = 64, batch_sz = 32, num_epochs = 30, steps_per_ep = 115,
               validation_steps = 20, learning_rate=0.0001, train_path = "/content/drive/MyDrive/train1/", img_gen=None,
               model_layers=None, optimizer=None)
trainModel(model, train_dataset, test_dataset, steps_per_ep, num_epochs, validation_steps, test_gen)

#reducing the batch size to 8 which affects steps_per_ep and validation_steps
model, train_dataset, test_dataset, test_gen, steps_per_ep, num_epochs, validation_steps = modelBuild(trynum=1, img_size = 64, batch_sz = 8, num_epochs = 30, steps_per_ep = 458,
               validation_steps = 81, learning_rate=0.0001, train_path = "/content/drive/MyDrive/train1/", img_gen=None,
               model_layers=None, optimizer=None)
trainModel(model, train_dataset, test_dataset, steps_per_ep, num_epochs, validation_steps, test_gen)

#Nadam optimizer
model, train_dataset, test_dataset, test_gen, steps_per_ep, num_epochs, validation_steps = modelBuild(trynum=1, img_size = 64, batch_sz = 16, num_epochs = 30, steps_per_ep = 230,
               validation_steps = 41, learning_rate=0.0001, train_path = "/content/drive/MyDrive/train1/", img_gen=None,
               model_layers=None, optimizer=optimizers.Adam(learning_rate=0.0001))
trainModel(model, train_dataset, test_dataset, steps_per_ep, num_epochs, validation_steps, test_gen)

# no augmentation
img_gen1= preprocessing.image.ImageDataGenerator(
            rescale=1./255
        )
model, train_dataset, test_dataset, test_gen, steps_per_ep, num_epochs, validation_steps = modelBuild(trynum=1, img_size = 64, batch_sz = 16, num_epochs = 30, steps_per_ep = 230,
               validation_steps = 41, learning_rate=0.0001, train_path = "/content/drive/MyDrive/train1/", img_gen=img_gen1,
               model_layers=None, optimizer=None)
trainModel(model, train_dataset, test_dataset, steps_per_ep, num_epochs, validation_steps, test_gen)

#Fewer convolutional layers
model_layers1 = [
            layers.Conv2D(64, (3, 3), activation='relu', input_shape=(64, 64, 3), kernel_regularizer=regularizers.l2(0.0001)),
            layers.BatchNormalization(),
            layers.MaxPooling2D(pool_size=(2, 2), strides=2),

            layers.Conv2D(256, (3, 3), activation='relu', kernel_regularizer=regularizers.l2(0.0001)),
            layers.BatchNormalization(),
            layers.MaxPooling2D(pool_size=(2, 2), strides=2),

            layers.GlobalAveragePooling2D(),  # Better than Flatten for reducing overfitting

            layers.Dense(128, activation='relu', kernel_regularizer=regularizers.l2(0.0001)),
            layers.Dropout(0.3),
            layers.Dense(5, activation='softmax', kernel_regularizer=regularizers.l2(0.0001))
        ]
model, train_dataset, test_dataset, test_gen, steps_per_ep, num_epochs, validation_steps = modelBuild(trynum=1, img_size = 64, batch_sz = 16, num_epochs = 30, steps_per_ep = 230,
               validation_steps = 41, learning_rate=0.0001, train_path = "/content/drive/MyDrive/train1/", img_gen=img_gen1,
               model_layers=model_layers1, optimizer=None)
trainModel(model, train_dataset, test_dataset, steps_per_ep, num_epochs, validation_steps, test_gen)

#Increasing the image size to 128
model, train_dataset, test_dataset, test_gen, steps_per_ep, num_epochs, validation_steps = modelBuild(trynum=1, img_size = 128, batch_sz = 16, num_epochs = 30, steps_per_ep = 230,
               validation_steps = 41, learning_rate=0.0001, train_path = "/content/drive/MyDrive/train1/", img_gen=None,
               model_layers=None, optimizer=None)
trainModel(model, train_dataset, test_dataset, steps_per_ep, num_epochs, validation_steps, test_gen)

#Increasing epoch number to 40
model, train_dataset, test_dataset, test_gen, steps_per_ep, num_epochs, validation_steps = modelBuild(trynum=1, img_size = 64, batch_sz = 16, num_epochs = 40, steps_per_ep = 230,
               validation_steps = 41, learning_rate=0.0001, train_path = "/content/drive/MyDrive/train1/", img_gen=None,
               model_layers=None, optimizer=None)
trainModel(model, train_dataset, test_dataset, steps_per_ep, num_epochs, validation_steps, test_gen)