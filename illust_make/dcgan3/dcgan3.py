
from keras.layers import Input, Dense, Reshape, Flatten, Dropout
from keras.layers import BatchNormalization, Activation, ZeroPadding2D
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.convolutional import UpSampling2D, Conv2D, Conv2DTranspose
from keras.models import Sequential, Model
from keras.optimizers import Adam
from keras.utils import np_utils
import tensorflow as tf
from keras.backend import tensorflow_backend

import matplotlib.pyplot as plt
import os
import cv2
import numpy as np

from tqdm import tqdm

np.random.seed(0)
np.random.RandomState(0)
tf.set_random_seed(0)

config = tf.ConfigProto(gpu_options=tf.GPUOptions(allow_growth=True))
session = tf.Session(config=config)
tensorflow_backend.set_session(session)

root_dir = "/home/dmitri/PycharmProjects/GAN/illust_make/resized/"


class DCGAN():
    def __init__(self):

        self.class_names = os.listdir(root_dir)

        # self.shape = (256, 256, 4)
        self.shape = (128,128,4)
        self.z_dim = 100

        optimizer = Adam(lr=0.00001, beta_1=0.1)
        # d_opt = Adam(lr=0.00001, beta_1=0.1)

        self.discriminator = self.build_discriminator()
        self.discriminator.compile(loss='binary_crossentropy', optimizer=optimizer, metrics=['accuracy'])

        self.generator = self.build_generator()
        # self.generator.compile(loss='binary_crossentropy', optimizer=optimizer)

        z = Input(shape=(self.z_dim,))
        img = self.generator(z)

        self.discriminator.trainable = False

        valid = self.discriminator(img)

        self.combined = Model(z, valid)
        self.combined.compile(loss='binary_crossentropy', optimizer=optimizer)

    def build_generator(self):
        noise_shape = (self.z_dim,)

        model = Sequential()
        # 128*128

        model.add(Dense(256 * 8 * 8, activation="relu", input_shape=noise_shape))
        model.add(Reshape((8, 8, 256)))
        model.add(BatchNormalization(momentum=0.8))
        # model.add(UpSampling2D())
        # model.add(Conv2D(512, kernel_size=3, padding="same"))
        model.add(Conv2DTranspose(512, kernel_size=4, strides=(2, 2), padding="same"))
        model.add(Activation("relu"))
        model.add(BatchNormalization(momentum=0.8))
        # model.add(UpSampling2D())
        # model.add(Conv2D(256, kernel_size=3, padding="same"))
        model.add(Conv2DTranspose(256, kernel_size=4, strides=(2, 2), padding="same"))
        model.add(Activation("relu"))
        model.add(BatchNormalization(momentum=0.8))
        # model.add(UpSampling2D())
        # model.add(Conv2D(128, kernel_size=3, padding="same"))
        model.add(Conv2DTranspose(128, kernel_size=4, strides=(2, 2), padding="same"))
        model.add(Activation("relu"))
        model.add(BatchNormalization(momentum=0.8))
        # model.add(UpSampling2D())
        # model.add(Conv2D(64, kernel_size=3, padding="same"))
        model.add(Conv2DTranspose(64, kernel_size=4, strides=(2, 2), padding="same"))
        model.add(Activation("relu"))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Conv2D(4, kernel_size=3, padding="same"))
        model.add(Activation("tanh"))

        # 256*256
        """
        model.add(Dense(256 * 32 * 32, activation="relu", input_shape=noise_shape))
        model.add(Reshape((32, 32, 256)))
        model.add(BatchNormalization(momentum=0.8))
        # model.add(UpSampling2D())
        # model.add(Conv2D(256, kernel_size=3, padding="same"))
        model.add(Conv2DTranspose(256,kernel_size=4, strides=(2, 2) ,padding="same"))
        model.add(Activation("relu"))
        model.add(BatchNormalization(momentum=0.8))
        # model.add(UpSampling2D())
        # model.add(Conv2D(128, kernel_size=3, padding="same"))
        model.add(Conv2DTranspose(128,kernel_size=4, strides=(2, 2) ,padding="same"))
        model.add(Activation("relu"))
        model.add(BatchNormalization(momentum=0.8))
        # model.add(UpSampling2D())
        # model.add(Conv2D(64, kernel_size=3, padding="same"))
        model.add(Conv2DTranspose(64, kernel_size=4, strides=(2,2),padding="same"))
        model.add(Activation("relu"))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Conv2D(4, kernel_size=3, padding="same"))
        model.add(Activation("tanh"))
        """

        # model.summary()

        noise = Input(shape=noise_shape)
        img = model(noise)

        return Model(noise, img)

    def build_discriminator(self):
        img_shape = self.shape

        model = Sequential()

        model.add(Conv2D(32, kernel_size=3, strides=2, input_shape=img_shape, padding="same"))
        model.add(LeakyReLU(alpha=0.2))
        # model.add(Dropout(0.25))
        model.add(Conv2D(64, kernel_size=3, strides=2, padding="same"))
        model.add(ZeroPadding2D(padding=((0, 1), (0, 1))))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dropout(0.25))
        # model.add(BatchNormalization(momentum=0.8))
        """
        model.add(Conv2D(128, kernel_size=3, strides=2, padding="same"))
        model.add(LeakyReLU(alpha=0.2))
        """
        # model.add(Dropout(0.25))
        # model.add(BatchNormalization(momentum=0.8))
        model.add(Conv2D(256, kernel_size=3, strides=1, padding="same"))
        model.add(LeakyReLU(alpha=0.2))
        # model.add(Dropout(0.25))

        model.add(Flatten())
        model.add(Dense(1, activation='sigmoid'))

        # model.summary()

        img = Input(shape=img_shape)
        validity = model(img)

        return Model(img, validity)

    def build_combined(self):
        self.discriminator.trainable = False
        model = Sequential([self.generator, self.discriminator])

        return model

    def train(self, iterations, batch_size=128, save_interval=50, model_interval=1000, check_noise=None, r=5, c=5):

        X_img_path, labels = self.load_imgs()

        half_batch = int(batch_size / 2)

        # print(X_train.size)

        for iteration in tqdm(range(iterations)):

            # ------------------
            # Training Discriminator
            # -----------------
            idx = np.random.randint(0, len(X_img_path), half_batch)

            img_paths = [X_img_path[i] for i in idx]

            images = []
            for img_path in img_paths:
                img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
                # print(img_path,img.shape)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
                images.append(img)
            X_train = np.array(images)


            imgs = (X_train.astype(np.float32) - 127.5) / 127.5

            noise = np.random.uniform(-1, 1, (half_batch, self.z_dim))

            gen_imgs = self.generator.predict(noise)

            d_loss_real = self.discriminator.train_on_batch(imgs, np.ones((half_batch, 1)))
            d_loss_fake = self.discriminator.train_on_batch(gen_imgs, np.zeros((half_batch, 1)))

            d_loss = 0.5 * np.add(d_loss_real, d_loss_fake)

            # -----------------
            # Training Generator
            # -----------------

            noise = np.random.uniform(-1, 1, (batch_size, self.z_dim))

            g_loss = self.combined.train_on_batch(noise, np.ones((batch_size, 1)))

            print("[D loss: %f, acc.: %.2f%%] [G loss: %f]" % (d_loss[0], 100 * d_loss[1], g_loss))

            if iteration % save_interval == 0:
                self.save_imgs(iteration, check_noise, r, c)
                start = np.expand_dims(check_noise[0], axis=0)
                end = np.expand_dims(check_noise[1], axis=0)
                resultImage = self.visualizeInterpolation(start=start, end=end)
                cv2.imwrite("images/latent/" + "latent_{}.png".format(iteration), resultImage)
                if iteration % model_interval == 0:
                    self.generator.save("ganmodels/dcgan-{}-iter.h5".format(iteration))

    def save_imgs(self, iteration, check_noise, r, c):
        noise = check_noise
        # print(noise)
        gen_imgs = self.generator.predict(noise)

        # 0-1 rescale
        gen_imgs = 0.5 * gen_imgs + 0.5

        fig, axs = plt.subplots(r, c)
        cnt = 0
        for i in range(r):
            for j in range(c):
                axs[i, j].imshow(gen_imgs[cnt, :, :, :])
                axs[i, j].axis('off')
                cnt += 1
        fig.savefig('gen_imgs/_%d.png' % iteration)

        plt.close()


    def load_imgs(self):

        img_paths = []
        labels = []
        images = []
        for cl_name in self.class_names:
            img_names = os.listdir(os.path.join(root_dir, cl_name))
            # print(img_names)
            for img_name in img_names:
                img_paths.append(os.path.abspath(os.path.join(root_dir, cl_name, img_name)))
                hot_cl_name = self.get_class_one_hot(cl_name)
                labels.append(hot_cl_name)

        return (img_paths, np.array(labels))


    def get_class_one_hot(self, class_str):
        label_encoded = self.class_names.index(class_str)

        label_hot = np_utils.to_categorical(label_encoded, len(self.class_names))
        label_hot = label_hot

        return label_hot

    def visualizeInterpolation(self, start, end, save=True, nbSteps=10):
        print("Generating interpolations...")

        steps = nbSteps
        latentStart = start
        latentEnd = end

        startImg = self.generator.predict(latentStart)
        endImg = self.generator.predict(latentEnd)

        vectors = []

        alphaValues = np.linspace(0, 1, steps)
        for alpha in alphaValues:
            vector = latentStart * (1 - alpha) + latentEnd * alpha
            vectors.append(vector)

        vectors = np.array(vectors)

        resultLatent = None
        resultImage = None

        for i, vec in enumerate(vectors):
            gen_img = np.squeeze(self.generator.predict(vec), axis=0)
            gen_img = (0.5 * gen_img + 0.5) * 255
            interpolatedImage = cv2.cvtColor(gen_img, cv2.COLOR_RGBA2BGRA)
            interpolatedImage = interpolatedImage.astype(np.uint8)
            resultImage = interpolatedImage if resultImage is None else np.hstack([resultImage, interpolatedImage])

        return resultImage



dcgan = DCGAN()
r, c = 5, 5
check_noise = np.random.uniform(-1, 1, (r * c, 100))
dcgan.train(iterations=200000, batch_size=64, save_interval=1000, model_interval=5000,
            check_noise=check_noise, r=r, c=c)
