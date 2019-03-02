"""モデルの作成."""

import csv
from argparse import ArgumentParser

import matplotlib.pyplot as plt
import numpy
from keras.layers import Dense, Dropout
from keras.layers.normalization import BatchNormalization
from keras.models import Sequential
from keras.optimizers import Adam


def main():
    """メイン関数."""
    p = ArgumentParser()
    p.add_argument('traincsv')
    p.add_argument('testcsv')
    p.add_argument('outfile')
    p.add_argument('-e', '--epochs', type=int, default=100)
    args = p.parse_args()

    def read_data(filename):
        x = []
        y = []

        with open(filename, 'r') as f:
            for r in csv.reader(f):
                x.append([float(e) for e in r[1:-16]])
                y.append([float(e) for e in r[-16:]])

        return numpy.array(x), numpy.array(y)

    X_train, Y_train = read_data(args.traincsv)
    X_test, Y_test = read_data(args.testcsv)

    model = Sequential()
    model.add(Dense(1600, activation='relu', input_dim=1600))
    model.add(Dropout(0.8))
    model.add(BatchNormalization())
    model.add(Dense(128, activation='relu'))
    model.add(Dropout(0.5))
    model.add(BatchNormalization())
    model.add(Dense(16, activation='softmax'))

    model.summary()

    adam = Adam()
    model.compile(loss='categorical_crossentropy',
                  optimizer=adam,
                  metrics=['accuracy'])

    history = model.fit(X_train, Y_train, epochs=args.epochs,
                        batch_size=50, validation_data=(X_test, Y_test)
                        )

    _plot_history(history)

    loss, accuracy = model.evaluate(X_test, Y_test, verbose=1)
    print("Accuracy = {:.2f}".format(accuracy))
    print("Loss = {:.2f}".format(loss))

    model.save(args.outfile, include_optimizer=False)


def _plot_history(history):

    # 精度の履歴をプロット
    plt.plot(history.history['acc'])
    plt.plot(history.history['val_acc'])
    plt.title('model accuracy')
    plt.xlabel('epoch')
    plt.ylabel('accuracy')
    plt.legend(['acc', 'val_acc'], loc='lower right')
    plt.show()

    # 損失の履歴をプロット
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model loss')
    plt.xlabel('epoch')
    plt.ylabel('loss')
    plt.legend(['loss', 'val_loss'], loc='lower right')
    plt.show()


if __name__ == "__main__":
    main()
