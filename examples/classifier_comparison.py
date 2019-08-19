import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from pycompss.api.api import compss_wait_on
from sklearn.datasets import make_moons, make_circles, make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

import dislib as ds
from dislib.classification import CascadeSVM, RandomForestClassifier


def main():
    h = .02  # step size in the mesh

    names = ["Linear C-SVM", "RBF C-SVM", "Random forest"]

    classifiers = [
        CascadeSVM(kernel="linear", c=0.025, max_iter=5),
        CascadeSVM(gamma=2, c=1, max_iter=5),
        RandomForestClassifier(random_state=1)
    ]

    x, y = make_classification(n_features=2, n_redundant=0, n_informative=2,
                               random_state=1, n_clusters_per_class=1)
    rng = np.random.RandomState(2)
    x += 2 * rng.uniform(size=x.shape)
    linearly_separable = (x, y)

    datasets = [make_moons(noise=0.3, random_state=0),
                make_circles(noise=0.2, factor=0.5, random_state=1),
                linearly_separable
                ]

    plt.figure(figsize=(27, 9))
    i = 1
    # iterate over datasets
    for ds_cnt, dataset in enumerate(datasets):
        # preprocess dataset, split into training and test part
        x, y = dataset
        x = StandardScaler().fit_transform(x)
        x_train, x_test, y_train, y_test = \
            train_test_split(x, y, test_size=.4, random_state=42)
        ds_x_train = ds.array(x_train, blocks_shape=(20, 2))
        ds_y_train = ds.array(y_train.reshape(-1, 1), blocks_shape=(20, 2))
        ds_x_test = ds.array(x_test, blocks_shape=(20, 2))
        ds_y_test = ds.array(y_test.reshape(-1, 1), blocks_shape=(20, 2))

        x_min, x_max = x[:, 0].min() - .5, x[:, 0].max() + .5
        y_min, y_max = x[:, 1].min() - .5, x[:, 1].max() + .5
        xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                             np.arange(y_min, y_max, h))

        # just plot the dataset first
        cm = plt.cm.RdBu
        cm_bright = ListedColormap(['#FF0000', '#0000FF'])
        ax = plt.subplot(len(datasets), len(classifiers) + 1, i)
        if ds_cnt == 0:
            ax.set_title("Input data")
        # Plot the training points
        ax.scatter(x_train[:, 0], x_train[:, 1], c=y_train, cmap=cm_bright,
                   edgecolors='k')
        # Plot the testing points
        ax.scatter(x_test[:, 0], x_test[:, 1], c=y_test, cmap=cm_bright,
                   alpha=0.6,
                   edgecolors='k')
        ax.set_xlim(xx.min(), xx.max())
        ax.set_ylim(yy.min(), yy.max())
        ax.set_xticks(())
        ax.set_yticks(())
        i += 1

        # iterate over classifiers
        for name, clf in zip(names, classifiers):
            ax = plt.subplot(len(datasets), len(classifiers) + 1, i)

            clf.fit(ds_x_train, ds_y_train)
            score = compss_wait_on(clf.score(ds_x_test, ds_y_test))

            # Plot the decision boundary. For that, we will assign a color to
            # each point in the mesh [x_min, x_max]x[y_min, y_max].
            mesh = np.c_[xx.ravel(), yy.ravel()]
            mesh_data = ds.array(mesh, (mesh.shape[0], 2))

            if hasattr(clf, "decision_function"):
                Z = clf.decision_function(mesh_data).collect()
            else:
                Z = clf.predict_proba(mesh_data).collect()[:, 1]

            # Put the result into a color plot
            Z = Z.reshape(xx.shape)
            ax.contourf(xx, yy, Z, cmap=cm, alpha=.8)

            # Plot the training points
            ax.scatter(x_train[:, 0], x_train[:, 1], c=y_train, cmap=cm_bright,
                       edgecolors='k')
            # Plot the testing points
            ax.scatter(x_test[:, 0], x_test[:, 1], c=y_test, cmap=cm_bright,
                       edgecolors='k', alpha=0.6)

            ax.set_xlim(xx.min(), xx.max())
            ax.set_ylim(yy.min(), yy.max())
            ax.set_xticks(())
            ax.set_yticks(())
            if ds_cnt == 0:
                ax.set_title(name)
            ax.text(xx.max() - .3, yy.min() + .3, ('%.2f' % score).lstrip('0'),
                    size=15, horizontalalignment='right')
            i += 1

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
