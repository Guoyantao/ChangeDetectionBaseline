import Debugger

import os
from os import listdir
from os.path import isfile, join
import re
import pickle
import numpy as np
from skimage import io
from tqdm import tqdm
import h5py


class DatasetInstance_ONERA(object):
    """
    Contains specific setting for one dataset instance.

    Has/Can do these:
    - Has paths, file names
    - data specific edits (when one dataset goes from [1 to 2] with it labels without explanations)
    - can have several variants (setting options)
    - specific paths to saved files
    - print to present itself
    """


    def __init__(self, settings, dataLoader):
        self.settings = settings
        self.dataLoader = dataLoader
        self.variant = 0

        self.save_path_ = "ONERA_preloadedImgs_sub"

    def get_paths(self):
        lefts_paths = []
        rights_paths = []
        labels_paths = []
        return lefts_paths, rights_paths, labels_paths

    #def datasetSpecificEdit_rasters(self,data):
    #    return data
    #def datasetSpecificEdit_vectors(self,data):
    #
    #    # labels are in 1 to 2 spread -> send them back to 0-1
    #    data = (data - 1.0)
    #
    #    return data

    def present_thyself(self):
        print("ONERA Satellite Change Detection dataset.")


    # Dataset specific:

    ### Alternative dataset, the "Onera Satellite Change Detection dataset"
    def load_dataset(self):
        lefts = []
        rights = []
        labels = []

        # Mess

        images_path = "/scratch/ruzicka/dataset_initial_view/02_11_OSCD_dataset/63_dataset/Onera Satellite Change Detection dataset - Images/"
        labels_path = "/scratch/ruzicka/dataset_initial_view/02_11_OSCD_dataset/63_training/Onera Satellite Change Detection dataset - Train Labels/"
        train = "aguasclaras,bercy,bordeaux,nantes,paris,rennes,saclay_e,abudhabi,cupertino,pisa,beihai,hongkong,beirut,mumbai"
        test = "brasilia,montpellier,norcia,rio,saclay_w,valencia,dubai,lasvegas,milano,chongqing"

        # for each in train:
        # image: /<name>/pair/img1.png x img2.png
        # label: /<name>/cm/cm.png

        trains = train.split(",")
        tests = test.split(",")

        train_x_left_paths = []
        train_x_right_paths = []
        train_y_label_paths = []

        for train in trains:
            path = images_path + train + "/pair/"
            train_x_left_paths.append(path + "img1.png")
            train_x_right_paths.append(path + "img2.png")
            # train_y_label_paths.append(labels_path + train + "/cm/cm.png")
            train_y_label_paths.append(labels_path + train + "/cm/" + train + "-cm.tif")
        # tile_paths_old = [f for f in listdir(path_old) if isfile(join(path_old, f))]

        test_x_left_paths = []
        test_x_right_paths = []

        for test in tests:
            path = images_path + test + "/pair/"
            test_x_left_paths.append(path + "img1.png")
            test_x_right_paths.append(path + "img2.png")

        print(len(train_x_left_paths), train_x_left_paths)
        print(len(train_x_right_paths), train_x_right_paths)
        print(len(train_y_label_paths), train_y_label_paths)

        # load as images and possibly also crop!
        # tile it into 112x112 tiles?
        from PIL import Image

        def tile_from_image(img, desired_size):
            repetitions = int(np.floor(min(img.size[0] / desired_size, img.size[1] / desired_size)))

            min_size = min(img.size[0], img.size[1])
            # print(desired_size, "fits", repetitions, "times into", min_size, "(", desired_size*repetitions, ")")

            width, height = img.size
            left = np.ceil((width - min_size) / 2.)
            top = np.ceil((height - min_size) / 2.)
            right = width - np.floor((width - min_size) / 2)
            bottom = height - np.floor((height - min_size) / 2)

            cropped_im = img.crop((left, top, right, bottom))

            # print(cropped_im.size)

            resize_to = desired_size * repetitions

            resized_im = cropped_im.resize((resize_to, resize_to))
            # print(resized_im.size)

            # resized_im.show()
            tiles = []
            # now crop it into repetitions*repetitions times!
            for x_off_i in range(repetitions):
                for y_off_i in range(repetitions):
                    left = x_off_i * desired_size
                    top = y_off_i * desired_size
                    right = left + desired_size
                    bottom = top + desired_size

                    box = (left, top, right, bottom)
                    # print(box)
                    segment = resized_im.crop(box)
                    # print(segment.size)
                    # segment.show()
                    tiles.append(segment)
            return tiles, resized_im

        desired_size = 112
        train_X_left = []
        train_X_right = []
        train_Y = []

        for i in range(len(train_x_left_paths)):
            # for i in range(1):
            train_left_img = Image.open(train_x_left_paths[i])
            train_right_img = Image.open(train_x_right_paths[i])
            train_label_img = Image.open(train_y_label_paths[i])

            train_label_img = train_label_img.convert('L')

            left_images, _ = tile_from_image(train_left_img, desired_size)
            right_images, _ = tile_from_image(train_right_img, desired_size)
            label_images, _ = tile_from_image(train_label_img, desired_size)

            # label_rebuilt = rebuild_image_from_tiles(label_images)

            # label_rebuilt.show()

            train_X_left += left_images
            train_X_right += right_images
            train_Y += label_images

        print("loaded", len(train_X_left), len(train_X_right), len(train_Y), "train images")

        train_X_left = [np.asarray(i) for i in train_X_left]
        train_X_right = [np.asarray(i) for i in train_X_right]
        train_Y = [np.asarray(i) for i in train_Y]

        train_X_left = np.asarray(train_X_left)
        train_X_right = np.asarray(train_X_right)
        train_Y = np.asarray(train_Y)

        def explore_set_stats(arr_set):
            amin = np.amin(arr_set.flatten())
            amax = np.amax(arr_set.flatten())
            print("min", amin, "max", amax, " ... avg", np.mean(arr_set.flatten()), "+-", np.std(arr_set.flatten()))

        #train_X_left = train_X_left / 255.0
        #train_X_right = train_X_right / 255.0
        # labels are in 1 to 2 spread -> send them to 0-1
        train_Y = (train_Y - 1.0)

        print("left images")
        explore_set_stats(train_X_left)
        print("right images")
        explore_set_stats(train_X_right)
        print("label images")
        explore_set_stats(train_Y)

        print(train_X_left[0].shape)
        print("shapes")
        print(train_Y[0].shape)
        print(train_Y.shape)

        #train_Y = train_Y.reshape(train_Y.shape + (1,)) # happens later
        # train_Y = train_Y.reshape((383, 112, 112, 1))

        print(train_Y[0].shape)

        ############### VIZ 1 ###################################################
        if False:
            fig = plt.figure(figsize=(8, 8))
            columns = 3  # needs to be multiple of 3
            rows = 3
            # off = random.randint(1,1001)
            for i in range(1, columns * rows + 1, 3):
                # idx = i * 20 + off
                idx = i * 2 + random.randint(1, 100)

                # img_old = mpimg.imread(path_old + tile_paths_old[idx])
                img_old = train_X_left[idx]
                fig.add_subplot(rows, columns, i)
                plt.imshow(img_old)
                fig.gca().set_axis_off()

                # img_new = mpimg.imread(path_new + tile_paths_new[idx])
                img_new = train_X_right[idx]
                fig.add_subplot(rows, columns, i + 1)
                plt.imshow(img_new)
                fig.gca().set_axis_off()

                img_lab = train_Y[idx]
                fig.add_subplot(rows, columns, i + 2)
                plt.imshow(img_lab[:, :, 0])
                fig.gca().set_axis_off()

            plt.subplots_adjust(wspace=0.1, hspace=0.1)
            fig.suptitle("Showing the same space in two points in time")

            fig.text(0.5, 0.04, 'Showing pairs: left, right', ha='center')

            plt.show()
        # =============================================================================

        lefts = train_X_left
        rights = train_X_right
        labels = train_Y

        data = [lefts, rights, labels]
        paths = [train_x_left_paths, train_x_right_paths, train_y_label_paths]
        return data, paths
