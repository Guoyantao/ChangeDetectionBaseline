# FORCE CPU
#import os

#os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"  # see issue #152
#os.environ["CUDA_VISIBLE_DEVICES"] = ""

import Debugger, DataPreprocesser
import keras
from keras.layers import Input, Dense
from keras.models import Model
#from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from keras.optimizers import Adam

class Model1_SkipSiamFCN(object):
    """
    An intermediate between the code and bunch of tester models.
    """

    def __init__(self, settings, dataset):
        self.settings = settings
        self.dataset = dataset
        self.dataPreprocesser = DataPreprocesser.DataPreprocesser(settings)
        self.debugger = Debugger.Debugger(settings)

        self.model = self.create_model(None)
        self.model.summary()

        self.local_setting_batch_size = 32
        self.local_setting_epochs = 5

    def train(self):
        print("Train")

        train_L, train_R, train_V = self.dataset.train
        val_L, val_R, val_V = self.dataset.val


        # 3 channels only - rgb
        if train_L.shape[3] > 3:
            train_L = train_L[:,:,:,1:4]
            train_R = train_R[:,:,:,1:4]
            val_L = val_L[:,:,:,1:4]
            val_R = val_R[:,:,:,1:4]
        # label also reshape
        train_V = train_V.reshape(train_V.shape + (1,))
        val_V = val_V.reshape(val_V.shape + (1,))


        print("left images (train)")
        self.debugger.explore_set_stats(train_L)
        print("right images (train)")
        self.debugger.explore_set_stats(train_R)
        print("label images (train)")
        self.debugger.explore_set_stats(train_V)

        history = self.model.fit([train_L, train_R], train_V, batch_size=self.local_setting_batch_size, epochs=self.local_setting_epochs,
                                 validation_data=([val_L, val_R], val_V))

        print(history)
        history.history["accuracy"] = history.history["acc"]

        self.debugger.nice_plot_history(history, no_val=True)

    def save(self, path=""):
        if path == "":
            self.model.save_weights(self.settings.large_file_folder+"last_trained_model_weights.h5")
        else:
            self.model.save_weights(path)
        print("Saved model weights.")

    def load(self, path=""):
        if path == "":
            self.model.load_weights(self.settings.large_file_folder+"last_trained_model_weights.h5")
        else:
            self.model.load_weights(path)
        print("Loaded model weights.")

    def test(self):
        print("Test")

        test_L, test_R, test_V = self.dataset.test

        if test_L.shape[3] > 3:
            # 3 channels only - rgb
            test_L = test_L[:,:,:,1:4]
            test_R = test_R[:,:,:,1:4]
        # label also reshape
        test_V = test_V.reshape(test_V.shape + (1,))

        predicted = self.model.predict([test_L, test_R])

        print(predicted)
        print(len(predicted))

        # chop off that last dimension
        predicted = predicted.reshape(predicted.shape[:-1])
        test_V = test_V.reshape(test_V.shape[:-1])


        # undo preprocessing steps?
        predicted = self.dataPreprocesser.postprocess_labels(predicted)
        test_L = self.dataPreprocesser.postprocess_images(test_L)
        test_R = self.dataPreprocesser.postprocess_images(test_R)


        print("left images")
        self.debugger.explore_set_stats(test_L)
        print("right images")
        self.debugger.explore_set_stats(test_R)
        print("label images")
        self.debugger.explore_set_stats(test_V)
        print("predicted images")
        self.debugger.explore_set_stats(predicted)

        off = 0
        while off < len(predicted):
            #self.debugger.viewTripples(test_L, test_R, test_V, how_many=4, off=off)
            self.debugger.viewQuadrupples(test_L, test_R, test_V, predicted, how_many=4, off=off)
            off += 4

    def create_model(self, input_size = 112, channels = 3, kernel_size = (3, 3), pool_size = (2, 2), up_size = (2, 2)):
        # input_size = None
        # building blocks:

        # conv + pool
        # keras.layers.Conv2D(filters, kernel_size, strides=(1, 1), padding='valid', data_format=None, dilation_rate=(1, 1), activation=None, use_bias=True, kernel_initializer='glorot_uniform', bias_initializer='zeros', kernel_regularizer=None, bias_regularizer=None, activity_regularizer=None, kernel_constraint=None, bias_constraint=None)
        # keras.layers.MaxPooling2D(pool_size=(2, 2), strides=None, padding='valid', data_format=None)

        # deconv + upsample
        # keras.layers.Conv2DTranspose(filters, kernel_size, strides=(1, 1), padding='valid', output_padding=None, data_format=None, dilation_rate=(1, 1), activation=None, use_bias=True, kernel_initializer='glorot_uniform', bias_initializer='zeros', kernel_regularizer=None, bias_regularizer=None, activity_regularizer=None, kernel_constraint=None, bias_constraint=None)
        # keras.layers.UpSampling2D(size=(2, 2), data_format=None, interpolation='nearest')


        input = Input(shape=(input_size, input_size, channels))
        # 1st block
        x = keras.layers.Conv2D(16, kernel_size, padding="same")(input)
        skip16 = keras.layers.Conv2D(16, kernel_size, padding="same")(x)
        x = keras.layers.MaxPooling2D(pool_size)(skip16)

        # 2nd block
        x = keras.layers.Conv2D(32, kernel_size, padding="same")(x)
        skip32 = keras.layers.Conv2D(32, kernel_size, padding="same")(x)
        x = keras.layers.MaxPooling2D(pool_size)(skip32)

        # 3rd block
        x = keras.layers.Conv2D(64, kernel_size, padding="same")(x)
        x = keras.layers.Conv2D(64, kernel_size, padding="same")(x)
        skip64 = keras.layers.Conv2D(64, kernel_size, padding="same")(x)
        x = keras.layers.MaxPooling2D(pool_size)(skip64)

        # 4th block
        x = keras.layers.Conv2D(128, kernel_size, padding="same")(x)
        x = keras.layers.Conv2D(128, kernel_size, padding="same")(x)
        skip128 = keras.layers.Conv2D(128, kernel_size, padding="same")(x)
        out = keras.layers.MaxPooling2D(pool_size)(skip128)

        # siamese_model = Model(input, out)
        siamese_model_encode = Model(inputs=[input], outputs=[out, skip16, skip32, skip64, skip128])

        print("<< Siamese model >>")
        siamese_model_encode.summary()

        # Then merging
        input_a = Input(shape=(input_size, input_size, 3))
        input_b = Input(shape=(input_size, input_size, 3))

        branch_a, skip16_a, skip32_a, skip64_a, skip128_a = siamese_model_encode([input_a])
        branch_b, skip16_b, skip32_b, skip64_b, skip128_b = siamese_model_encode([input_b])

        # merge two branches
        x = keras.layers.concatenate([branch_a, branch_a])
        x = keras.layers.Conv2DTranspose(128, kernel_size, padding="same")(x)
        x = keras.layers.UpSampling2D(up_size)(x)

        # merge 128
        x = keras.layers.concatenate([x, skip128_a, skip128_b])

        x = keras.layers.Conv2DTranspose(128, kernel_size, padding="same")(x)
        x = keras.layers.Conv2DTranspose(128, kernel_size, padding="same")(x)
        x = keras.layers.Conv2DTranspose(64, kernel_size, padding="same")(x)
        x = keras.layers.UpSampling2D(up_size)(x)

        # merge 64
        x = keras.layers.concatenate([x, skip64_a, skip64_b])
        x = keras.layers.Conv2DTranspose(64, kernel_size, padding="same")(x)
        x = keras.layers.Conv2DTranspose(64, kernel_size, padding="same")(x)
        x = keras.layers.Conv2DTranspose(32, kernel_size, padding="same")(x)
        x = keras.layers.UpSampling2D(up_size)(x)

        # merge 32
        x = keras.layers.concatenate([x, skip32_a, skip32_b])
        x = keras.layers.Conv2DTranspose(32, kernel_size, padding="same")(x)
        x = keras.layers.Conv2DTranspose(16, kernel_size, padding="same")(x)
        x = keras.layers.UpSampling2D(up_size)(x)

        # merge 16
        x = keras.layers.concatenate([x, skip16_a, skip16_b])
        x = keras.layers.Conv2DTranspose(16, kernel_size, padding="same")(x)
        final_out = keras.layers.Conv2DTranspose(2, kernel_size, padding="same")(x)

        # within 0-1
        # and just 1 channel
        final_out = keras.layers.Conv2D(1, (1, 1), activation='sigmoid')(final_out)

        print("<< Full model >>")
        full_model = Model([input_a, input_b], final_out)

        #full_model.summary()

        model = full_model
        # model.compile(optimizer=Adam(lr=0.001), loss="binary_crossentropy", metrics=["accuracy"])
        # model.compile(optimizer=Adam(lr=0.0001), loss='binary_crossentropy', metrics=['accuracy'])

        model.compile(optimizer=Adam(lr=0.00001), loss='binary_crossentropy', metrics=['accuracy'])

        return model



