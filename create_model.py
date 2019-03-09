"""モデルの作成."""

from argparse import ArgumentParser

import matplotlib.pyplot as plt
from keras.layers import Dense, Dropout
from keras.layers.normalization import BatchNormalization
from keras.models import Sequential
from keras.optimizers import Adam

from utility import read_data


def main():
    """メイン関数."""
    parser = ArgumentParser()
    parser.add_argument('traincsv')
    parser.add_argument('testcsv')
    parser.add_argument('outfile')
    parser.add_argument('-e', '--epochs', type=int, default=100)
    args = parser.parse_args()

    x_train, y_train, _ = read_data(args.traincsv)
    x_test, y_test, _ = read_data(args.testcsv)

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

    history = model.fit(x_train, y_train, epochs=args.epochs,
                        batch_size=50, validation_data=(x_test, y_test)
                        )

    _plot_history(history)

    loss, accuracy = model.evaluate(x_test, y_test, verbose=1)
    print("Accuracy = {:.2f}".format(accuracy))
    print("Loss = {:.2f}".format(loss))

    model.save(args.outfile)


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
