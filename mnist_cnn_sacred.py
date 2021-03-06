"""
https://www.hhllcks.de/blog/2018/5/4/version-your-machine-learning-models-with-sacred
import keras from tensorflow not directly from keras
"""
# imports {{{
from sacred import Experiment
from sacred.utils import apply_backspaces_and_linefeeds
from sacred.observers import MongoObserver

from tensorflow import keras
from tensorflow.keras.datasets import mnist
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.layers import Conv2D, MaxPooling2D
from tensorflow.keras import backend as K
# from tensorflow.keras.callbacks import Callback
from tensorflow.keras import callbacks
# }}}

# start mongdbservice by mongod --config /opt/homebrew/etc/mongod.conf --fork
ex = Experiment("mnist_cnn")
db_name = "sacred_db_1"
url = '127.0.0.1:27017'
ex.observers.append(MongoObserver.create(
    url=url,
    db_name=db_name)
)
# optional
ex.captured_out_filter = apply_backspaces_and_linefeeds

# decorate for sacred {{{


@ex.config
def my_config():
    batch_size = 128
    num_classes = 10
    epochs = 3


@ex.capture
def my_metrics(_run, logs):
    """
    each time an epoch ends sacred will log the metrics,
    and plot in omniboard.
    """
    _run.log_scalar("loss", float(logs.get('loss')))
    _run.log_scalar("acc", float(logs.get('accuracy')))
    _run.log_scalar("val_loss", float(logs.get('val_loss')))
    _run.log_scalar("val_acc", float(logs.get('val_accuracy')))
    _run.result = float(logs.get('val_accuracy'))


@ex.automain
def my_main(batch_size, num_classes, epochs):

    # input image dimensions
    img_rows, img_cols = 28, 28

    # the data, split between train and test sets
    (x_train, y_train), (x_test, y_test) = mnist.load_data()

    if K.image_data_format() == 'channels_first':
        x_train = x_train.reshape(x_train.shape[0], 1, img_rows, img_cols)
        x_test = x_test.reshape(x_test.shape[0], 1, img_rows, img_cols)
        input_shape = (1, img_rows, img_cols)
    else:
        x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
        x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)
        input_shape = (img_rows, img_cols, 1)

    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')
    x_train /= 255
    x_test /= 255
    print('x_train shape:', x_train.shape)
    print(x_train.shape[0], 'train samples')
    print(x_test.shape[0], 'test samples')

    # convert class vectors to binary class matrices
    y_train = keras.utils.to_categorical(y_train, num_classes)
    y_test = keras.utils.to_categorical(y_test, num_classes)

    model = Sequential()
    model.add(Conv2D(32, kernel_size=(3, 3),
                     activation='relu',
                     input_shape=input_shape))
    model.add(Conv2D(64, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))
    model.add(Flatten())
    model.add(Dense(128, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(num_classes, activation='softmax'))

    model.compile(loss=keras.losses.categorical_crossentropy,
                  optimizer=keras.optimizers.Adadelta(),
                  metrics=['accuracy'])

    # class LogMetrics(Callback):
    #     def on_epoch_end(self, _, logs={}):
    #         my_metrics(logs=logs)
    # # callback method 2
    log_callback = callbacks.LambdaCallback(
        on_epoch_end=lambda _, logs: my_metrics(logs=logs))
    model.fit(x_train, y_train,
              batch_size=batch_size,
              epochs=epochs,
              verbose=1,
              validation_data=(x_test, y_test),
              callbacks=[log_callback]  # [LogMetrics()]
              )
    score = model.evaluate(x_test, y_test, verbose=0)
    print('Test loss:', score[0])
    print('Test accuracy:', score[1])
    print("open omniboard by the following command...",
          f"omniboard -m {url}:{db_name}", end="\n", sep='\n')
# }}}
