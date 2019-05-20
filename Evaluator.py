from builtins import print

import Debugger
import matplotlib.pyplot as plt
import numpy as np
import sklearn.metrics

class Evaluator(object):
    """
    Class to hold everything related to evaluation of the model's performance.
    """

    def __init__(self, settings):
        self.settings = settings
        self.debugger = Debugger.Debugger(settings)

    def histogram_of_predictions(self, predictions):
        print("We have", len(predictions), "predictions, each is a", predictions[0].shape, "image.")

        flat_predictions = predictions.flatten() # (works for 2D, nD and simple 1D class labels)

        fig = plt.figure()
        bins = 33
        values_of_bins, bins, patches = plt.hist(flat_predictions, bins, facecolor='g', alpha=0.75)
        #plt.yscale('log', nonposy='clip')

        plt.title('Histogram of raw predicted values from the model\n(how much are they around 0.5 vs at the edges)')
        plt.xlabel('Pixel values (0 and 1 being the class categories)')
        plt.ylabel('Number of pixels')

        plt.show()

        #fig = plt.figure()
        #sorted_predictions = sorted(flat_predictions)
        #plt.plot(sorted_predictions)
        #plt.show()

    def try_all_thresholds(self, predicted, labels, range_values = [0.0, 0.5, 1.0], title_txt="", show=True, save=False, name=""):
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 3)) # w, h

        xs = []
        ys_recalls = []
        ys_precisions = []
        ys_accuracies = []
        ys_f1s= []
        for thr in range_values: #np.arange(0.0,1.0,0.01):
            xs.append(thr)
            print("threshold=",thr)
            #_, recall, precision, accuracy = self.calculate_metrics(predicted, labels, threshold=thr)
            if "NoChange" in title_txt:
                print("from the position of NoChange class instead...")
                recall, precision, accuracy, f1 = self.calculate_recall_precision_accuracy_NOCHANGECLASS(predicted, labels, threshold=thr, need_f1=True)
            else:
                recall, precision, accuracy, f1 = self.calculate_recall_precision_accuracy(predicted, labels, threshold=thr, need_f1=True)

            ys_recalls.append(recall)
            ys_precisions.append(precision)
            ys_accuracies.append(accuracy)
            ys_f1s.append(f1)

        print("xs", len(xs), xs)
        print("ys_recalls", len(ys_recalls), ys_recalls)
        print("ys_precisions", len(ys_precisions), ys_precisions)
        print("ys_accuracies", len(ys_accuracies), ys_accuracies)
        print("ys_f1s", len(ys_f1s), ys_f1s)

        if title_txt == "":
            plt.title('Changing the threshold values')
        else:
            plt.title(title_txt)
        plt.xlabel('threshold value')
        plt.ylabel('metrics')

        plt.plot(xs, ys_recalls, color='red', marker='o', label="Recall")
        plt.plot(xs, ys_precisions, color='blue', marker='o', label="Precision")
        plt.plot(xs, ys_accuracies, color='green', marker='o', label="Accuracy")
        plt.plot(xs, ys_f1s, color='orange', marker='o', label="f1")

        plt.legend()

        plt.ylim(0.0, 1.0)

        if save:
           from matplotlib import pyplot as plt
           plt.savefig(name+'_all_thesholds.png')

        if show:
           plt.show()

        plt.close()

    def calculate_f1(self, predictions, ground_truths, threshold = 0.5):
        if len(predictions.shape) > 1:
            predictions_copy = np.array(predictions)
        else:
            predictions_copy = np.array([predictions])

        for image in predictions_copy:
            image[image >= threshold] = 1
            image[image < threshold] = 0

        arr_predictions = predictions_copy.flatten()
        arr_gts = ground_truths.flatten()

        sklearn_f1 = sklearn.metrics.f1_score(arr_gts, arr_predictions)

        return sklearn_f1

    def calculate_recall_precision_accuracy(self, predictions, ground_truths, threshold = 0.5, need_f1=False, save_text_file=""):
        if len(predictions.shape) > 1:
            predictions_copy = np.array(predictions)
        else:
            predictions_copy = np.array([predictions])

        for image in predictions_copy:
            image[image >= threshold] = 1
            image[image < threshold] = 0

        arr_predictions = predictions_copy.flatten()
        arr_gts = ground_truths.flatten()

        sklearn_accuracy = sklearn.metrics.accuracy_score(arr_gts, arr_predictions)
        sklearn_precision = sklearn.metrics.precision_score(arr_gts, arr_predictions)
        sklearn_recall = sklearn.metrics.recall_score(arr_gts, arr_predictions)
        sklearn_f1 = 0.0
        if need_f1:
            sklearn_f1 = sklearn.metrics.f1_score(arr_gts, arr_predictions)

        if save_text_file is not "":
            labels = ["no change", "change"]  # 0 no change, 1 change
            text_report = str(sklearn.metrics.classification_report(arr_gts, arr_predictions, target_names=labels))
            text_report += "\n"
            text_report += str(sklearn.metrics.confusion_matrix(arr_gts, arr_predictions))
            file = open(save_text_file, "w")
            file.write(text_report)
            file.close()

        return sklearn_recall, sklearn_precision, sklearn_accuracy, sklearn_f1

    def calculate_recall_precision_accuracy_NOCHANGECLASS(self, predictions, ground_truths, threshold = 0.5):
        if len(predictions.shape) > 1:
            predictions_copy = np.array(predictions)
        else:
            predictions_copy = np.array([predictions])

        for image in predictions_copy:
            image[image >= threshold] = 1
            image[image < threshold] = 0

        arr_predictions = predictions_copy.flatten()
        arr_gts = ground_truths.flatten()

        sklearn_accuracy = sklearn.metrics.accuracy_score(arr_gts, arr_predictions)
        sklearn_precision = sklearn.metrics.precision_score(arr_gts, arr_predictions, pos_label=0) # NO CHANGE CLASS
        sklearn_recall = sklearn.metrics.recall_score(arr_gts, arr_predictions, pos_label=0) # NO CHANGE CLASS
        sklearn_f1 = sklearn.metrics.f1_score(arr_gts, arr_predictions)

        return sklearn_recall, sklearn_precision, sklearn_accuracy, sklearn_f1

    def calculate_metrics(self, predictions, ground_truths, threshold = 0.5, verbose=2, save_text_file=""):

        flavour_text = ""
        if len(predictions.shape) > 1:
            if verbose >= 2:
                print("We have", len(predictions), "predictions, each is a", predictions[0].shape, "image.", predictions[0][0][0:3])
                print("We have", len(ground_truths), "ground truths, each is a", ground_truths[0].shape, "image.", ground_truths[0][0][0:3])
            flavour_text = "pixels"
            # careful not to edit the label images here
            predictions_copy = np.array(predictions)
        else:
            flavour_text = "labels"
            predictions_copy = np.array([predictions])

        # 1 threshold the data per each pixel

        # Sith thinks in absolutes
        for image in predictions_copy:
            image[image >= threshold] = 1
            image[image < threshold] = 0

        # only "0.0" and "1.0" in the data now

        #if True:
        #    print("pred:",predictions_copy[0].astype(int))
        #    print("gt:  ",ground_truths)

        # 2 calculate T/F P/N

        arr_predictions = predictions_copy.flatten()
        arr_gts = ground_truths.flatten()

        #print("We have", len(arr_predictions), "~", len(arr_gts), "pixels.")
        assert len(arr_predictions) == len(arr_gts)

        FN = 0
        FP = 0
        TP = 0
        TN = 0

        # from the standpoint of the "changed" (1.0) class:
        for pixel_i in range(len(arr_predictions)):
            pred = arr_predictions[pixel_i]
            gt = arr_gts[pixel_i]

            if pred == 0.0 and gt == 0.0:
                TN += 1
            elif pred == 1.0 and gt == 1.0:
                TP += 1
            elif pred == 1.0 and gt == 0.0:
                FP += 1
            elif pred == 0.0 and gt == 1.0:
                FN += 1

        total = FP + FN + TP + TN

        # 3a generate confusion matrix
        # 3b metrics - recall, precision, accuracy

        if verbose >= 2:
            print("Statistics over", total,flavour_text,":")
            print("TP", TP, "\t ... correctly classified as a change.")
            print("TN", TN, "\t ... correctly classified as a no-change.")
            print("FP", FP, "\t ... classified as change while it's not.")
            print("FN", FN, "\t ... classified as no-change while it is one.")

        accuracy = float(TP + TN) / float(total)
        precision = float(TP) / float(TP + FP)
        recall = float(TP) / float(TP + FN)

        print("accuracy", accuracy, "\t")
        print("precision", precision, "\t")
        print("recall", recall, "\t")

        # 3b metrics - IoU
        IoU = float(TP) / float(TP + FP + FN)
        print("IoU", IoU)

        #sklearn_precision = sklearn.metrics.precision_score(arr_gts, arr_predictions)
        #sklearn_recall = sklearn.metrics.recall_score(arr_gts, arr_predictions)
        #print("sklearn_precision", sklearn_precision, "\t")
        #print("sklearn_recall", sklearn_recall, "\t")

        sklearn_f1 = sklearn.metrics.f1_score(arr_gts, arr_predictions)
        print("sklearn_f1", sklearn_f1, "\t")

        labels = ["no change", "change"] # 0 no change, 1 change

        if verbose >= 2:
            print(sklearn.metrics.classification_report(arr_gts, arr_predictions, target_names=labels))
            conf = sklearn.metrics.confusion_matrix(arr_gts, arr_predictions)
            print(conf)

            if save_text_file is not "":
                text_report = str(sklearn.metrics.classification_report(arr_gts, arr_predictions, target_names=labels))
                text_report += "\n"
                text_report += str(conf)
                file = open(save_text_file, "w")
                file.write(text_report)
                file.close()

            print("=====================================================================================")

        predictions_thresholded = predictions_copy
        return predictions_thresholded, recall, precision, accuracy, sklearn_f1


    # chopped out some unnecessary things:
    def calculate_metrics_fast(self, predictions, ground_truths, threshold = 0.5, verbose=2):

        flavour_text = ""
        if len(predictions.shape) > 1:
            if verbose >= 2:
                print("We have", len(predictions), "predictions, each is a", predictions[0].shape, "image.", predictions[0][0][0:3])
                print("We have", len(ground_truths), "ground truths, each is a", ground_truths[0].shape, "image.", ground_truths[0][0][0:3])
            flavour_text = "pixels"
            # careful not to edit the label images here
            predictions_copy = np.array(predictions)
        else:
            flavour_text = "labels"
            predictions_copy = np.array([predictions])

        # 1 threshold the data per each pixel

        # Sith thinks in absolutes
        for image in predictions_copy:
            image[image >= threshold] = 1
            image[image < threshold] = 0

        # only "0.0" and "1.0" in the data now

        #if True:
        #    print("pred:",predictions_copy[0].astype(int))
        #    print("gt:  ",ground_truths)

        # 2 calculate T/F P/N

        arr_predictions = predictions_copy.flatten()
        arr_gts = ground_truths.flatten()

        #print("We have", len(arr_predictions), "~", len(arr_gts), "pixels.")
        assert len(arr_predictions) == len(arr_gts)

        FN = 0
        FP = 0
        TP = 0
        TN = 0

        # from the standpoint of the "changed" (1.0) class:
        for pixel_i in range(len(arr_predictions)):
            pred = arr_predictions[pixel_i]
            gt = arr_gts[pixel_i]

            if pred == 0.0 and gt == 0.0:
                TN += 1
            elif pred == 1.0 and gt == 1.0:
                TP += 1
            elif pred == 1.0 and gt == 0.0:
                FP += 1
            elif pred == 0.0 and gt == 1.0:
                FN += 1

        total = FP + FN + TP + TN

        # 3a generate confusion matrix
        # 3b metrics - recall, precision, accuracy

        if verbose >= 2:
            print("Statistics over", total,flavour_text,":")
            print("TP", TP, "\t ... correctly classified as a change.")
            print("TN", TN, "\t ... correctly classified as a no-change.")
            print("FP", FP, "\t ... classified as change while it's not.")
            print("FN", FN, "\t ... classified as no-change while it is one.")

        accuracy = float(TP + TN) / float(total)
        precision = float(TP) / float(TP + FP)
        recall = float(TP) / float(TP + FN)

        print("accuracy", accuracy, "\t")
        print("precision", precision, "\t")
        print("recall", recall, "\t")

        predictions_thresholded = predictions_copy
        return predictions_thresholded, recall, precision, accuracy

    # select thr which maximizes the f1 score
    def metrics_autothr_f1_max(self, predictions, ground_truths, jump_by = 0.1, save_text_file=""):
        # force it selecting something 'sensible' for the threshold ...
        range_values = np.arange(0.0+jump_by, 1.0, jump_by)

        xs = []
        ys_recalls = []
        ys_precisions = []
        ys_accuracies = []
        ys_f1s = []
        for thr in range_values:
            xs.append(thr)
            print("auto threshold=", thr)

            f1 = self.calculate_f1(predictions, ground_truths, threshold=thr)
            ys_f1s.append(f1)

        max_f1_idx = np.argmax(ys_f1s)
        best_thr = xs[max_f1_idx]

        selected_recall, selected_precision, selected_accuracy, _ = self.calculate_recall_precision_accuracy(predictions, ground_truths,threshold=thr, need_f1=False, save_text_file=save_text_file)
        selected_f1 = ys_f1s[max_f1_idx]

        print("Selecting threshold as", best_thr, "as it maximizes the f1 score getting", selected_f1,
              "(other scores are: recall", selected_recall, ", precision", selected_precision, ", acc", selected_accuracy, ")")

        return best_thr, selected_recall, selected_precision, selected_accuracy, selected_f1